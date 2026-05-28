import logging
from typing import List, Dict, Any
from rank_bm25 import BM25Okapi
from config.database import get_collection
from config.settings import settings

logger = logging.getLogger(__name__)

async def vector_search(embedding: List[float], top_k: int) -> List[Dict[str, Any]]:
    collection = get_collection(settings.CHUNKS_COLLECTION)
    pipeline = [
        {
            "$vectorSearch": {
                "index": "vector_index",
                "path": "embedding",
                "queryVector": embedding,
                "numCandidates": top_k * 10,
                "limit": top_k
            }
        },
        {
            "$project": {
                "_id": 0,
                "text": 1,
                "source_file": 1,
                "page_number": 1,
                "chunk_index": 1,
                "score": {"$meta": "vectorSearchScore"}
            }
        }
    ]
    cursor = collection.aggregate(pipeline)
    return await cursor.to_list(length=top_k)

async def hybrid_search(question: str, embedding: List[float], top_k: int) -> List[Dict[str, Any]]:
    collection = get_collection(settings.CHUNKS_COLLECTION)
    
    # 1. Fetch top 200 chunks via vector search as candidate pool
    pipeline = [
        {
            "$vectorSearch": {
                "index": "vector_index",
                "path": "embedding",
                "queryVector": embedding,
                "numCandidates": 1000,
                "limit": 200
            }
        },
        {
            "$project": {
                "_id": 1,
                "text": 1,
                "source_file": 1,
                "page_number": 1,
                "chunk_index": 1,
                "score": {"$meta": "vectorSearchScore"}
            }
        }
    ]
    cursor = collection.aggregate(pipeline)
    candidates = await cursor.to_list(length=200)
    
    if not candidates:
        return []
        
    # 2. Run BM25 on candidates
    tokenized_corpus = [doc.get("text", "").lower().split() for doc in candidates]
    tokenized_query = question.lower().split()
    bm25 = BM25Okapi(tokenized_corpus)
    bm25_scores = bm25.get_scores(tokenized_query)
    
    # 3. Apply Reciprocal Rank Fusion (RRF)
    k = 60
    
    vector_ranked = sorted(candidates, key=lambda x: x.get("score", 0), reverse=True)
    vector_ranks = {str(doc["_id"]): i + 1 for i, doc in enumerate(vector_ranked)}
    
    for i, doc in enumerate(candidates):
        doc["bm25_score"] = float(bm25_scores[i])
        
    bm25_ranked = sorted(candidates, key=lambda x: x.get("bm25_score", 0), reverse=True)
    bm25_ranks = {str(doc["_id"]): i + 1 for i, doc in enumerate(bm25_ranked)}
    
    for doc in candidates:
        doc_id = str(doc["_id"])
        v_rank = vector_ranks.get(doc_id, 1000)
        b_rank = bm25_ranks.get(doc_id, 1000)
        rrf_score = (1.0 / (k + v_rank)) + (1.0 / (k + b_rank))
        doc["rrf_score"] = rrf_score
        
    final_ranked = sorted(candidates, key=lambda x: x["rrf_score"], reverse=True)
    
    results = []
    for doc in final_ranked[:top_k]:
        results.append({
            "text": doc.get("text", ""),
            "source_file": doc.get("source_file", ""),
            "page_number": doc.get("page_number"),
            "chunk_index": doc.get("chunk_index", 0),
            "score": doc["rrf_score"]
        })
        
    return results
