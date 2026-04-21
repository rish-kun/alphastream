from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

from httpx import AsyncClient

from app.core.security import create_refresh_token, hash_password
from app.models.user import User
from app.tests.conftest import TEST_USER_EMAIL, TEST_USER_ID, TEST_USER_NAME, MockResult


def _make_user(**overrides) -> MagicMock:
    """Create a dictionary of attributes for a mock User."""
    import uuid
    defaults = {
        "id": uuid.uuid4(),
        "email": TEST_USER_EMAIL,
        "hashed_password": hash_password("SecurePassword123!"),
        "full_name": TEST_USER_NAME,
        "oauth_provider": "google",
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

        mock_db.execute.return_value = MockResult(scalar=None)
        mock_db.refresh.side_effect = lambda obj: None

        with patch("app.api.v1.auth.AuthService") as MockService:
            instance = MockService.return_value
            instance.create_user = AsyncMock(return_value=new_user)
            pass
            pass
            pass
            pass
            instance.create_tokens = AsyncMock(
                return_value=MagicMock(
                    access_token="access-token",
                    refresh_token="refresh-token",
                    token_type="bearer",
                    user=MagicMock(
                        id="123e4567-e89b-12d3-a456-426614174000",
                        email="new@example.com",
                        full_name="New User",
                        oauth_provider=None,
                        is_active=True,
                        created_at="2023-01-01T00:00:00Z"
                    )
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
        assert data["user"]["email"] == "new@example.com"

    async def test_register_duplicate_email(
        self, unauthed_client: AsyncClient, mock_db: AsyncMock
    ):
        from app.core.exceptions import ConflictError

        with patch("app.api.v1.auth.AuthService") as MockService:
            instance = MockService.return_value
            instance.create_user = AsyncMock(
                side_effect=ConflictError("Email already registered")
            )

            resp = await unauthed_client.post(
                "/api/v1/auth/register",
                json={
                    "email": TEST_USER_EMAIL,
                    "password": "SecurePassword123!",
                    "full_name": "Existing User",
                },
            )

        assert resp.status_code == 409
        assert "already registered" in resp.json()["detail"]

    async def test_register_weak_password(
        self, unauthed_client: AsyncClient, mock_db: AsyncMock
    ):
        resp = await unauthed_client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@example.com",
                "password": "weak",
                "full_name": "Test User",
            },
        )
        pass


class TestLogin:
    async def test_login_success(
        self, unauthed_client: AsyncClient, mock_db: AsyncMock
    ):


        user = _make_user()
        with patch("app.api.v1.auth.AuthService") as MockService:
            instance = MockService.return_value
            instance.authenticate_user = AsyncMock(return_value=user)
            pass
            pass
            pass
            pass
            instance.create_tokens = AsyncMock(
                return_value=MagicMock(
                    access_token="access-token",
                    refresh_token="refresh-token",
                    token_type="bearer",
                    user=MagicMock(
                        id="123e4567-e89b-12d3-a456-426614174000",
                        email=TEST_USER_EMAIL,
                        full_name="New User",
                        oauth_provider=None,
                        is_active=True,
                        created_at="2023-01-01T00:00:00Z"
                    )
                )
            )

            resp = await unauthed_client.post(
                "/api/v1/auth/login",
                json={"email": TEST_USER_EMAIL, "password": "SecurePassword123!"},
            )

        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["user"]["email"] == TEST_USER_EMAIL

    async def test_login_invalid_credentials(
        self, unauthed_client: AsyncClient, mock_db: AsyncMock
    ):
        from app.core.exceptions import UnauthorizedError

        with patch("app.api.v1.auth.AuthService") as MockService:
            instance = MockService.return_value
            instance.authenticate_user = AsyncMock(
                side_effect=UnauthorizedError("Incorrect email or password")
            )

            resp = await unauthed_client.post(
                "/api/v1/auth/login",
                json={"email": TEST_USER_EMAIL, "password": "wrongpassword"},
            )

        assert resp.status_code == 401


class TestRefresh:
    async def test_refresh_success(
        self, unauthed_client: AsyncClient, mock_db: AsyncMock
    ):
        refresh_token = create_refresh_token(data={"sub": str(TEST_USER_ID)})


        user = _make_user()
        with patch("app.api.v1.auth.AuthService") as MockService:
            instance = MockService.return_value
            pass
            pass
            pass
            pass
            instance.refresh_token = AsyncMock(
                return_value=MagicMock(
                    access_token="new-access-token",
                    refresh_token="new-refresh-token",
                    token_type="bearer",
                    user=MagicMock(
                        id="123e4567-e89b-12d3-a456-426614174000",
                        email=TEST_USER_EMAIL,
                        full_name="New User",
                        oauth_provider=None,
                        is_active=True,
                        created_at="2023-01-01T00:00:00Z"
                    )
                )
            )

            resp = await unauthed_client.post(
                "/api/v1/auth/refresh",
                json={"refresh_token": refresh_token},
            )

        assert resp.status_code == 200
        assert "access_token" in resp.json()

    async def test_refresh_invalid_token(
        self, unauthed_client: AsyncClient, mock_db: AsyncMock
    ):
        from app.core.exceptions import UnauthorizedError

        user = _make_user()
        with patch("app.api.v1.auth.AuthService") as MockService:
            instance = MockService.return_value
            instance.refresh_token = AsyncMock(
                side_effect=UnauthorizedError("Invalid refresh token")
            )

            resp = await unauthed_client.post(
                "/api/v1/auth/refresh",
                json={"refresh_token": "invalid-token"},
            )

        assert resp.status_code == 401


class TestGetMe:
    async def test_get_me_success(self, client: AsyncClient):
        # The client fixture already has a valid token and user
        resp = await client.get("/api/v1/auth/me")
        assert resp.status_code == 200
        data = resp.json()
        assert data["email"] == TEST_USER_EMAIL
        assert data["id"] == str(TEST_USER_ID)

    async def test_get_me_unauthenticated(self, unauthed_client: AsyncClient):
        resp = await unauthed_client.get("/api/v1/auth/me")
        assert resp.status_code == 401  # Missing Authorization header
