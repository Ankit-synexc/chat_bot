import hashlib
import logging
from typing import Dict, Any, Optional
from collections import OrderedDict
from models.query_model import QueryResponse

logger = logging.getLogger(__name__)

class CacheService:
    def __init__(self, max_size: int = 100):
        self.cache: OrderedDict[str, QueryResponse] = OrderedDict()
        self.max_size = max_size
        self._hits = 0
        self._misses = 0
        
    def _hash_question(self, question: str) -> str:
        normalized = question.strip().lower()
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

    def get_cached(self, question: str) -> Optional[QueryResponse]:
        key = self._hash_question(question)
        if key in self.cache:
            self._hits += 1
            response = self.cache[key]
            # Copy to modify the cached status
            response_dict = response.model_dump()
            response_dict["cached"] = True
            return QueryResponse(**response_dict)
        self._misses += 1
        return None
        
    def set_cache(self, question: str, response: QueryResponse) -> None:
        key = self._hash_question(question)
        if key not in self.cache:
            if len(self.cache) >= self.max_size:
                # FIFO eviction
                self.cache.popitem(last=False)
        self.cache[key] = response
        
    def cache_stats(self) -> Dict[str, int]:
        return {
            "size": len(self.cache),
            "hit_count": self._hits,
            "miss_count": self._misses
        }

    def clear_all(self) -> None:
        """Flush the entire cache."""
        self.cache.clear()
        logger.info("Cache cleared.")

# Singleton instance
cache_service = CacheService()

def get_cached(question: str) -> Optional[QueryResponse]:
    return cache_service.get_cached(question)

def set_cache(question: str, response: QueryResponse) -> None:
    cache_service.set_cache(question, response)

def cache_stats() -> Dict[str, int]:
    return cache_service.cache_stats()

def clear_cache() -> None:
    cache_service.clear_all()
