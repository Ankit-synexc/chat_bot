import logging
import time
import asyncio
from typing import AsyncGenerator
from fastapi import HTTPException
from fastapi.responses import StreamingResponse

from models.query_model import QueryRequest, QueryResponse, StreamChunk
from ml_core.embedder import embedder
from ml_core.groq_client import generate_answer, generate_answer_stream
from ml_core.prompt_builder import build_system_prompt, build_rag_prompt
from services.query_service import hybrid_search
from services.history_service import save_history, get_recent_history
from services.cache_service import get_cached, set_cache
from config.settings import settings

logger = logging.getLogger(__name__)


async def ask_question(request: QueryRequest) -> QueryResponse:
    try:
        # 1. Check cache
        cached_response = get_cached(request.question)
        if cached_response:
            logger.info("Cache hit for question.")
            return cached_response

        # 2. Fetch last 5 messages for conversational memory (global, no session)
        chat_history = await get_recent_history(limit=5)

        # 3. Embed question
        question_embedding = embedder.embed_text(request.question)

        # 4. Hybrid Search
        search_results = await hybrid_search(request.question, question_embedding, request.top_k)
        logger.info(f"Hybrid search returned {len(search_results)} candidates")

        if not search_results:
            answer = "I'm sorry, but I couldn't find any relevant information in the uploaded documents to answer your question."
            response = QueryResponse(answer=answer)
            await save_history(request.question, answer, settings.GROQ_MODEL)
            set_cache(request.question, response)
            return response

        # 5. Build prompt with chat history for memory
        system_prompt = build_system_prompt()
        rag_prompt = build_rag_prompt(request.question, search_results, chat_history)

        # 6. Call LLM
        answer = await generate_answer(rag_prompt, system_prompt)

        # 7. Build response
        response = QueryResponse(answer=answer)

        # 8. Save to history & cache
        await save_history(request.question, answer, settings.GROQ_MODEL)
        set_cache(request.question, response)

        return response

    except Exception as e:
        logger.error(f"Error processing question: {e}")
        raise HTTPException(status_code=500, detail="An error occurred while processing your question.")


async def ask_question_stream(request: QueryRequest) -> StreamingResponse:

    async def stream_generator() -> AsyncGenerator[str, None]:
        complete_answer = ""
        try:
            # 1. Check cache
            cached_response = get_cached(request.question)
            if cached_response:
                logger.info("Cache hit for stream question.")
                complete_answer = cached_response.answer

                for char in cached_response.answer:
                    chunk = StreamChunk(delta=char, done=False)
                    yield f"data: {chunk.model_dump_json()}\n\n"
                    await asyncio.sleep(0.005)

                done_chunk = StreamChunk(delta="", done=True)
                yield f"data: {done_chunk.model_dump_json()}\n\n"
                return

            # 2. Fetch last 5 messages for conversational memory (global, no session)
            chat_history = await get_recent_history(limit=5)

            # 3. Embed question
            question_embedding = embedder.embed_text(request.question)

            # 4. Hybrid Search
            search_results = await hybrid_search(request.question, question_embedding, request.top_k)

            if not search_results:
                complete_answer = "I'm sorry, but I couldn't find any relevant information in the uploaded documents to answer your question."

                for char in complete_answer:
                    chunk = StreamChunk(delta=char, done=False)
                    yield f"data: {chunk.model_dump_json()}\n\n"
                    await asyncio.sleep(0.005)

                done_chunk = StreamChunk(delta="", done=True)
                yield f"data: {done_chunk.model_dump_json()}\n\n"

                await save_history(request.question, complete_answer, settings.GROQ_MODEL)
                set_cache(request.question, QueryResponse(answer=complete_answer))
                return

            # 5. Build prompt with chat history for memory
            system_prompt = build_system_prompt()
            rag_prompt = build_rag_prompt(request.question, search_results, chat_history)

            # 6. Stream from Groq and yield tokens
            async for token in generate_answer_stream(rag_prompt, system_prompt):
                complete_answer += token
                chunk = StreamChunk(delta=token, done=False)
                yield f"data: {chunk.model_dump_json()}\n\n"

            # 7. Yield done signal
            done_chunk = StreamChunk(delta="", done=True)
            yield f"data: {done_chunk.model_dump_json()}\n\n"

            # 8. Save to history & cache
            await save_history(request.question, complete_answer, settings.GROQ_MODEL)
            set_cache(request.question, QueryResponse(answer=complete_answer))

        except Exception as e:
            logger.error(f"Error in streaming generation: {e}")
            error_chunk = StreamChunk(delta="\n[Error: An error occurred while generating the answer.]", done=True)
            yield f"data: {error_chunk.model_dump_json()}\n\n"

    return StreamingResponse(
        stream_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no"
        }
    )
