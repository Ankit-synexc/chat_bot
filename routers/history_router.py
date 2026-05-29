from fastapi import APIRouter, Query
from models.history_model import HistoryListResponse
from models.common import BaseResponse
from controllers.history_controller import get_history_controller, delete_history_controller

router = APIRouter(prefix="/api/v1/history", tags=["admin"])


@router.get("", response_model=HistoryListResponse)
async def get_history_route(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
):
    """Retrieve paginated chat history (admin — use via Swagger)."""
    return await get_history_controller(page, page_size)


@router.delete("", response_model=BaseResponse)
async def delete_history_route():
    """Delete all chat history (admin — use via Swagger)."""
    return await delete_history_controller()
