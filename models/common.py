# models/common.py
from typing import Any, Generic, TypeVar
from pydantic import BaseModel, ConfigDict, Field
from pydantic.functional_validators import BeforeValidator
from typing_extensions import Annotated

# Represents an ObjectId field in the database.
# It will be represented as a `str` on the model so that it can be serialized to JSON.
PyObjectId = Annotated[str, BeforeValidator(str)]

T = TypeVar('T')

class BaseResponse(BaseModel, Generic[T]):
    success: bool = Field(..., description="Indicates if the request was successful")
    message: str = Field(..., description="Response message or error description")
    data: T | None = Field(default=None, description="The response payload")

    model_config = ConfigDict(populate_by_name=True)

class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T] = Field(..., description="List of items for the current page")
    total: int = Field(..., description="Total number of items across all pages")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Number of items per page")
    total_pages: int = Field(..., description="Total number of pages")

    model_config = ConfigDict(populate_by_name=True)
