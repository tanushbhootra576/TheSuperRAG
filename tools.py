import os
import asyncio
from pydantic import BaseModel, Field

class WebSearchInput(BaseModel):
    query: str = Field(description="The search query to look up on the web.")

class SQLQueryInput(BaseModel):
    query: str = Field(description="The natural language question to translate into SQL and execute against the database.")

async def execute_web_search(query: str) -> list[dict]:
    try:
        from tavily import TavilyClient
        client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
        results = await asyncio.to_thread(
            client.search, query, max_results=5
        )
        return [
            {"content": r["content"], "source": r["url"]}
            for r in results.get("results", [])
        ]
    except Exception as e:
        return [{"content": f"Web search failed: {e}", "source": "Error"}]

SCHEMA_CONTEXT = """
Tables:
- users(id, name, email, region, created_at)
- products(id, name, category, price)
- orders(id, user_id, product_id, quantity, status, order_date)
"""

async def execute_sql_query(query: str) -> list[dict]:
    try:
        from langchain_groq import ChatGroq
        from langchain_core.messages import SystemMessage, HumanMessage
        import json
        import sqlite3
        
        llm = ChatGroq(model_name="llama-3.1-8b-instant", temperature=0.0)
        
        sys_msg = (
            "You are a SQL expert. Translate the user's natural language question into a SQL query.\n"
            f"Use the EXACT following schema:\n{SCHEMA_CONTEXT}\n"
            "CRITICAL: Do NOT invent column names. ONLY use the columns explicitly listed above.\n"
            "Return ONLY the SQL query, nothing else, no markdown formatting."
        )
        
        response = await llm.ainvoke([SystemMessage(content=sys_msg), HumanMessage(content=query)])
        sql = response.content.replace('```sql', '').replace('```', '').strip()
        
        import os
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sales.db")
        conn = sqlite3.connect(db_path)
        cursor = conn.execute(sql)
        columns = [d[0] for d in cursor.description]
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(zip(columns, row)) for row in rows]
    except Exception as e:
        return [{"error": str(e)}]

