import uuid
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.logging import logger
from app.core import security
from app.models.auth import User, RefreshToken, UserRole
from app.schemas.auth import UserRegister, Token, TokenData

# OAuth2 scheme config
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


class AuthService:
    @staticmethod
    async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
        """Fetch user from database by email."""
        result = await db.execute(select(User).where(User.email == email))
        return result.scalars().first()

    @staticmethod
    async def get_user_by_id(db: AsyncSession, user_id: uuid.UUID) -> Optional[User]:
        """Fetch user from database by ID."""
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalars().first()

    @classmethod
    async def register_user(cls, db: AsyncSession, schema: UserRegister) -> User:
        """Register a new user in the system."""
        existing_user = await cls.get_user_by_email(db, schema.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email is already registered"
            )

        hashed_password = security.get_password_hash(schema.password)
        new_user = User(
            email=schema.email,
            hashed_password=hashed_password,
            role=schema.role
        )
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
        logger.info(f"Successfully registered user: {new_user.email} with role {new_user.role.value}")
        return new_user

    @classmethod
    async def authenticate_user(cls, db: AsyncSession, email: str, password: str) -> Token:
        """Authenticate user credentials and generate tokens."""
        user = await cls.get_user_by_email(db, email)
        if not user or not security.verify_password(password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is deactivated"
            )

        # Generate tokens
        access_token = security.create_access_token(user.id, user.role)
        refresh_token_str = security.create_refresh_token(user.id)

        # Store refresh token in DB
        decoded_refresh = security.decode_token(refresh_token_str)
        expires_at = datetime.fromtimestamp(decoded_refresh["exp"], tz=timezone.utc).replace(tzinfo=None)

        db_refresh_token = RefreshToken(
            user_id=user.id,
            token=refresh_token_str,
            expires_at=expires_at
        )
        db.add(db_refresh_token)
        await db.commit()

        logger.info(f"User {user.email} logged in successfully.")
        return Token(
            access_token=access_token,
            refresh_token=refresh_token_str,
            role=user.role
        )

    @classmethod
    async def refresh_tokens(cls, db: AsyncSession, refresh_token_str: str) -> Token:
        """Verify refresh token and issue a new token pair."""
        # Decode and verify refresh token payload
        payload = security.decode_token(refresh_token_str)
        if not payload or payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )

        user_id = uuid.UUID(payload.get("sub"))
        
        # Look up in DB to ensure it isn't revoked
        result = await db.execute(
            select(RefreshToken)
            .where(RefreshToken.token == refresh_token_str)
            .where(RefreshToken.is_revoked == False)
        )
        db_token = result.scalars().first()
        
        if not db_token or db_token.expires_at < datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Expired or revoked refresh token"
            )

        # Load user
        user = await cls.get_user_by_id(db, user_id)
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )

        # Revoke the old refresh token
        db_token.is_revoked = True
        
        # Issue new token pair
        access_token = security.create_access_token(user.id, user.role)
        new_refresh_token_str = security.create_refresh_token(user.id)

        # Save new refresh token
        decoded_refresh = security.decode_token(new_refresh_token_str)
        expires_at = datetime.fromtimestamp(decoded_refresh["exp"], tz=timezone.utc).replace(tzinfo=None)

        new_db_token = RefreshToken(
            user_id=user.id,
            token=new_refresh_token_str,
            expires_at=expires_at
        )
        db.add(new_db_token)
        await db.commit()

        logger.info(f"Successfully refreshed tokens for user ID: {user.id}")
        return Token(
            access_token=access_token,
            refresh_token=new_refresh_token_str,
            role=user.role
        )


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Dependency to retrieve the currently logged in user."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    payload = security.decode_token(token)
    if payload is None or payload.get("type") != "access":
        raise credentials_exception
        
    user_id_str = payload.get("sub")
    if user_id_str is None:
        raise credentials_exception
        
    try:
        user_id = uuid.UUID(user_id_str)
    except ValueError:
        raise credentials_exception

    user = await AuthService.get_user_by_id(db, user_id)
    if user is None:
        raise credentials_exception
        
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
        
    return user


class RoleChecker:
    """RBAC Dependency class to restrict endpoint access to specific roles."""
    def __init__(self, allowed_roles: List[UserRole]):
        self.allowed_roles = allowed_roles

    def __call__(self, current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this resource"
            )
        return current_user
