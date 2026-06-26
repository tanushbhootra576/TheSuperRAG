import json
from langchain_core.prompts import ChatPromptTemplate
from typing import List

_suggestion_cache = {}

class SuggestionGenerator:
    def __init__(self, llm):
        self.llm = llm

    async def generate(self, query: str, answer: str, source_docs: List[str], entities: dict) -> List[str]:
        cache_key = (query, frozenset(source_docs))
        
        if cache_key in _suggestion_cache:
            return _suggestion_cache[cache_key]
                
        # LLM Generation
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a helpful assistant. Given a Q&A exchange and the source documents used, generate exactly 3 follow-up questions the user might naturally want to ask next. Make them specific, answerable from the same documents, and progressively deeper. Return ONLY a JSON array of 3 strings. Do not use markdown blocks."),
            ("user", "Query: {query}\\nAnswer: {answer}\\nSource Docs: {docs}\\nEntities: {entities}")
        ])
        
        entities_str = ", ".join(f"{k}: {v}" for k, v in entities.items()) if entities else "None"
        docs_str = ", ".join(set(source_docs)) if source_docs else "None"
        
        try:
            res = await (prompt | self.llm).ainvoke({
                "query": query,
                "answer": answer[:500], # truncating for context size
                "docs": docs_str,
                "entities": entities_str
            })
            content = res.content.strip()
            # Clean potential markdown formatting
            if content.startswith("```json"): content = content[7:]
            if content.startswith("```"): content = content[3:]
            if content.endswith("```"): content = content[:-3]
            
            suggestions = json.loads(content.strip())
            if isinstance(suggestions, list) and len(suggestions) >= 3:
                suggestions = suggestions[:3]
            else:
                suggestions = ["Can you explain that in more detail?", "What is the next step?", "Are there any exceptions to this rule?"]
                
            _suggestion_cache[cache_key] = suggestions
                    
            return suggestions
        except Exception as e:
            print(f"Suggestion Generation Failed: {e}")
            return ["Can you explain that in more detail?", "What is the next step?", "Are there any exceptions to this rule?"]
