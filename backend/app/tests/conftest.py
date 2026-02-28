"""Shared test fixtures for the AlphaStream backend test suite.

Uses dependency overrides to mock the database and auth layers,
avoiding the need for a running PostgreSQL instance.
"""

from __future__ import annotations

import asyncio
import uuid
from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.core.security import create_access_token, hash_password
from app.database import get_db
from app.main import app
from app.models.user import User


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# ---------------------------------------------------------------------------
# Test user & auth helpers
# ---------------------------------------------------------------------------

TEST_USER_ID = uuid.UUID("00000000-0000-4000-8000-000000000001")
TEST_USER_EMAIL = "test@example.com"
TEST_USER_PASSWORD = "SecurePassword123!"
TEST_USER_NAME = "Test User"


def _make_test_user(**overrides) -> MagicMock:
    """Create a mock User for testing (avoids SQLAlchemy instrumentation issues)."""
    defaults = {
        "id": TEST_USER_ID,
        "email": TEST_USER_EMAIL,
        "hashed_password": hash_password(TEST_USER_PASSWORD),
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


@pytest.fixture
def test_user() -> MagicMock:
    return _make_test_user()


@pytest.fixture
def test_user_token() -> str:
    """A valid JWT access token for the test user."""
    return create_access_token(data={"sub": str(TEST_USER_ID)})


@pytest.fixture
def auth_headers(test_user_token: str) -> dict[str, str]:
    """Authorization headers with a valid Bearer token."""
    return {"Authorization": f"Bearer {test_user_token}"}


# ---------------------------------------------------------------------------
# Mock database session
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_db() -> AsyncMock:
    """A mock async SQLAlchemy session."""
    db = AsyncMock()
    db.execute = AsyncMock()
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    db.flush = AsyncMock()
    db.refresh = AsyncMock()
    db.add = MagicMock()
    db.delete = AsyncMock()
    return db


# ---------------------------------------------------------------------------
# FastAPI test client with dependency overrides
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def client(
    mock_db: AsyncMock, test_user: MagicMock
) -> AsyncGenerator[AsyncClient, None]:
    """Async HTTP test client with mocked DB and auth dependencies."""

    async def override_get_db():
        yield mock_db

    async def override_get_current_user():
        return test_user

    app.dependency_overrides[get_db] = override_get_db

    # Override auth dependency for all protected routes
    from app.api.deps import get_current_user

    app.dependency_overrides[get_current_user] = override_get_current_user

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def unauthed_client(mock_db: AsyncMock) -> AsyncGenerator[AsyncClient, None]:
    """Async HTTP test client with mocked DB but NO auth override.

    Use this for testing unauthenticated / login / register flows.
    """

    async def override_get_db():
        yield mock_db

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Helpers for mock DB result objects
# ---------------------------------------------------------------------------


class MockResult:
    """A simple mock for SQLAlchemy execute() results."""

    def __init__(self, data=None, scalar=None):
        self._data = data or []
        self._scalar = scalar

    def scalars(self):
        return self

    def all(self):
        return self._data

    def unique(self):
        return self

    def scalar_one_or_none(self):
        return self._scalar

    def scalar_one(self):
        if self._scalar is None:
            return 0
        return self._scalar


@pytest.fixture
def mock_result():
    """Factory fixture for creating MockResult instances."""
    return MockResult
