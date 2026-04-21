import os
file = "backend/app/tests/test_auth.py"
with open(file, "r") as f:
    content = f.read()

content = content.replace('from app.schemas.auth import TokenResponse', 'from app.schemas.auth import TokenResponse\n            pass')
content = content.replace('from app.schemas.auth import TokenResponse', 'pass')
content = content.replace('from app.schemas.user import UserResponse\n            from app.models.user import User', 'pass')
content = content.replace('import uuid\n            import datetime', 'pass')

content = content.replace('''            instance.create_tokens = AsyncMock(
                return_value=TokenResponse(
                    access_token="access-token",
                    refresh_token="refresh-token",
                    token_type="bearer",
                    user=UserResponse(id=uuid.uuid4(), email="new@example.com", full_name="New User", oauth_provider=None, is_active=True, created_at=datetime.datetime.now())
                )
            )''', '''            instance.create_tokens = AsyncMock(
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
            )''')

content = content.replace('''            instance.create_tokens = AsyncMock(
                return_value=TokenResponse(
                    access_token="access-token",
                    refresh_token="refresh-token",
                    token_type="bearer",
                    user=UserResponse(id=uuid.uuid4(), email=TEST_USER_EMAIL, full_name="New User", oauth_provider=None, is_active=True, created_at=datetime.datetime.now())
                )
            )''', '''            instance.create_tokens = AsyncMock(
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
            )''')

content = content.replace('''            instance.refresh_token = AsyncMock(
                return_value=TokenResponse(
                    access_token="new-access-token",
                    refresh_token="new-refresh-token",
                    token_type="bearer",
                    user=UserResponse(id=uuid.uuid4(), email=TEST_USER_EMAIL, full_name="New User", oauth_provider=None, is_active=True, created_at=datetime.datetime.now())
                )
            )''', '''            instance.refresh_token = AsyncMock(
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
            )''')

content = content.replace('def _make_user(**overrides) -> MagicMock:\n    """Create a dictionary of attributes for a mock User."""\n    defaults = {\n        "id": TEST_USER_ID,\n        "email": TEST_USER_EMAIL,\n        "hashed_password": hash_password("SecurePassword123!"),\n        "full_name": TEST_USER_NAME,\n        "oauth_provider": None,\n        "oauth_id": None,\n        "gemini_api_key": None,\n        "openrouter_api_key": None,\n        "is_active": True,\n        "created_at": datetime.now(UTC),\n        "updated_at": None,\n    }\n    defaults.update(overrides)\n    user = MagicMock(spec=User)\n    for k, v in defaults.items():\n        setattr(user, k, v)\n    return user', '''def _make_user(**overrides) -> MagicMock:
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
    return user''')

with open(file, "w") as f:
    f.write(content)
