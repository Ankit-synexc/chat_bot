from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from models.query_model import QueryRequest, QueryResponse
from controllers.query_controller import ask_question, ask_question_stream

router = APIRouter(prefix="/api/v1/query", tags=["query"])

from utils.dependencies import check_rate_limit
from models.auth_model import UserDocument

@router.post("/ask", response_model=QueryResponse)
async def ask_question_route(request: QueryRequest, user: UserDocument = Depends(check_rate_limit)):
    """Ask a question and receive a complete answer with sources."""
    if request.stream:
        return await ask_question_stream(request, str(user.id))
    return await ask_question(request, str(user.id))

@router.post("/ask/stream", response_class=StreamingResponse)
async def ask_question_stream_route(request: QueryRequest, user: UserDocument = Depends(check_rate_limit)):
    """Ask a question and receive a Server-Sent Events (SSE) stream of the answer."""
    return await ask_question_stream(request, str(user.id))
