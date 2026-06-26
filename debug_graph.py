import asyncio
from graph import RAGGraph

async def main():
    rag = RAGGraph()
    inputs = {
        "user_query": "what if my attendance is less than 75%",
        "chat_history": [],
    }
    try:
        async for event in rag.app.astream_events(inputs, version="v2"):
            kind = event["event"]
            if kind == "on_chat_model_stream":
                pass
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
