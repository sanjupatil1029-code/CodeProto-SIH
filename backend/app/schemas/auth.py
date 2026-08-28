import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field
from app.models.auth import UserRole


class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=50)
    full_name: Optional[str] = None
    role: UserRole = UserRole.ENTREPRENEUR


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: uuid.UUID
    email: EmailStr
    full_name: Optional[str] = None
    role: UserRole
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    role: UserRole
    full_name: Optional[str] = None


class TokenData(BaseModel):
    user_id: uuid.UUID
    role: UserRole


class RefreshTokenRequest(BaseModel):
    refresh_token: str
