from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.schemas.auth import UserRegister, UserOut, Token, RefreshTokenRequest
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register(schema: UserRegister, db: AsyncSession = Depends(get_db)):
    """Register a new user (default role: ENTREPRENEUR)."""
    return await AuthService.register_user(db, schema)


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """Log in using email (as username) and password to get JWT access and refresh tokens."""
    return await AuthService.authenticate_user(db, form_data.username, form_data.password)


@router.post("/refresh", response_model=Token)
async def refresh(schema: RefreshTokenRequest, db: AsyncSession = Depends(get_db)):
    """Refresh access token using a valid, non-revoked refresh token."""
    return await AuthService.refresh_tokens(db, schema.refresh_token)
