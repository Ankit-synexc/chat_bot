import logging
from typing import List, Dict, Any
from datetime import datetime, timezone
from config.database import get_collection
from config.settings import settings

logger = logging.getLogger(__name__)


async def save_history(question: str, answer: str, model_used: str) -> str:
    """Save a Q&A pair to MongoDB history (no user/session — global)."""
    collection = get_collection(settings.HISTORY_COLLECTION)
    doc = {
        "question": question,
        "answer": answer,
        "model_used": model_used,
        "created_at": datetime.now(timezone.utc)
    }
    result = await collection.insert_one(doc)
    return str(result.inserted_id)


async def get_recent_history(limit: int = 5) -> List[Dict[str, Any]]:
    """Fetch the most recent `limit` Q&A pairs from MongoDB for conversational memory."""
    collection = get_collection(settings.HISTORY_COLLECTION)
    # Sort newest first, take limit, then reverse to chronological order
    cursor = collection.find({}).sort("created_at", -1).limit(limit)
    items = await cursor.to_list(length=limit)
    items.reverse()
    return items


async def get_history(page: int, page_size: int) -> Dict[str, Any]:
    """Paginated history for admin use via Swagger."""
    collection = get_collection(settings.HISTORY_COLLECTION)
    skip = (page - 1) * page_size

    total = await collection.count_documents({})
    cursor = collection.find({}).sort("created_at", -1).skip(skip).limit(page_size)
    items = await cursor.to_list(length=page_size)

    for item in items:
        item["_id"] = str(item["_id"])

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size
    }


async def delete_all_history() -> int:
    """Delete all chat history (admin use via Swagger)."""
    collection = get_collection(settings.HISTORY_COLLECTION)
    result = await collection.delete_many({})
    return result.deleted_count
