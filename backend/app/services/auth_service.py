from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError, UnauthorizedError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
    verify_token,
)
from app.models.user import User
from app.schemas.user import TokenResponse, UserCreate


class AuthService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_user(self, user_data: UserCreate) -> User:
        """Register a new user with email and password."""
        result = await self.db.execute(
            select(User).where(User.email == user_data.email)
        )
        existing = result.scalar_one_or_none()
        if existing is not None:
            raise ConflictError("A user with this email already exists")

        user = User(
            email=user_data.email,
            hashed_password=hash_password(user_data.password),
            full_name=user_data.full_name,
        )
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)
        return user

    async def authenticate_user(self, email: str, password: str) -> User:
        """Authenticate user with email and password."""
        result = await self.db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()

        if user is None or user.hashed_password is None:
            raise UnauthorizedError("Invalid email or password")

        if not verify_password(password, user.hashed_password):
            raise UnauthorizedError("Invalid email or password")

        if not user.is_active:
            raise UnauthorizedError("Account is deactivated")

        return user

    async def create_tokens(self, user: User) -> TokenResponse:
        """Create access and refresh tokens for a user."""
        access_token = create_access_token(data={"sub": str(user.id)})
        refresh = create_refresh_token(data={"sub": str(user.id)})
        return TokenResponse(access_token=access_token, refresh_token=refresh)

    async def refresh_token(self, refresh_token: str) -> TokenResponse:
        """Refresh an access token using a refresh token."""
        try:
            payload = verify_token(refresh_token)
        except ValueError as e:
            raise UnauthorizedError(str(e))

        if payload.get("type") != "refresh":
            raise UnauthorizedError("Invalid token type")

        user_id = payload.get("sub")
        if not user_id:
            raise UnauthorizedError("Invalid token payload")

        user = await self.get_user_by_id(uuid.UUID(user_id))
        if user is None:
            raise NotFoundError("User", user_id)

        if not user.is_active:
            raise UnauthorizedError("Account is deactivated")

        return await self.create_tokens(user)

    async def get_user_by_id(self, user_id: uuid.UUID) -> User | None:
        """Fetch a user by their ID."""
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_or_create_oauth_user(
        self, email: str, full_name: str, provider: str, oauth_id: str
    ) -> User:
        """Get an existing user by email or create a new OAuth user."""
        result = await self.db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()

        if user is not None:
            if user.oauth_provider is None:
                user.oauth_provider = provider
                user.oauth_id = oauth_id
                await self.db.flush()
                await self.db.refresh(user)
            return user

        user = User(
            email=email,
            full_name=full_name,
            oauth_provider=provider,
            oauth_id=oauth_id,
            hashed_password=None,
        )
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)
        return user
