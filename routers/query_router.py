from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from models.query_model import QueryRequest, QueryResponse
from controllers.query_controller import ask_question, ask_question_stream

router = APIRouter(prefix="/api/v1/query", tags=["query"])


@router.post("/ask", response_model=QueryResponse)
async def ask_question_route(request: QueryRequest):
    """Ask a question and receive a complete answer."""
    if request.stream:
        return await ask_question_stream(request)
    return await ask_question(request)


@router.post("/ask/stream", response_class=StreamingResponse)
async def ask_question_stream_route(request: QueryRequest):
    """Ask a question and receive a Server-Sent Events (SSE) stream of the answer."""
    return await ask_question_stream(request)
