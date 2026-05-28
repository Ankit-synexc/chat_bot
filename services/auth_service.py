import logging
import jwt
import bcrypt
from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import HTTPException, status
from models.auth_model import UserDocument, TokenResponse, UserResponse
from config.database import get_collection
from config.settings import settings

logger = logging.getLogger(__name__)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def get_password_hash(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt

async def register_user(username: str, password: str) -> UserResponse:
    collection = get_collection(settings.USERS_COLLECTION)
    
    # Check if user exists
    existing_user = await collection.find_one({"username": username})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
        
    hashed_password = get_password_hash(password)
    doc = UserDocument(
        username=username,
        hashed_password=hashed_password,
        is_admin=False,
        is_active=True,
        created_at=datetime.now(timezone.utc),
        request_count=0
    )
    
    result = await collection.insert_one(doc.model_dump(by_alias=True, exclude={"id"}))
    user_id = str(result.inserted_id)
    
    return UserResponse(
        id=user_id,
        username=username,
        is_admin=False,
        created_at=doc.created_at
    )

async def authenticate_user(username: str, password: str) -> Optional[UserDocument]:
    collection = get_collection(settings.USERS_COLLECTION)
    user_dict = await collection.find_one({"username": username})
    
    if not user_dict:
        return None
        
    if not verify_password(password, user_dict["hashed_password"]):
        return None
        
    user_dict["_id"] = str(user_dict["_id"])
    return UserDocument(**user_dict)

async def increment_request_count(user_id: str) -> None:
    from bson import ObjectId
    collection = get_collection(settings.USERS_COLLECTION)
    await collection.update_one(
        {"_id": ObjectId(user_id)},
        {"$inc": {"request_count": 1}}
    )
