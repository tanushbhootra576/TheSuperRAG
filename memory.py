import json
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate

class RewrittenQuery(BaseModel):
    rewritten_query: str = Field(description="The self-contained standalone version of the user query.")
    extracted_entities: dict = Field(description="A dictionary of key entities mentioned. (e.g. {'person': 'John', 'company': 'Acme'}).")

class MemoryManager:
    def __init__(self, llm):
        self.llm = llm

    async def process(self, query: str, history: list, existing_summary: str, existing_entities: dict):
        new_summary = existing_summary or ""
        
        if len(history) > 10:
            to_summarize = history[:-6]
            history = history[-6:]
            history_str = "\n".join([f"{m['role']}: {m['content']}" for m in to_summarize])
            prompt = ChatPromptTemplate.from_messages([
                ("system", "Summarize the following old conversation turns into a dense paragraph. Incorporate the previous summary: {prev}"),
                ("user", "{history}")
            ])
            res = await (prompt | self.llm).ainvoke({"prev": new_summary, "history": history_str})
            new_summary = res.content.strip()

        history_str = "\n".join([f"{m['role']}: {m['content']}" for m in history])
        prompt2 = ChatPromptTemplate.from_messages([
            ("system", "You are a memory agent. Given the conversation summary and recent history, rewrite the user's query to be fully self-contained and standalone (e.g. resolving pronouns). Also extract key entities.\n\nSummary: {summary}"),
            ("user", "History:\n{history}\n\nUser Query: {query}")
        ])
        
        try:
            res2 = await (prompt2 | self.llm.with_structured_output(RewrittenQuery)).ainvoke({
                "summary": new_summary,
                "history": history_str,
                "query": query
            })
            rewritten = res2.rewritten_query if res2 else query
            entities = res2.extracted_entities if res2 else {}
        except Exception:
            rewritten = query
            entities = {}
            
        merged_entities = {**(existing_entities or {})}
        for k, v in entities.items():
            merged_entities[k] = v
            
        return {
            "conversation_summary": new_summary,
            "entity_store": merged_entities,
            "rewritten_query": rewritten,
            "truncated_history": history
        }
