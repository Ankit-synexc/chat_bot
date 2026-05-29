import logging
from typing import List, Dict, Any
from config.database import get_collection
from config.settings import settings
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

async def create_document_record(document_id: str, source_file: str, total_chunks: int):
    collection = get_collection(settings.DOCUMENTS_COLLECTION)
    doc = {
        "document_id": document_id,
        "source_file": source_file,
        "total_chunks": total_chunks,
        "processed_chunks": 0,
        "status": "processing",
        "created_at": datetime.now(timezone.utc)
    }
    await collection.insert_one(doc)

async def update_document_progress(document_id: str, processed_chunks: int, status: str):
    collection = get_collection(settings.DOCUMENTS_COLLECTION)
    await collection.update_one(
        {"document_id": document_id},
        {"$set": {"processed_chunks": processed_chunks, "status": status}}
    )

async def insert_chunks(document_id: str, source_file: str, chunks: List[str], embeddings: List[List[float]], start_index: int = 0) -> int:
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
            "chunk_index": start_index + i,
            "created_at": datetime.now(timezone.utc)
        }
        documents.append(doc)
        
    result = await collection.insert_many(documents)
    return len(result.inserted_ids)

async def get_all_documents() -> List[Dict[str, Any]]:
    collection = get_collection(settings.DOCUMENTS_COLLECTION)
    cursor = collection.find({}).sort("created_at", -1)
    return await cursor.to_list(length=None)

async def delete_document(document_id: str) -> int:
    chunks_collection = get_collection(settings.CHUNKS_COLLECTION)
    docs_collection = get_collection(settings.DOCUMENTS_COLLECTION)
    
    result = await chunks_collection.delete_many({"document_id": document_id})
    await docs_collection.delete_one({"document_id": document_id})
    return result.deleted_count

async def delete_all_documents() -> int:
    chunks_collection = get_collection(settings.CHUNKS_COLLECTION)
    docs_collection = get_collection(settings.DOCUMENTS_COLLECTION)
    
    result = await chunks_collection.delete_many({})
    await docs_collection.delete_many({})
    return result.deleted_count

async def document_exists(source_file: str) -> bool:
    collection = get_collection(settings.DOCUMENTS_COLLECTION)
    doc = await collection.find_one({"source_file": source_file})
    return doc is not None
