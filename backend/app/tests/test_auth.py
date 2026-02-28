"""Tests for auth API endpoints."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient

from app.core.security import create_access_token, create_refresh_token, hash_password
from app.models.user import User
from app.tests.conftest import TEST_USER_EMAIL, TEST_USER_ID, TEST_USER_NAME, MockResult


def _make_user(**overrides) -> MagicMock:
    """Create a mock User for testing."""
    defaults = {
        "id": TEST_USER_ID,
        "email": TEST_USER_EMAIL,
        "hashed_password": hash_password("SecurePassword123!"),
        "full_name": TEST_USER_NAME,
        "oauth_provider": None,
        "oauth_id": None,
        "gemini_api_key": None,
        "openrouter_api_key": None,
        "is_active": True,
        "created_at": datetime.now(UTC),
        "updated_at": None,
    }
    defaults.update(overrides)
    user = MagicMock(spec=User)
    for k, v in defaults.items():
        setattr(user, k, v)
    return user


class TestRegister:
    async def test_register_success(
        self, unauthed_client: AsyncClient, mock_db: AsyncMock
    ):
        new_user = _make_user(email="new@example.com")

        # First call: check existing user (returns None)
        # flush/refresh are handled by the mock
        mock_db.execute.return_value = MockResult(scalar=None)
        mock_db.refresh.side_effect = lambda obj: None

        # Patch AuthService.create_user to return our user
        with patch("app.api.v1.auth.AuthService") as MockService:
            instance = MockService.return_value
            instance.create_user = AsyncMock(return_value=new_user)
            instance.create_tokens = AsyncMock(
                return_value=MagicMock(
                    access_token="access-token",
                    refresh_token="refresh-token",
                    token_type="bearer",
                )
            )

            resp = await unauthed_client.post(
                "/api/v1/auth/register",
                json={
                    "email": "new@example.com",
                    "password": "SecurePassword123!",
                    "full_name": "New User",
                },
            )

        assert resp.status_code == 201
        data = resp.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    async def test_register_missing_email(self, unauthed_client: AsyncClient):
        resp = await unauthed_client.post(
            "/api/v1/auth/register",
            json={"password": "pass123", "full_name": "Test"},
        )
        assert resp.status_code == 422

    async def test_register_invalid_email(self, unauthed_client: AsyncClient):
        resp = await unauthed_client.post(
            "/api/v1/auth/register",
            json={
                "email": "not-an-email",
                "password": "pass123",
                "full_name": "Test",
            },
        )
        assert resp.status_code == 422

    async def test_register_missing_password(self, unauthed_client: AsyncClient):
        resp = await unauthed_client.post(
            "/api/v1/auth/register",
            json={"email": "test@example.com", "full_name": "Test"},
        )
        assert resp.status_code == 422


class TestLogin:
    async def test_login_success(
        self, unauthed_client: AsyncClient, mock_db: AsyncMock
    ):
        user = _make_user()

        with patch("app.api.v1.auth.AuthService") as MockService:
            instance = MockService.return_value
            instance.authenticate_user = AsyncMock(return_value=user)
            instance.create_tokens = AsyncMock(
                return_value=MagicMock(
                    access_token="access-token",
                    refresh_token="refresh-token",
                    token_type="bearer",
                )
            )

            resp = await unauthed_client.post(
                "/api/v1/auth/login",
                json={"email": TEST_USER_EMAIL, "password": "SecurePassword123!"},
            )

        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert "refresh_token" in data

    async def test_login_missing_fields(self, unauthed_client: AsyncClient):
        resp = await unauthed_client.post(
            "/api/v1/auth/login", json={"email": "test@example.com"}
        )
        assert resp.status_code == 422


class TestRefresh:
    async def test_refresh_success(
        self, unauthed_client: AsyncClient, mock_db: AsyncMock
    ):
        refresh_token = create_refresh_token(data={"sub": str(TEST_USER_ID)})

        with patch("app.api.v1.auth.AuthService") as MockService:
            instance = MockService.return_value
            instance.refresh_token = AsyncMock(
                return_value=MagicMock(
                    access_token="new-access-token",
                    refresh_token="new-refresh-token",
                    token_type="bearer",
                )
            )

            resp = await unauthed_client.post(
                "/api/v1/auth/refresh",
                json={"refresh_token": refresh_token},
            )

        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data

    async def test_refresh_missing_token(self, unauthed_client: AsyncClient):
        resp = await unauthed_client.post("/api/v1/auth/refresh", json={})
        assert resp.status_code == 422


class TestGetMe:
    async def test_get_me_authenticated(self, client: AsyncClient, auth_headers: dict):
        resp = await client.get("/api/v1/auth/me", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["email"] == TEST_USER_EMAIL
        assert data["full_name"] == TEST_USER_NAME
        assert data["is_active"] is True

    async def test_get_me_unauthenticated(self, unauthed_client: AsyncClient):
        resp = await unauthed_client.get("/api/v1/auth/me")
        assert resp.status_code == 422  # Missing Authorization header
