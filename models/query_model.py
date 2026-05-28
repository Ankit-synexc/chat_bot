# models/query_model.py
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator

class QueryRequest(BaseModel):
    question: str = Field(..., min_length=3, description="The user's question to answer")
    session_id: Optional[str] = Field(default=None, description="Optional session ID to remember conversation history")
    top_k: int = Field(default=5, description="Number of top chunks to retrieve before reranking")
    stream: bool = Field(default=False, description="Whether to stream the response back")

    @field_validator('question')
    @classmethod
    def question_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Question cannot be empty or just whitespace")
        return v

    model_config = ConfigDict(populate_by_name=True)

class SourceReference(BaseModel):
    text: str = Field(..., description="The text of the source chunk")
    source_file: str = Field(..., description="The file the chunk came from")
    page_number: Optional[int] = Field(default=None, description="The page number, if applicable")
    chunk_index: int = Field(..., description="The index of the chunk in the document")
    score: float = Field(..., description="The relevance score (e.g., from cross-encoder)")

    model_config = ConfigDict(populate_by_name=True)

class QueryResponse(BaseModel):
    answer: str = Field(..., description="The generated answer to the question")
    # sources: list[SourceReference] = Field(..., description="List of source chunks used to generate the answer")
    # latency_ms: int = Field(..., description="Total latency of the request in milliseconds")
    # cached: bool = Field(default=False, description="Whether the answer was served from cache")
    # model_used: str = Field(..., description="The name of the LLM used to generate the answer")

    model_config = ConfigDict(populate_by_name=True)

class StreamChunk(BaseModel):
    delta: str = Field(..., description="The new text delta to append")
    done: bool = Field(..., description="Whether the stream has finished")

    model_config = ConfigDict(populate_by_name=True)
