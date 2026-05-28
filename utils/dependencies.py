import math
import time
import jwt
from fastapi import Header, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer
from models.auth_model import UserDocument
from services.auth_service import increment_request_count
from config.database import get_collection
from utils.rate_limiter import rate_limiter
from config.settings import settings
from bson import ObjectId

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

async def get_current_user(token: str = Depends(oauth2_scheme)) -> UserDocument:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        username: str = payload.get("username")
        if username is None:
            raise credentials_exception
    except jwt.InvalidTokenError:
        raise credentials_exception
        
    collection = get_collection(settings.USERS_COLLECTION)
    user_dict = await collection.find_one({"username": username})
    if user_dict is None:
        raise credentials_exception
        
    user_dict["_id"] = str(user_dict["_id"])
    user = UserDocument(**user_dict)
    
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
        
    return user

async def require_admin(current_user: UserDocument = Depends(get_current_user)) -> UserDocument:
    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
    return current_user

async def check_rate_limit(user: UserDocument = Depends(get_current_user)) -> UserDocument:
    if user.is_admin:
        return user

    user_id = str(user.id)
    
    if not rate_limiter.is_allowed(user_id):
        stats = rate_limiter.get_stats(user_id)
        
        # Calculate reset time based on the oldest request in the window
        if rate_limiter.requests.get(user_id):
            oldest_request = rate_limiter.requests[user_id][0]
            reset_time = oldest_request + settings.RATE_LIMIT_WINDOW_SECONDS - time.time()
            reset_seconds = max(1, math.ceil(reset_time))
        else:
            reset_seconds = settings.RATE_LIMIT_WINDOW_SECONDS
            
        headers = {
            "Retry-After": str(reset_seconds),
            "X-RateLimit-Limit": str(settings.RATE_LIMIT_REQUESTS),
            "X-RateLimit-Remaining": "0",
            "X-RateLimit-Reset": str(reset_seconds)
        }
        
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Try again in {reset_seconds} seconds.",
            headers=headers
        )
        
    # Valid request, update request count metric
    await increment_request_count(user_id)
    
    return user

require_auth = Depends(get_current_user)
