import re

with open("backend/app/tests/test_auth.py", "r") as f:
    content = f.read()

# Fix TestLogin
content = content.replace('user=new_user\n            instance.create_tokens = AsyncMock(return_value=Tokens())', 'user=user\n            instance.create_tokens = AsyncMock(return_value=Tokens())')

# Fix TestRefresh
content = re.sub(
    r'instance\.refresh_token = AsyncMock\(\n\s*return_value=MagicMock\(\n\s*access_token="new-access-token",\n\s*refresh_token="new-refresh-token",\n\s*token_type="bearer",\n\s*\)\n\s*\)',
    r'''class Tokens:
                access_token="new-access-token"
                refresh_token="new-refresh-token"
                token_type="bearer"
                user=user
            instance.refresh_token = AsyncMock(return_value=Tokens())''',
    content
)

with open("backend/app/tests/test_auth.py", "w") as f:
    f.write(content)
