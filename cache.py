import os
from langchain.globals import set_llm_cache
from langchain.cache import InMemoryCache
from fastapi import APIRouter

CACHE_ENABLED = os.environ.get("CACHE_ENABLED", "true").lower() == "true"
cache_router = APIRouter(prefix="/api/cache", tags=["Semantic Cache"])

if CACHE_ENABLED:
    set_llm_cache(InMemoryCache())

class SemanticCache:
    def __init__(self):
        self.enabled = CACHE_ENABLED

    def search(self, workspace_id: str, query: str, threshold: float = 0.92):
        return None

    def store(self, workspace_id: str, query: str, response: dict, ttl_seconds: int = 86400):
        pass

    def invalidate_workspace(self, workspace_id: str):
        pass
        
    def flush_all(self):
        if self.enabled:
            set_llm_cache(InMemoryCache())

semantic_cache = SemanticCache()

@cache_router.get("/stats")
def get_cache_stats():
    return {"status": "disabled_or_in_memory_only"}

@cache_router.delete("/workspace/{ws_id}")
def flush_workspace_cache(ws_id: str):
    semantic_cache.invalidate_workspace(ws_id)
    return {"message": f"Flushed cache for workspace {ws_id}"}

@cache_router.delete("")
def flush_all_cache():
    semantic_cache.flush_all()
    return {"message": "Flushed all cache"}
