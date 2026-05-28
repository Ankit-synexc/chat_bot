import time
from typing import Dict, Any
from config.settings import settings
from config.database import ping_db
from ml_core.embedder import embedder
from ml_core.reranker import reranker
from services.cache_service import cache_stats

# Global to track start time
APP_START_TIME = time.time()

async def health_check() -> Dict[str, Any]:
    uptime_seconds = int(time.time() - APP_START_TIME)
    db_status = await ping_db()
    
    return {
        "status": "healthy" if db_status else "degraded",
        "app_name": settings.APP_NAME,
        "version": settings.VERSION,
        "uptime_seconds": uptime_seconds,
        "mongodb": "connected" if db_status else "disconnected",
        "embedder_loaded": embedder.is_loaded(),
        "reranker_loaded": reranker.is_loaded(),
        "cache_stats": cache_stats()
    }
