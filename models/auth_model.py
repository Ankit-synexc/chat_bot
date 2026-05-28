# models/auth_model.py
from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field
from models.common import PyObjectId

class UserCreate(BaseModel):
    username: str = Field(..., description="Unique username for the user")
    password: str = Field(..., min_length=6, description="Password for the user")

    model_config = ConfigDict(populate_by_name=True)

class UserLogin(BaseModel):
    username: str = Field(..., description="Username")
    password: str = Field(..., description="Password")

class UserResponse(BaseModel):
    id: str = Field(..., description="User ID")
    username: str = Field(..., description="Username")
    is_admin: bool = Field(default=False, description="Whether the user has admin privileges")
    created_at: datetime = Field(..., description="Account creation date")

    model_config = ConfigDict(populate_by_name=True)

class TokenResponse(BaseModel):
    access_token: str = Field(..., description="The JWT access token")
    token_type: str = Field(default="bearer", description="Token type")

    model_config = ConfigDict(populate_by_name=True)

class UserDocument(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None, description="MongoDB document ID")
    username: str = Field(..., description="Username")
    hashed_password: str = Field(..., description="Bcrypt hashed password")
    is_admin: bool = Field(default=False, description="Whether the user has admin privileges")
    is_active: bool = Field(default=True, description="Whether the user account is active")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Timestamp of account creation")
    request_count: int = Field(default=0, description="Number of requests made by this user")

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)
