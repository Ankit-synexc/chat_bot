import logging
import time
from typing import List, Optional
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

class Embedder:
    _instance = None
    _model: Optional[SentenceTransformer] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Embedder, cls).__new__(cls)
        return cls._instance

    def _load_model(self):
        if self._model is None:
            start_time = time.time()
            logger.info("Loading sentence-transformers model 'all-MiniLM-L6-v2'...")
            self._model = SentenceTransformer("all-MiniLM-L6-v2")
            load_time = time.time() - start_time
            logger.info(f"Model loaded in {load_time:.2f} seconds.")

    def embed_text(self, text: str) -> List[float]:
        self._load_model()
        if not text.strip():
            return [0.0] * 384
        # Return as list of floats, L2 normalized
        embeddings = self._model.encode(text, normalize_embeddings=True)
        return embeddings.tolist()

    def embed_batch(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        self._load_model()
        if not texts:
            return []
        embeddings = self._model.encode(texts, batch_size=batch_size, normalize_embeddings=True)
        return embeddings.tolist()

    def is_loaded(self) -> bool:
        return self._model is not None

# Singleton instance
embedder = Embedder()
