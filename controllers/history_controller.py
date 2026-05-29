import logging
from models.history_model import HistoryListResponse
from models.common import BaseResponse
from services.history_service import get_history, delete_all_history

logger = logging.getLogger(__name__)


async def get_history_controller(page: int, page_size: int) -> HistoryListResponse:
    history_data = await get_history(page, page_size)
    return HistoryListResponse(**history_data)


async def delete_history_controller() -> BaseResponse:
    deleted_count = await delete_all_history()
    return BaseResponse(
        success=True,
        message=f"Deleted {deleted_count} history entries",
        data=deleted_count
    )
