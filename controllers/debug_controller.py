"""
Diagnostic endpoint to debug the RAG pipeline.
Run: uvicorn main:app --reload, then visit /debug/check in browser or Swagger.
"""
import logging
from config.database import get_collection
from config.settings import settings
from ml_core.embedder import embedder

logger = logging.getLogger(__name__)

async def run_diagnostics(question: str = "What does this company do?") -> dict:
    results = {}
    
    # 1. Check if chunks exist in DB
    collection = get_collection(settings.CHUNKS_COLLECTION)
    total_chunks = await collection.count_documents({})
    results["total_chunks_in_db"] = total_chunks
    
    if total_chunks == 0:
        results["error"] = "NO CHUNKS FOUND IN DATABASE. Upload a document first."
        return results
    
    # 2. Show sample chunk (without embedding to keep output small)
    sample = await collection.find_one({}, {"embedding": 0})
    if sample:
        sample["_id"] = str(sample["_id"])
        results["sample_chunk"] = sample
    
    # 3. Check if embeddings exist in chunks
    chunk_with_embedding = await collection.find_one({"embedding": {"$exists": True}})
    results["chunks_have_embeddings"] = chunk_with_embedding is not None
    
    if chunk_with_embedding:
        emb = chunk_with_embedding.get("embedding", [])
        results["embedding_dimensions"] = len(emb)
        results["embedding_sample_first_5"] = emb[:5] if emb else []
    
    # 4. Try vector search directly
    try:
        question_embedding = embedder.embed_text(question)
        results["question_embedding_dims"] = len(question_embedding)
        
        pipeline = [
            {
                "$vectorSearch": {
                    "index": "vector_index",
                    "path": "embedding",
                    "queryVector": question_embedding,
                    "numCandidates": 50,
                    "limit": 5
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "text": 1,
                    "source_file": 1,
                    "chunk_index": 1,
                    "score": {"$meta": "vectorSearchScore"}
                }
            }
        ]
        cursor = collection.aggregate(pipeline)
        vector_results = await cursor.to_list(length=5)
        results["vector_search_results_count"] = len(vector_results)
        results["vector_search_results"] = vector_results
        
    except Exception as e:
        results["vector_search_error"] = str(e)
    
    # 5. List all unique documents
    doc_cursor = collection.aggregate([
        {"$group": {"_id": "$document_id", "source_file": {"$first": "$source_file"}, "count": {"$sum": 1}}},
    ])
    docs = await doc_cursor.to_list(length=100)
    results["uploaded_documents"] = [{"document_id": d["_id"], "source_file": d["source_file"], "chunks": d["count"]} for d in docs]
    
    return results
