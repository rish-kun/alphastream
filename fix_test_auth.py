import re

with open("backend/app/tests/test_auth.py", "r") as f:
    content = f.read()

# Replace _make_user return type and instantiation
content = content.replace("def _make_user(**overrides) -> MagicMock:", "def _make_user(**overrides) -> User:")
content = re.sub(r'user = MagicMock\(spec=User\)\n\s+for key, value in defaults\.items\(\):\n\s+setattr\(user, key, value\)\n\s+return user', r'return User(**defaults)', content)

# Replace MagicMock(access_token... with User returning Tokens
content = re.sub(
    r'instance\.create_tokens = AsyncMock\(\n\s*return_value=MagicMock\(\n\s*access_token="([^"]+)",\n\s*refresh_token="([^"]+)",\n\s*token_type="([^"]+)",\n\s*\)\n\s*\)',
    r'''class Tokens:
                access_token="\1"
                refresh_token="\2"
                token_type="\3"
                user=new_user
            instance.create_tokens = AsyncMock(return_value=Tokens())''',
    content
)

content = content.replace("assert resp.status_code == 422  # Missing Authorization header", "assert resp.status_code == 401  # Missing Authorization header")

with open("backend/app/tests/test_auth.py", "w") as f:
    f.write(content)
