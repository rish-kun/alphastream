import os
file = "backend/app/tests/test_auth.py"
with open(file, "r") as f:
    content = f.read()

content = content.replace('user = User()', 'user = MagicMock(spec=User)')
content = content.replace('def _make_user(**overrides) -> User:', 'def _make_user(**overrides) -> MagicMock:')
content = content.replace('''    # ensure these are concrete for serialization
    user.id = defaults["id"]
    user.email = defaults["email"]
    user.full_name = defaults["full_name"]
    user.oauth_provider = defaults["oauth_provider"]
''', '')

content = content.replace('''        with patch("app.api.v1.auth.AuthService") as MockService:
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
''', '''        with patch("app.api.v1.auth.AuthService") as MockService:
            instance = MockService.return_value
            instance.create_user = AsyncMock(return_value=new_user)
            from app.schemas.auth import TokenResponse
            from app.schemas.user import UserResponse
            import uuid
            import datetime
            instance.create_tokens = AsyncMock(
                return_value=TokenResponse(
                    access_token="access-token",
                    refresh_token="refresh-token",
                    token_type="bearer",
                    user=UserResponse(id=uuid.uuid4(), email="new@example.com", full_name="New User", oauth_provider=None, is_active=True, created_at=datetime.datetime.now())
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
''')

content = content.replace('''        with patch("app.api.v1.auth.AuthService") as MockService:
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
''', '''        with patch("app.api.v1.auth.AuthService") as MockService:
            instance = MockService.return_value
            instance.authenticate_user = AsyncMock(return_value=user)
            from app.schemas.auth import TokenResponse
            from app.schemas.user import UserResponse
            import uuid
            import datetime
            instance.create_tokens = AsyncMock(
                return_value=TokenResponse(
                    access_token="access-token",
                    refresh_token="refresh-token",
                    token_type="bearer",
                    user=UserResponse(id=uuid.uuid4(), email=TEST_USER_EMAIL, full_name="New User", oauth_provider=None, is_active=True, created_at=datetime.datetime.now())
                )
            )

            resp = await unauthed_client.post(
                "/api/v1/auth/login",
                json={"email": TEST_USER_EMAIL, "password": "SecurePassword123!"},
            )
''')

content = content.replace('''        with patch("app.api.v1.auth.AuthService") as MockService:
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
''', '''        with patch("app.api.v1.auth.AuthService") as MockService:
            instance = MockService.return_value
            from app.schemas.auth import TokenResponse
            from app.schemas.user import UserResponse
            import uuid
            import datetime
            instance.refresh_token = AsyncMock(
                return_value=TokenResponse(
                    access_token="new-access-token",
                    refresh_token="new-refresh-token",
                    token_type="bearer",
                    user=UserResponse(id=uuid.uuid4(), email=TEST_USER_EMAIL, full_name="New User", oauth_provider=None, is_active=True, created_at=datetime.datetime.now())
                )
            )

            resp = await unauthed_client.post(
                "/api/v1/auth/refresh",
                json={"refresh_token": refresh_token},
            )
''')

content = content.replace('def _make_user(**overrides) -> dict:', 'def _make_user(**overrides) -> MagicMock:')

with open(file, "w") as f:
    f.write(content)
