# models/document_model.py
from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator
from models.common import PyObjectId

class ChunkDocument(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None, description="MongoDB document ID")
    document_id: str = Field(..., description="Unique identifier for the parent document")
    text: str = Field(..., description="The textual content of the chunk")
    embedding: list[float] = Field(..., description="Vector embedding of the chunk text (384 dimensions)")
    source_file: str = Field(..., description="Name of the source file")
    page_number: Optional[int] = Field(default=None, description="Page number where the chunk was found")
    chunk_index: int = Field(..., description="Sequential index of the chunk within the document")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Timestamp of chunk creation")

    @field_validator('embedding')
    @classmethod
    def check_embedding_length(cls, v: list[float]) -> list[float]:
        if len(v) != 384:
            raise ValueError(f"Embedding must have exactly 384 dimensions, got {len(v)}")
        return v

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_schema_extra={
            "example": {
                "document_id": "doc_123",
                "text": "This is a sample chunk of text.",
                "embedding": [0.1] * 384,
                "source_file": "sample.pdf",
                "page_number": 1,
                "chunk_index": 0
            }
        }
    )

class DocumentUploadResponse(BaseModel):
    document_id: str = Field(..., description="Unique identifier for the uploaded document")
    source_file: str = Field(..., description="Name of the uploaded file")
    total_chunks: int = Field(..., description="Total number of chunks created from the document")
    uploaded_at: datetime = Field(..., description="Timestamp of document upload")

    model_config = ConfigDict(populate_by_name=True)

class DocumentListItem(BaseModel):
    document_id: str = Field(..., description="Unique identifier for the document")
    source_file: str = Field(..., description="Name of the source file")
    chunk_count: int = Field(..., description="Number of chunks associated with the document")
    created_at: datetime = Field(..., description="Timestamp of document creation")

    model_config = ConfigDict(populate_by_name=True)

class DeleteDocumentResponse(BaseModel):
    document_id: str = Field(..., description="Unique identifier of the deleted document")
    deleted_chunks: int = Field(..., description="Number of chunks deleted")

    model_config = ConfigDict(populate_by_name=True)

class DeleteAllDocumentsResponse(BaseModel):
    deleted_chunks: int = Field(..., description="Total number of chunks deleted across all documents")

    model_config = ConfigDict(populate_by_name=True)
