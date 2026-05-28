import logging
import time
import asyncio
from typing import AsyncGenerator
from fastapi import HTTPException
from fastapi.responses import StreamingResponse

from models.query_model import QueryRequest, QueryResponse, SourceReference, StreamChunk
from ml_core.embedder import embedder
from ml_core.reranker import reranker
from ml_core.groq_client import generate_answer, generate_answer_stream
from ml_core.prompt_builder import build_system_prompt, build_rag_prompt
from services.query_service import hybrid_search
from services.history_service import save_history, get_recent_history
from services.cache_service import get_cached, set_cache
from config.settings import settings

logger = logging.getLogger(__name__)

async def ask_question(request: QueryRequest, user_id: str) -> QueryResponse:
    start_time = time.time()
    try:
        # 1. Check cache
        cache_key = f"{request.question}_{request.session_id}" if request.session_id else request.question
        cached_response = get_cached(cache_key)
        if cached_response:
            logger.info("Cache hit for question.")
            cached_response.latency_ms = int((time.time() - start_time) * 1000)
            return cached_response

        chat_history = []
        if request.session_id:
            chat_history = await get_recent_history(user_id, request.session_id)

        # 2. Embed question
        question_embedding = embedder.embed_text(request.question)

        # 3. Hybrid Search
        search_results = await hybrid_search(request.question, question_embedding, request.top_k)
        logger.info(f"Hybrid search returned {len(search_results)} candidates")

        if not search_results:
            answer = "I'm sorry, but I couldn't find any relevant information in the uploaded documents to answer your question."
            sources = []
            latency = int((time.time() - start_time) * 1000)
            response = QueryResponse(
                answer=answer, sources=sources, latency_ms=latency,
                cached=False, model_used=settings.GROQ_MODEL
            )
            await save_history(user_id, request.question, answer, [], latency, settings.GROQ_MODEL, request.session_id)
            set_cache(cache_key, response)
            return response

        # 4. Bypass Rerank to save memory on free tier
        reranked_chunks = search_results

        # 5. Check Similarity Threshold bypassed since we use RRF score
        best_score = reranked_chunks[0]["score"] if reranked_chunks else 0
        logger.info(f"Top RRF score: {best_score:.4f}")
        
        if not reranked_chunks:
            answer = "I'm sorry, but I couldn't find any relevant information in the uploaded documents to answer your question."
            sources = []
            
            latency = int((time.time() - start_time) * 1000)
            response = QueryResponse(
                answer=answer,
                sources=sources,
                latency_ms=latency,
                cached=False,
                model_used=settings.GROQ_MODEL
            )
            
            # Save history & cache
            await save_history(user_id, request.question, answer, [], latency, settings.GROQ_MODEL, request.session_id)
            set_cache(cache_key, response)
            return response

        # Format sources
        sources = [
            SourceReference(
                text=c["text"],
                source_file=c["source_file"],
                page_number=c.get("page_number"),
                chunk_index=c["chunk_index"],
                score=c["score"]
            )
            for c in reranked_chunks
        ]

        # 6. Build prompt
        system_prompt = build_system_prompt()
        rag_prompt = build_rag_prompt(request.question, reranked_chunks, chat_history)

        # 7. Call LLM
        answer = await generate_answer(rag_prompt, system_prompt)

        # 8. Calculate latency
        latency = int((time.time() - start_time) * 1000)

        # 9. Build response
        response = QueryResponse(
            answer=answer,
            sources=sources,
            latency_ms=latency,
            cached=False,
            model_used=settings.GROQ_MODEL
        )

        # 10. Save history and cache
        sources_dict = [s.model_dump() for s in sources]
        await save_history(user_id, request.question, answer, sources_dict, latency, settings.GROQ_MODEL, request.session_id)
        set_cache(cache_key, response)
        
        return response

    except Exception as e:
        logger.error(f"Error processing question: {e}")
        raise HTTPException(status_code=500, detail="An error occurred while processing your question.")


async def ask_question_stream(request: QueryRequest, user_id: str) -> StreamingResponse:
    start_time = time.time()
    
    async def stream_generator() -> AsyncGenerator[str, None]:
        complete_answer = ""
        sources = []
        try:
            # 1. Check cache
            cache_key = f"{request.question}_{request.session_id}" if request.session_id else request.question
            cached_response = get_cached(cache_key)
            if cached_response:
                logger.info("Cache hit for stream question.")
                sources = cached_response.sources
                complete_answer = cached_response.answer
                
                # Simulate streaming char by char
                for char in cached_response.answer:
                    chunk = StreamChunk(delta=char, done=False)
                    yield f"data: {chunk.model_dump_json()}\n\n"
                    await asyncio.sleep(0.005)
                
                done_chunk = StreamChunk(delta="", done=True)
                yield f"data: {done_chunk.model_dump_json()}\n\n"
                return

            chat_history = []
            if request.session_id:
                chat_history = await get_recent_history(user_id, request.session_id)

            # 2. Embed question
            question_embedding = embedder.embed_text(request.question)

            # 3. Hybrid Search
            search_results = await hybrid_search(request.question, question_embedding, request.top_k)

            # 4. Bypass Rerank to save memory
            reranked_chunks = search_results

            # 5. Check Similarity Threshold bypassed since we use RRF score
            best_score = reranked_chunks[0]["score"] if reranked_chunks else 0
            if not reranked_chunks:
                complete_answer = "I'm sorry, but I couldn't find any relevant information in the uploaded documents to answer your question."
                
                for char in complete_answer:
                    chunk = StreamChunk(delta=char, done=False)
                    yield f"data: {chunk.model_dump_json()}\n\n"
                    await asyncio.sleep(0.005)
                
                done_chunk = StreamChunk(delta="", done=True)
                yield f"data: {done_chunk.model_dump_json()}\n\n"
                
                latency = int((time.time() - start_time) * 1000)
                await save_history(user_id, request.question, complete_answer, [], latency, settings.GROQ_MODEL, request.session_id)
                
                response = QueryResponse(
                    answer=complete_answer,
                    sources=[],
                    latency_ms=latency,
                    cached=False,
                    model_used=settings.GROQ_MODEL
                )
                set_cache(cache_key, response)
                return

            sources = [
                SourceReference(
                    text=c["text"],
                    source_file=c["source_file"],
                    page_number=c.get("page_number"),
                    chunk_index=c["chunk_index"],
                    score=c["score"]
                )
                for c in reranked_chunks
            ]

            # 6. Build prompt
            system_prompt = build_system_prompt()
            rag_prompt = build_rag_prompt(request.question, reranked_chunks, chat_history)

            # 7 & 8. Stream from Groq and yield
            async for token in generate_answer_stream(rag_prompt, system_prompt):
                complete_answer += token
                chunk = StreamChunk(delta=token, done=False)
                yield f"data: {chunk.model_dump_json()}\n\n"

            # 9. Yield completion chunk
            done_chunk = StreamChunk(delta="", done=True)
            yield f"data: {done_chunk.model_dump_json()}\n\n"

            # 10. Save complete answer to history & cache
            latency = int((time.time() - start_time) * 1000)
            sources_dict = [s.model_dump() for s in sources]
            await save_history(user_id, request.question, complete_answer, sources_dict, latency, settings.GROQ_MODEL, request.session_id)
            
            response = QueryResponse(
                answer=complete_answer,
                sources=sources,
                latency_ms=latency,
                cached=False,
                model_used=settings.GROQ_MODEL
            )
            set_cache(cache_key, response)

        except Exception as e:
            logger.error(f"Error in streaming generation: {e}")
            error_chunk = StreamChunk(delta="\n[Error: An error occurred while generating the answer.]", done=True)
            yield f"data: {error_chunk.model_dump_json()}\n\n"
            
    # Return StreamingResponse with SSE headers
    return StreamingResponse(
        stream_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no"
        }
    )
