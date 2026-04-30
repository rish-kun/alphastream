import re

with open("backend/app/tests/test_auth.py", "r") as f:
    content = f.read()

content = content.replace(
    'return_value=MagicMock(',
    'return_value=TokenResponse('
)

content = content.replace(
    'def _make_user(**overrides) -> MagicMock:',
    'def _make_user(**overrides) -> UserResponse:'
)

user_mock = """def _make_user(**overrides) -> UserResponse:
    \"\"\"Create a mock User for testing.\"\"\"
    defaults = {
        "id": TEST_USER_ID,
        "email": TEST_USER_EMAIL,
        "full_name": TEST_USER_NAME,
        "oauth_provider": None,
        "is_active": True,
        "created_at": datetime.now(UTC),
    }
    defaults.update(overrides)
    return UserResponse(**defaults)"""

content = re.sub(
    r'def _make_user\(\*\*overrides\) -> .*?:.*?(?=\n\n\nclass)',
    user_mock,
    content,
    flags=re.DOTALL | re.MULTILINE
)

# Fix TokenResponse instantiation
content = content.replace(
    'TokenResponse(\n                    access_token="access-token",\n                    refresh_token="refresh-token",\n                    token_type="bearer",\n                )',
    'TokenResponse(\n                    access_token="access-token",\n                    refresh_token="refresh-token",\n                    token_type="bearer",\n                    user=_make_user(),\n                )'
)

content = content.replace(
    'TokenResponse(\n                    access_token="new-access-token",\n                    refresh_token="new-refresh-token",\n                    token_type="bearer",\n                )',
    'TokenResponse(\n                    access_token="new-access-token",\n                    refresh_token="new-refresh-token",\n                    token_type="bearer",\n                    user=_make_user(),\n                )'
)

content = content.replace(
    'assert resp.status_code == 422  # Missing Authorization header',
    'assert resp.status_code == 401  # Missing Authorization header'
)

# need to import TokenResponse and UserResponse
if 'from app.schemas.user import' not in content:
    content = content.replace(
        'from app.models.user import User',
        'from app.models.user import User\nfrom app.schemas.user import TokenResponse, UserResponse'
    )

with open("backend/app/tests/test_auth.py", "w") as f:
    f.write(content)
