from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from models.auth_model import UserCreate, UserResponse, TokenResponse, UserDocument
from services.auth_service import register_user, authenticate_user, create_access_token
from utils.dependencies import get_current_user

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

@router.post("/register", response_model=UserResponse)
async def register(user_data: UserCreate):
    """Register a new user account."""
    return await register_user(user_data.username, user_data.password)

@router.post("/login", response_model=TokenResponse)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Authenticate and get a JWT token."""
    user = await authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"username": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: UserDocument = Depends(get_current_user)):
    """Get metadata about the currently authenticated user."""
    return UserResponse(
        id=str(current_user.id),
        username=current_user.username,
        is_admin=current_user.is_admin,
        created_at=current_user.created_at
    )
