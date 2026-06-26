import asyncio
import json
import httpx

async def main():
    async with httpx.AsyncClient() as client:
        req = {
            "query": "what is 2 + 2?",
            "history": [],
            "selected_documents": [],
            "llm_model": "llama-3.1-8b-instant",
            "temperature": 0.0,
            "use_cross_encoder": False,
            "use_hyde": False,
            "use_multi_query": False,
            "evaluate": False
        }
        async with client.stream("POST", "http://localhost:8000/chat", json=req) as r:
            async for chunk in r.aiter_text():
                print(chunk, end="")

if __name__ == "__main__":
    asyncio.run(main())
