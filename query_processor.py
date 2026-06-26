import time
import asyncio
from typing import List, Tuple
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate

class HyDEExpander:
    def __init__(self, llm: BaseChatModel):
        self.llm = llm
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", "Please write a short, hypothetical paragraph that answers the following question. Do not provide any conversational filler, just the hypothetical answer text."),
            ("user", "{query}")
        ])
        self.chain = self.prompt | self.llm
        
    async def expand(self, query: str) -> str:
        response = await self.chain.ainvoke({"query": query})
        return response.content.strip()

class MultiQueryExpander:
    def __init__(self, llm: BaseChatModel):
        self.llm = llm
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an AI language model assistant. Your task is to generate 3 different versions of the given user query to retrieve relevant documents from a vector database. Provide these alternative questions separated by newlines, with no numbering, bullet points, or additional text."),
            ("user", "{query}")
        ])
        self.chain = self.prompt | self.llm
        
    async def expand(self, query: str) -> List[str]:
        response = await self.chain.ainvoke({"query": query})
        lines = [line.strip() for line in response.content.strip().split("\n") if line.strip()]
        return lines[:3]

class QueryProcessor:
    def __init__(self, llm: BaseChatModel):
        self.hyde = HyDEExpander(llm)
        self.multi_query = MultiQueryExpander(llm)
        
    async def process(self, query: str, use_hyde: bool, use_multi_query: bool) -> Tuple[List[str], float]:
        start_time = time.time()
        queries = [query]
        
        tasks = []
        if use_multi_query:
            tasks.append(self.multi_query.expand(query))
        else:
            tasks.append(asyncio.sleep(0, result=[]))
            
        if use_hyde:
            tasks.append(self.hyde.expand(query))
        else:
            tasks.append(asyncio.sleep(0, result=""))
            
        multi_result, hyde_result = await asyncio.gather(*tasks)
        
        if use_multi_query and multi_result:
            queries.extend(multi_result)
            
        if use_hyde and hyde_result:
            queries.append(hyde_result)
            
        latency = time.time() - start_time
        return queries, latency
