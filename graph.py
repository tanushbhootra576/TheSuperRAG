import os
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.documents import Document

from ingest import DocumentStore
from reranker import CrossEncoderReranker
import asyncio

RETRIEVAL_K = 5
RERANK_TOP_K = 2

class DirectWorkflow:
    def __init__(self, rag_graph):
        self.rag_graph = rag_graph
        
    async def astream_events(self, inputs, version="v2"):
        state = inputs.copy()
        
        sub_queries = await self.rag_graph.decompose_query_step(state["user_query"])
        yield {"event": "decomposed", "sub_queries": [{"index": i+1, "query": sq, "tool": "pending"} for i, sq in enumerate(sub_queries)]}
        
        # 1. Agent Router
        yield {
            "event": "on_chain_start",
            "metadata": {"langgraph_node": "smart_router"}
        }
        
        llm = self.rag_graph._get_llm(temperature=0.0)
        from langchain_core.tools import tool
        from tools import execute_web_search, execute_sql_query
        import json
        
        @tool
        async def web_search(query: str):
            """Search the web for recent or external information."""
            return await execute_web_search(query)
            
        @tool
        async def sql_query(query: str):
            """Query the structured SQL database for analytics, sales, or business data."""
            return await execute_sql_query(query)
            
        @tool
        async def vector_search(query: str):
            """Search the document knowledge base for internal documents, guides, and texts."""
            return "Proceed to vector search"
            
        tools = [web_search, sql_query, vector_search]
        llm_with_tools = llm.bind_tools(tools)
        
        from langchain_core.messages import SystemMessage, HumanMessage
        router_prompt = "You are an intelligent routing agent. Decide which tool to use based on the user's query."
        
        all_retrieved_docs = []
        confidences = []
        
        for sq in sub_queries:
            messages = [SystemMessage(content=router_prompt), HumanMessage(content=sq)]
            
            try:
                router_response = await llm_with_tools.ainvoke(messages)
                tool_calls = router_response.tool_calls
            except Exception as e:
                import logging
                logging.getLogger(__name__).warning(f"Router LLM failed to invoke tools, defaulting to vector search: {e}")
                tool_calls = [{"name": "vector_search", "args": {"query": sq}}]
            
            skip_rag = False
            if tool_calls:
                tool_call = tool_calls[0]
                if tool_call["name"] == "web_search":
                    yield {"event": "tool_start", "tool": "web_search", "query": tool_call["args"].get("query", str(tool_call["args"]))}
                    res = await web_search.ainvoke(tool_call["args"])
                    for idx, r in enumerate(res):
                        all_retrieved_docs.append({
                            "file": "Web: " + r["source"],
                            "page": "1",
                            "snippet": r["content"]
                        })
                    yield {"event": "tool_done", "tool": "web_search", "result_count": len(res)}
                    skip_rag = True
                elif tool_call["name"] == "sql_query":
                    yield {"event": "tool_start", "tool": "sql_query", "query": tool_call["args"].get("query", str(tool_call["args"]))}
                    res = await sql_query.ainvoke(tool_call["args"])
                    for idx, r in enumerate(res):
                        all_retrieved_docs.append({
                            "file": "SQL Database",
                            "page": "1",
                            "snippet": json.dumps(r)
                        })
                    yield {"event": "tool_done", "tool": "sql_query", "result_count": len(res)}
                    skip_rag = True
                    
            if not skip_rag:
                yield {"event": "tool_start", "tool": "vector_search", "query": sq}
                # 1.5. Rewrite Query
                yield {
                    "event": "on_chain_start",
                    "metadata": {"langgraph_node": "rewrite_query"}
                }
                
                transformed_query = await self.rag_graph.transform_query_step({"user_query": sq})
                
                yield {
                    "event": "on_chain_end",
                    "metadata": {"langgraph_node": "rewrite_query"},
                    "data": {"output": {"current_search_query": transformed_query}}
                }
                
                # Retrieve
                retrieved_docs, confidence = await self.rag_graph.retrieve_step({"current_search_query": transformed_query})
                all_retrieved_docs.extend(retrieved_docs)
                confidences.append(confidence["score"])
                yield {"event": "tool_done", "tool": "vector_search", "result_count": len(retrieved_docs)}
        
        avg_conf = sum(confidences) / len(confidences) if confidences else 10.0
        final_confidence = {"score": round(avg_conf, 1), "label": "High" if avg_conf > 8.0 else "Medium", "emoji": ""}
        
        state["retrieved_docs"] = all_retrieved_docs
        state["confidence"] = final_confidence
        
        yield {
            "event": "on_chain_end",
            "metadata": {"langgraph_node": "smart_router"},
            "data": {"output": {"current_search_query": state["user_query"], "generation": "proceed"}}
        }
        
        yield {
            "event": "on_chain_end",
            "metadata": {"langgraph_node": "retrieve"},
            "data": {"output": {"retrieved_docs": all_retrieved_docs, "confidence": final_confidence}}
        }
        
        # 3. Generate (streaming)

        
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
        
        memory = state.get("user_memory", "")
        memory_str = f"\nUser Memory/Preferences:\n{memory}\n" if memory else ""
        
        system_prompt = f"You are the Answer Agent. Answer the user's question. Cite document sources strictly using [1], [2], etc.{memory_str}\nContext from Documents:\n{context}"
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

    async def decompose_query_step(self, query: str):
        llm = self._get_llm(temperature=0.0)
        prompt = (
            "You are an expert query analyzer. Determine if the following user query is complex and needs to be broken down into multiple simpler sub-queries to be answered correctly.\n"
            "If the query asks to combine or compare internal data (like orders, sales, DB) with external data (like news, web search), you MUST break it down into 2-3 simpler sub-queries.\n"
            "If it is simple (only needs one tool or domain), return a JSON array with just the original query.\n"
            "Return ONLY the JSON array, no markdown or text.\n"
            f"Query: {query}"
        )
        try:
            from langchain_core.messages import HumanMessage
            res = await llm.ainvoke([HumanMessage(content=prompt)])
            content = res.content
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            import json
            sub_queries = json.loads(content)
            if not isinstance(sub_queries, list) or len(sub_queries) == 0:
                return [query]
            
            cleaned_sqs = []
            for sq in sub_queries:
                if isinstance(sq, dict):
                    # In case the LLM returned [{"query": "..."}] instead of ["..."]
                    cleaned_sqs.append(sq.get("query", str(sq)))
                else:
                    cleaned_sqs.append(str(sq))
            return cleaned_sqs
        except Exception:
            return [query]

    async def transform_query_step(self, state):
        query = state["user_query"]
        llm = self._get_llm(temperature=0.7)
        
        from langchain_core.messages import SystemMessage, HumanMessage
        prompt = (
            "You are an expert search assistant. Your task is to enhance the user's query for a semantic search engine.\n"
            "Generate a hypothetical ideal answer (HyDE) to the query, and a step-back broader question to capture context.\n"
            "Return your response EXACTLY in this format:\n"
            "STEP-BACK: <broader question>\n"
            "HYDE: <hypothetical answer>"
        )
        messages = [SystemMessage(content=prompt), HumanMessage(content=query)]
        response = await llm.ainvoke(messages)
        
        transformed = f"{query}\n\n{response.content}"
        return transformed

    async def retrieve_step(self, state):
        query = state["current_search_query"]
        
        retriever = self.doc_store.get_retriever(qdrant_filter=None, k=RETRIEVAL_K)
        
        raw_docs = await retriever.ainvoke(query)
                    
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
        
        if conf_val > 0.8: confidence = {"score": round(conf_val*10, 1), "label": "High", "emoji": ""}
        elif conf_val > 0.4: confidence = {"score": round(conf_val*10, 1), "label": "Medium", "emoji": ""}
        else: confidence = {"score": round(conf_val*10, 1), "label": "Low", "emoji": ""}
        
        return retrieved_docs, confidence

    async def generate_step(self, state):
        docs = state.get("retrieved_docs", [])
        context_parts = []
        for i, d in enumerate(docs):
            context_parts.append(f"[{i+1}] Source: {d['file']}, Page: {d['page']}\n{d['snippet']}")
        context = "\n\n".join(context_parts)
        
        memory = state.get("user_memory", "")
        memory_str = f"\nUser Memory/Preferences:\n{memory}\n" if memory else ""
        
        system_prompt = f"You are the Answer Agent. Answer the user's question. Cite document sources strictly using [1], [2], etc.{memory_str}\nContext from Documents:\n{context}"
        from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
        
        messages = [SystemMessage(content=system_prompt)]
        for m in state.get("chat_history", []):
            if m["role"] == "user": messages.append(HumanMessage(content=m["content"]))
            elif m["role"] == "assistant": messages.append(AIMessage(content=m["content"]))
        messages.append(HumanMessage(content=state["user_query"]))
        
        llm = self._get_llm()
        response = await llm.ainvoke(messages)
        return response.content
