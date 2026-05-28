import logging
from typing import List, Dict, Any
from config.database import get_collection
from config.settings import settings
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

async def insert_chunks(document_id: str, source_file: str, chunks: List[str], embeddings: List[List[float]]) -> int:
    collection = get_collection(settings.CHUNKS_COLLECTION)
    if not chunks:
        return 0
        
    documents = []
    for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
        doc = {
            "document_id": document_id,
            "text": chunk,
            "embedding": embedding,
            "source_file": source_file,
            "chunk_index": i,
            "created_at": datetime.now(timezone.utc)
        }
        documents.append(doc)
        
    result = await collection.insert_many(documents)
    return len(result.inserted_ids)

async def get_all_documents() -> List[Dict[str, Any]]:
    collection = get_collection(settings.CHUNKS_COLLECTION)
    pipeline = [
        {"$group": {
            "_id": {"document_id": "$document_id", "source_file": "$source_file"},
            "chunk_count": {"$sum": 1},
            "created_at": {"$first": "$created_at"}
        }},
        {"$project": {
            "_id": 0,
            "document_id": "$_id.document_id",
            "source_file": "$_id.source_file",
            "chunk_count": 1,
            "created_at": 1
        }},
        {"$sort": {"created_at": -1}}
    ]
    cursor = collection.aggregate(pipeline)
    return await cursor.to_list(length=None)

async def delete_document(document_id: str) -> int:
    collection = get_collection(settings.CHUNKS_COLLECTION)
    result = await collection.delete_many({"document_id": document_id})
    return result.deleted_count

async def delete_all_documents() -> int:
    collection = get_collection(settings.CHUNKS_COLLECTION)
    result = await collection.delete_many({})
    return result.deleted_count

async def document_exists(source_file: str) -> bool:
    collection = get_collection(settings.CHUNKS_COLLECTION)
    doc = await collection.find_one({"source_file": source_file})
    return doc is not None
