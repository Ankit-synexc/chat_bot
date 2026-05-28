from fastapi import APIRouter, Query, Depends
from models.auth_model import UserDocument
from models.history_model import HistoryListResponse
from models.common import BaseResponse
from controllers.history_controller import get_history_controller, delete_history_controller
from utils.dependencies import check_rate_limit

router = APIRouter(prefix="/api/v1/history", tags=["history"])

@router.get("", response_model=HistoryListResponse)
async def get_history_route(
    page: int = Query(1, ge=1), 
    page_size: int = Query(10, ge=1, le=100), 
    user: UserDocument = Depends(check_rate_limit)
):
    """Retrieve paginated chat history for the authenticated user."""
    return await get_history_controller(page, page_size, user)

@router.delete("", response_model=BaseResponse)
async def delete_history_route(user: UserDocument = Depends(check_rate_limit)):
    """Delete all chat history for the authenticated user."""
    return await delete_history_controller(user)
