"""
graph.py -- LangGraph RAG Workflow for TheSuperRAG.

Improvements over v1:
  1. Conversation history injected into generate_node prompt (not just router)
  2. Hybrid retrieval via DocumentStore (dense + BM25)
  3. Cross-encoder re-ranking after each retrieval step
  4. retrieved_docs with {file, page, snippet} returned for frontend citations
  5. Confidence score computed from re-ranker and surfaced to the frontend
  6. Document filtering via selected_documents in AgentState
  7. Configurable retrieval depth (RETRIEVAL_K) separate from re-rank depth
"""
import os
from typing import TypedDict, List, Optional
from dotenv import load_dotenv

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.documents import Document
from langgraph.graph import StateGraph, END

from ingest import DocumentStore
from reranker import CrossEncoderReranker

load_dotenv()

# ── Constants ─────────────────────────────────────────────────────────────────
RETRIEVAL_K = 10     # Candidates fetched from hybrid search
RERANK_TOP_K = 4     # Documents kept after cross-encoder re-ranking
MAX_HEAL_LOOPS = 3   # Maximum self-healing query rewrites before giving up


# ── State Definition ──────────────────────────────────────────────────────────
class AgentState(TypedDict):
    chat_history: List[dict]
    user_query: str
    current_search_query: str
    retrieved_context: str
    retrieved_docs: List[dict]        # [{file, page, snippet}] for citations
    generation: str
    confidence: dict                  # {score, label, emoji}
    loop_count: int
    logs: List[str]
    selected_documents: List[str]     # [] = search all, non-empty = filter
    llm_model: str                    # e.g., 'llama-3.1-8b-instant', 'mixtral-8x7b-32768', 'gemma2-9b-it'
    temperature: float                # 0.0 to 1.0
    use_cross_encoder: bool           # Whether to use the cross-encoder re-ranking


# ── RAG Graph ─────────────────────────────────────────────────────────────────
class RAGGraph:
    """
    LangGraph-powered self-healing RAG pipeline.

    Nodes:
        smart_router   -> disambiguate & contextualise the query using history
        retrieve       -> hybrid vector search + cross-encoder re-ranking
        generate       -> LLM generation with history context + citations
        rewrite_query  -> Self-heal: rewrite query on "Information missing"

    Edges:
        smart_router -> retrieve  (if query is clear)
        smart_router -> END       (if clarification needed)
        retrieve     -> generate
        generate     -> rewrite_query  (if missing & under loop limit)
        generate     -> END       (if answered or loop limit reached)
        rewrite_query -> retrieve
    """

    def __init__(self, doc_store: DocumentStore):
        self.doc_store = doc_store

        if doc_store.is_empty():
            raise ValueError(
                "Document store is empty. Please add PDFs to the DATA/ folder, "
                "then call /init again."
            )

        groq_key = os.getenv("GROQ_API_KEY")
        if not groq_key:
            raise ValueError("GROQ_API_KEY not found in environment.")

        self.groq_key = groq_key

        self.reranker = CrossEncoderReranker()
        self.app = self._build_graph()
        print(
            f"\n[OK] RAGGraph ready "
            f"(hybrid={'yes' if doc_store.hybrid_enabled else 'no'}, "
            f"reranker=yes, k={RETRIEVAL_K}->{RERANK_TOP_K}).\n"
        )

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _format_history(self, history: List[dict], n: int = 6) -> str:
        """Format the last n chat turns for injection into prompts."""
        if not history:
            return "No previous conversation."
        entries = history[-n:]
        return "\n".join(
            f"{m['role'].capitalize()}: {m['content']}" for m in entries
        )

    def _docs_to_citations(self, docs: List[Document]) -> List[dict]:
        """Convert LangChain Document list to citation dicts for the frontend."""
        return [
            {
                "file": d.metadata.get("source_file", "Unknown"),
                "page": d.metadata.get("page_number", "N/A"),
                "snippet": (
                    d.page_content[:220] + "..."
                    if len(d.page_content) > 220
                    else d.page_content
                ),
            }
            for d in docs
        ]

    # ── Graph Nodes ───────────────────────────────────────────────────────────

    async def smart_router_node(self, state: AgentState) -> dict:
        """
        Analyses conversation history + latest query.
        - If follow-up / ambiguous: rewrites into a standalone search query.
        - If vague and off-topic: asks a clarifying question instead.
        Outputs PROCEED: <query> or a clarifying question.
        """
        history_text = self._format_history(state.get("chat_history", []))

        prompt = ChatPromptTemplate.from_messages([
            ("system",
             """You are the intelligence layer for a policy/regulatory document database.

Rules:
1. If the query is a follow-up or references prior context, rewrite it as a
   complete, self-contained search query.
2. If the query is clear and specific, output STRICTLY:
   PROCEED: [full standalone search query]
3. If the query is vague, greeting, or off-topic, output a clarifying question.
Do NOT include preamble, thoughts, or formatting. Just output the PROCEED command or the question.
"""),
            ("user", "History: {history}\n\nLatest Query: {query}")
        ])

        llm = ChatGroq(
            temperature=state.get("temperature", 0.0),
            model_name=state.get("llm_model", "llama-3.1-8b-instant"),
            groq_api_key=self.groq_key,
        )
        chain = prompt | llm

        chain = prompt | llm

        res = await chain.ainvoke({
            "history": history_text,
            "query": state["user_query"],
        })
        output = res.content.strip()
        logs = state.get("logs", []) + ["[smart_router] Query analysed."]

        if output.upper().startswith("PROCEED:"):
            standalone = output[8:].strip()
            return {
                "current_search_query": standalone,
                "generation": "proceed",
                "logs": logs,
            }
        return {"generation": output, "logs": logs}

    async def retrieve_node(self, state: AgentState) -> dict:
        """
        Runs hybrid search (dense + BM25) then cross-encoder re-ranking.
        Populates retrieved_context (for LLM), retrieved_docs (for citations),
        and confidence (for the frontend badge).
        """
        query = state["current_search_query"]
        selected = state.get("selected_documents") or []

        retriever = self.doc_store.get_retriever(
            selected_docs=selected if selected else None,
            k=RETRIEVAL_K,
        )
        # Assuming retriever supports ainvoke (if not, we can run_in_executor, or use aget_relevant_documents)
        raw_docs = await retriever.ainvoke(query)

        # Cross-encoder re-ranking (toggleable)
        use_reranker = state.get("use_cross_encoder", True)
        
        if use_reranker:
            final_docs, scores = self.reranker.rerank(
                query, raw_docs, top_k=RERANK_TOP_K
            )
            confidence = self.reranker.score_to_confidence(scores)
        else:
            final_docs = raw_docs[:RERANK_TOP_K]
            confidence = {"score": 0, "label": "Disabled", "emoji": ""}

        # Build context string for LLM (includes file + page attribution)
        context_parts = []
        for d in final_docs:
            file_ref = d.metadata.get("source_file", "Unknown")
            page_ref = d.metadata.get("page_number", "N/A")
            context_parts.append(
                f"[Source: {file_ref} | Page: {page_ref}]\n{d.page_content}"
            )
        context = "\n\n---\n\n".join(context_parts)

        return {
            "retrieved_context": context,
            "retrieved_docs": self._docs_to_citations(final_docs),
            "confidence": confidence,
            "loop_count": state.get("loop_count", 0) + 1,
        }

    async def generate_node(self, state: AgentState) -> dict:
        """
        Generates an answer using the re-ranked context and conversation history.
        Instructs the LLM to include a Sources section in its answer.
        """
        history_text = self._format_history(state.get("chat_history", []))

        prompt = ChatPromptTemplate.from_messages([
            ("system",
             """You are an expert document analyst for policy, regulatory, and legal documents.

Your task is to answer the user's question using ONLY the provided document context.

Rules:
1. Pay close attention to cross-references, exclusions, conditions, and tabular data.
2. Cite sources using [Document_Name] or [Page X] when facts are used.
3. Your tone must be highly professional, structured, and enterprise-ready.
4. Use bullet points or numbered lists when appropriate for readability.
5. If the context does not contain the answer, explicitly state: "Information missing." Do not guess.
6. TRANSLATE ALL CONTEXT to ENGLISH if it is in another language before incorporating it into your answer.

Context provided:
{context}"""),
            ("user", "Conversation History:\n{history}\n\nCurrent Question: {query}")
        ])

        llm = ChatGroq(
            temperature=state.get("temperature", 0.0),
            model_name=state.get("llm_model", "llama-3.1-8b-instant"),
            groq_api_key=self.groq_key,
        )
        chain = prompt | llm

        resp = await chain.ainvoke({
            "context": state["retrieved_context"],
            "query": state["user_query"],
            "history": history_text,
        })
        return {"generation": resp.content}

    async def rewrite_node(self, state: AgentState) -> dict:
        """
        Self-heal: generates a new, semantically different search query when
        the previous one failed to retrieve relevant context.
        """
        prompt = ChatPromptTemplate.from_messages([
            ("system",
             """You are the Document Intelligence layer.
The query below failed to retrieve relevant documents from the database. 
Generate an entirely different, highly specific keyword search query that 
may uncover hidden clauses, cross-references, or alternative phrasings."""),
            ("user", "Query that failed: {query}\n\nPlease generate exactly 3 alternative search queries separated by a comma. Do not include quotes.")
        ])

        llm = ChatGroq(
            temperature=state.get("temperature", 0.0) + 0.3, # Slightly more creative for rewrites
            model_name=state.get("llm_model", "llama-3.1-8b-instant"),
            groq_api_key=self.groq_key,
        )
        chain = prompt | llm
        resp = await chain.ainvoke({"query": state["current_search_query"]})
        new_query = resp.content.strip()
        logs = state.get("logs", []) + [
            f"[self_heal] Rewrote query to: '{new_query}'"
        ]
        return {"current_search_query": new_query, "logs": logs}

    # ── Conditional Edges ─────────────────────────────────────────────────────

    def evaluate_router_edge(self, state: AgentState) -> str:
        """Route to retrieval or ask the user for clarification."""
        return "search" if state.get("generation", "").lower() == "proceed" else "ask_user"

    def evaluate_generation_edge(self, state: AgentState) -> str:
        """Decide whether to self-heal or stop."""
        generation = state.get("generation", "").lower()
        context = state.get("retrieved_context", "").strip()

        if "information missing" in generation or not context:
            if state.get("loop_count", 0) >= MAX_HEAL_LOOPS:
                return "stop"
            return "heal"
        return "stop"

    # ── Graph Builder ─────────────────────────────────────────────────────────

    def _build_graph(self):
        wf = StateGraph(AgentState)

        wf.add_node("smart_router", self.smart_router_node)
        wf.add_node("retrieve", self.retrieve_node)
        wf.add_node("generate", self.generate_node)
        wf.add_node("rewrite_query", self.rewrite_node)

        wf.set_entry_point("smart_router")

        wf.add_conditional_edges(
            "smart_router",
            self.evaluate_router_edge,
            {"search": "retrieve", "ask_user": END},
        )
        wf.add_edge("retrieve", "generate")
        wf.add_conditional_edges(
            "generate",
            self.evaluate_generation_edge,
            {"heal": "rewrite_query", "stop": END},
        )
        wf.add_edge("rewrite_query", "retrieve")

        return wf.compile()