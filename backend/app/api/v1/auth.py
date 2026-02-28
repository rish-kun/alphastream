from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.requests import Request
from starlette.responses import RedirectResponse

from app.api.deps import get_current_user
from app.core.oauth import oauth
from app.database import get_db
from app.models.user import User
from app.schemas.user import (
    TokenRefresh,
    TokenResponse,
    UserCreate,
    UserLogin,
    UserResponse,
)
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(
    user_data: UserCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TokenResponse:
    service = AuthService(db)
    user = await service.create_user(user_data)
    return await service.create_tokens(user)


@router.post("/login", response_model=TokenResponse)
async def login(
    user_data: UserLogin,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TokenResponse:
    service = AuthService(db)
    user = await service.authenticate_user(user_data.email, user_data.password)
    return await service.create_tokens(user)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    data: TokenRefresh,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TokenResponse:
    service = AuthService(db)
    return await service.refresh_token(data.refresh_token)


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    return current_user


@router.get("/google")
async def google_redirect(request: Request) -> RedirectResponse:
    redirect_uri = request.url_for("google_callback")
    return await oauth.google.authorize_redirect(request, str(redirect_uri))


@router.get("/google/callback")
async def google_callback(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> RedirectResponse:
    token = await oauth.google.authorize_access_token(request)
    userinfo = token.get("userinfo")

    email = userinfo["email"]
    full_name = userinfo.get("name", "")
    oauth_id = userinfo.get("sub", "")

    service = AuthService(db)
    user = await service.get_or_create_oauth_user(
        email=email, full_name=full_name, provider="google", oauth_id=oauth_id
    )
    tokens = await service.create_tokens(user)

    return RedirectResponse(
        url=f"http://localhost:3000/auth/callback?access_token={tokens.access_token}&refresh_token={tokens.refresh_token}"
    )


@router.get("/github")
async def github_redirect(request: Request) -> RedirectResponse:
    redirect_uri = request.url_for("github_callback")
    return await oauth.github.authorize_redirect(request, str(redirect_uri))


@router.get("/github/callback")
async def github_callback(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> RedirectResponse:
    token = await oauth.github.authorize_access_token(request)
    resp = await oauth.github.get("user", token=token)
    user_info = resp.json()

    email = user_info.get("email", "")
    full_name = user_info.get("name", "") or user_info.get("login", "")
    oauth_id = str(user_info.get("id", ""))

    service = AuthService(db)
    user = await service.get_or_create_oauth_user(
        email=email, full_name=full_name, provider="github", oauth_id=oauth_id
    )
    tokens = await service.create_tokens(user)

    return RedirectResponse(
        url=f"http://localhost:3000/auth/callback?access_token={tokens.access_token}&refresh_token={tokens.refresh_token}"
    )
