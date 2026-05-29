# models/query_model.py
from pydantic import BaseModel, ConfigDict, Field, field_validator


class QueryRequest(BaseModel):
    question: str = Field(..., min_length=1, description="The user's question to answer")
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
    page_number: int | None = Field(default=None, description="The page number, if applicable")
    chunk_index: int = Field(..., description="The index of the chunk in the document")
    score: float = Field(..., description="The relevance score")

    model_config = ConfigDict(populate_by_name=True)


class QueryResponse(BaseModel):
    answer: str = Field(..., description="The generated answer to the question")

    model_config = ConfigDict(populate_by_name=True)


class StreamChunk(BaseModel):
    delta: str = Field(..., description="The new text delta to append")
    done: bool = Field(..., description="Whether the stream has finished")

    model_config = ConfigDict(populate_by_name=True)
