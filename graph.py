import os
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.documents import Document

from ingest import DocumentStore
from reranker import CrossEncoderReranker
from query_processor import QueryProcessor
from filters import FilterBuilder
import asyncio

RETRIEVAL_K = 10
RERANK_TOP_K = 5

class DirectWorkflow:
    def __init__(self, rag_graph):
        self.rag_graph = rag_graph
        
    async def astream_events(self, inputs, version="v2"):
        state = inputs.copy()
        
        # 1. Router
        yield {
            "event": "on_chain_start",
            "metadata": {"langgraph_node": "smart_router"}
        }
        yield {
            "event": "on_chain_end",
            "metadata": {"langgraph_node": "smart_router"},
            "data": {"output": {"current_search_query": state["user_query"], "generation": "proceed"}}
        }
        
        # 2. Retrieve
        retrieved_docs, confidence = await self.rag_graph.retrieve_step(state)
        state["retrieved_docs"] = retrieved_docs
        state["confidence"] = confidence
        yield {
            "event": "on_chain_end",
            "metadata": {"langgraph_node": "retrieve"},
            "data": {"output": {"retrieved_docs": retrieved_docs, "confidence": confidence}}
        }
        
        # 3. Generate (streaming)
        yield {
            "event": "on_chain_start",
            "metadata": {"langgraph_node": "generate"}
        }
        
        docs = state.get("retrieved_docs", [])
        context_parts = []
        for i, d in enumerate(docs):
            context_parts.append(f"[{i+1}] Source: {d['file']}, Page: {d['page']}\n{d['snippet']}")
        context = "\n\n".join(context_parts)
        
        system_prompt = f"You are the Answer Agent. Answer the user's question. Cite document sources strictly using [1], [2], etc.\nContext from Documents:\n{context}"
        from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
        
        messages = [SystemMessage(content=system_prompt)]
        for m in state.get("chat_history", []):
            if m["role"] == "user": messages.append(HumanMessage(content=m["content"]))
            elif m["role"] == "assistant": messages.append(AIMessage(content=m["content"]))
        messages.append(HumanMessage(content=state["user_query"]))
        
        llm = self.rag_graph._get_llm(temperature=state.get("temperature", 0.0))
        full_generation = ""
        
        async for chunk in llm.astream(messages):
            full_generation += chunk.content
            yield {
                "event": "on_chat_model_stream",
                "metadata": {"langgraph_node": "generate"},
                "data": {"chunk": chunk}
            }
            
        yield {
            "event": "on_chain_end",
            "metadata": {"langgraph_node": "generate"},
            "data": {"output": {"generation": full_generation}}
        }


class RAGGraph:
    def __init__(self, doc_store: DocumentStore):
        self.doc_store = doc_store
        self.groq_key = os.getenv("GROQ_API_KEY")
        if not self.groq_key:
            raise ValueError("GROQ_API_KEY not found in environment.")

        self.reranker = CrossEncoderReranker()
        self.llm = ChatGroq(model_name="llama-3.1-8b-instant", groq_api_key=self.groq_key)
        self.app = DirectWorkflow(self)
        print(f"\n[OK] Direct RAGGraph ready.\n")

    def _get_llm(self, temperature: float = 0.0):
        return ChatGroq(
            temperature=temperature,
            model_name="llama-3.1-8b-instant",
            groq_api_key=self.groq_key,
        )

    async def retrieve_step(self, state):
        query = state["current_search_query"]
        processor = QueryProcessor(self._get_llm(temperature=0.2))
        queries, latency = await processor.process(query, False, False)
        
        qdrant_filter = FilterBuilder.build({})
        retriever = self.doc_store.get_retriever(qdrant_filter=qdrant_filter, k=RETRIEVAL_K)
        
        tasks = [retriever.ainvoke(q) for q in queries]
        results = await asyncio.gather(*tasks)
        
        raw_docs = []
        seen = set()
        for res in results:
            for d in res:
                content = d.page_content
                if content not in seen:
                    seen.add(content)
                    raw_docs.append(d)
                    
        final_docs, scores = self.reranker.rerank(query, raw_docs, top_k=RERANK_TOP_K)
            
        retrieved_docs = []
        for i, d in enumerate(final_docs):
            score = scores[i] if i < len(scores) else 0.0
            retrieved_docs.append({
                "chunk_id": d.metadata.get("chunk_id", ""),
                "file": d.metadata.get("source_file", "Unknown"),
                "page": d.metadata.get("page_number", "N/A"),
                "snippet": d.page_content,
                "score": score
            })
            
        avg_score = sum(d["score"] for d in retrieved_docs) / max(len(retrieved_docs), 1) if retrieved_docs else 0.0
        # Simulated confidence score
        conf_val = min(max(avg_score, 0.0), 1.0)
        
        if conf_val > 0.8: confidence = {"score": round(conf_val*10, 1), "label": "High", "emoji": "🟢"}
        elif conf_val > 0.4: confidence = {"score": round(conf_val*10, 1), "label": "Medium", "emoji": "🟡"}
        else: confidence = {"score": round(conf_val*10, 1), "label": "Low", "emoji": "🔴"}
        
        return retrieved_docs, confidence

    async def generate_step(self, state):
        docs = state.get("retrieved_docs", [])
        context_parts = []
        for i, d in enumerate(docs):
            context_parts.append(f"[{i+1}] Source: {d['file']}, Page: {d['page']}\n{d['snippet']}")
        context = "\n\n".join(context_parts)
        
        system_prompt = f"You are the Answer Agent. Answer the user's question. Cite document sources strictly using [1], [2], etc.\nContext from Documents:\n{context}"
        from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
        
        messages = [SystemMessage(content=system_prompt)]
        for m in state.get("chat_history", []):
            if m["role"] == "user": messages.append(HumanMessage(content=m["content"]))
            elif m["role"] == "assistant": messages.append(AIMessage(content=m["content"]))
        messages.append(HumanMessage(content=state["user_query"]))
        
        llm = self._get_llm()
        response = await llm.ainvoke(messages)
        return response.content
