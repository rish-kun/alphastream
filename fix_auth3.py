import re

with open("backend/app/tests/test_auth.py", "r") as f:
    content = f.read()

# Replace _make_user return type and instantiation
content = content.replace("def _make_user(**overrides) -> MagicMock:", "def _make_user(**overrides) -> User:")
content = re.sub(r'user = MagicMock\(spec=User\)\n\s+for key, value in defaults\.items\(\):\n\s+setattr\(user, key, value\)\n\s+return user', r'return User(**defaults)', content)

# 1. Register Tokens
content = re.sub(
    r'instance\.create_tokens = AsyncMock\(\n\s*return_value=MagicMock\(\n\s*access_token="access-token",\n\s*refresh_token="refresh-token",\n\s*token_type="bearer",\n\s*\)\n\s*\)',
    r'''class Tokens1:
                access_token="access-token"
                refresh_token="refresh-token"
                token_type="bearer"
                user=new_user
            instance.create_tokens = AsyncMock(return_value=Tokens1())''',
    content
)

# 2. Login Tokens
content = re.sub(
    r'instance\.create_tokens = AsyncMock\(\n\s*return_value=MagicMock\(\n\s*access_token="new-access-token",\n\s*refresh_token="new-refresh-token",\n\s*token_type="bearer",\n\s*\)\n\s*\)',
    r'''class Tokens2:
                access_token="new-access-token"
                refresh_token="new-refresh-token"
                token_type="bearer"
                user=user
            instance.create_tokens = AsyncMock(return_value=Tokens2())''',
    content
)

# 3. Refresh Tokens
content = re.sub(
    r'instance\.refresh_token = AsyncMock\(\n\s*return_value=MagicMock\(\n\s*access_token="new-access-token",\n\s*refresh_token="new-refresh-token",\n\s*token_type="bearer",\n\s*\)\n\s*\)',
    r'''class Tokens3:
                access_token="new-access-token"
                refresh_token="new-refresh-token"
                token_type="bearer"
                user=user
            instance.refresh_token = AsyncMock(return_value=Tokens3())''',
    content
)

content = content.replace("assert resp.status_code == 422  # Missing Authorization header", "assert resp.status_code == 401  # Missing Authorization header")

with open("backend/app/tests/test_auth.py", "w") as f:
    f.write(content)
