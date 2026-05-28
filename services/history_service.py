import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from config.database import get_collection
from config.settings import settings

logger = logging.getLogger(__name__)

async def save_history(user_id: str, question: str, answer: str, sources: List[Dict[str, Any]], latency_ms: int, model_used: str, session_id: Optional[str] = None) -> str:
    collection = get_collection(settings.HISTORY_COLLECTION)
    doc = {
        "user_id": user_id,
        "session_id": session_id,
        "question": question,
        "answer": answer,
        "sources": sources,
        "latency_ms": latency_ms,
        "model_used": model_used,
        "created_at": datetime.now(timezone.utc)
    }
    result = await collection.insert_one(doc)
    return str(result.inserted_id)

async def get_history(user_id: str, page: int, page_size: int) -> Dict[str, Any]:
    collection = get_collection(settings.HISTORY_COLLECTION)
    skip = (page - 1) * page_size
    
    filter_query = {"user_id": user_id}
    total = await collection.count_documents(filter_query)
    
    cursor = collection.find(filter_query).sort("created_at", -1).skip(skip).limit(page_size)
    items = await cursor.to_list(length=page_size)
    
    for item in items:
        item["_id"] = str(item["_id"])
        
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size
    }

async def delete_history(user_id: str) -> int:
    collection = get_collection(settings.HISTORY_COLLECTION)
    result = await collection.delete_many({"user_id": user_id})
    return result.deleted_count

async def get_recent_history(user_id: str, session_id: str, limit: int = 5) -> List[Dict[str, Any]]:
    if not session_id:
        return []
    collection = get_collection(settings.HISTORY_COLLECTION)
    filter_query = {"user_id": user_id, "session_id": session_id}
    # Get last `limit` questions, sorted by newest first
    cursor = collection.find(filter_query).sort("created_at", -1).limit(limit)
    items = await cursor.to_list(length=limit)
    # Reverse to get chronological order (oldest to newest)
    items.reverse()
    return items
