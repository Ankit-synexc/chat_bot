# models/history_model.py
from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field
from models.common import PyObjectId


class HistoryEntry(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None, description="MongoDB document ID")
    question: str = Field(..., description="The user's question")
    answer: str = Field(..., description="The generated answer")
    model_used: str = Field(..., description="LLM used to generate the answer")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp of the query"
    )

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)


class HistoryListResponse(BaseModel):
    items: list[HistoryEntry] = Field(..., description="List of history entries for the current page")
    total: int = Field(..., description="Total number of history entries")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Number of items per page")

    model_config = ConfigDict(populate_by_name=True)
