import logging
import time
import math
from typing import List, Dict, Any, Optional
from sentence_transformers import CrossEncoder

logger = logging.getLogger(__name__)

class Reranker:
    _instance = None
    _model: Optional[CrossEncoder] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Reranker, cls).__new__(cls)
        return cls._instance

    def _load_model(self):
        if self._model is None:
            start_time = time.time()
            logger.info("Loading cross-encoder model 'cross-encoder/ms-marco-MiniLM-L-6-v2'...")
            self._model = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
            load_time = time.time() - start_time
            logger.info(f"Reranker model loaded in {load_time:.2f} seconds.")

    def rerank(self, query: str, chunks: List[Dict[str, Any]], top_k: int) -> List[Dict[str, Any]]:
        if not chunks:
            return []
            
        self._load_model()
        
        # Prepare pairs of (query, chunk_text)
        pairs = [[query, chunk.get("text", "")] for chunk in chunks]
        
        # Predict scores
        scores = self._model.predict(pairs)
        
        # Update scores in chunks and sort, applying sigmoid to normalize logits to 0-1
        for i, chunk in enumerate(chunks):
            raw_score = float(scores[i])
            # Apply sigmoid
            normalized_score = 1 / (1 + math.exp(-raw_score))
            chunk["score"] = normalized_score
            
        # Sort descending by score
        ranked_chunks = sorted(chunks, key=lambda x: x["score"], reverse=True)
        return ranked_chunks[:top_k]

    def is_loaded(self) -> bool:
        return self._model is not None

# Singleton instance
reranker = Reranker()
