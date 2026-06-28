import asyncio
import os
from graph import RAGGraph
from ingest import DocumentStore

async def test_router():
    doc_store = DocumentStore()
    rag = RAGGraph(doc_store)
    
    queries = [
        "What is quantum entanglement?",
        "What's the latest news on OpenAI?",
        "How many orders were delivered last week?"
    ]
    
    for q in queries:
        print(f"\n--- Testing Query: '{q}' ---")
        state = {
            "user_query": q,
            "chat_history": [],
            "temperature": 0.0
        }
        
        async for event in rag.app.astream_events(state, version="v2"):
            node = event.get("metadata", {}).get("langgraph_node")
            kind = event.get("event")
            if kind == "on_chain_end" and node == "smart_router":
                print("Router Output:")
                print(event.get("data", {}).get("output", {}))
            elif kind == "on_chain_end" and node in ["retrieve", "generate"]:
                print(f"Finished {node} step.")

if __name__ == "__main__":
    asyncio.run(test_router())
