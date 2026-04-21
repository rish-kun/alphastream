import os
file = "backend/app/tests/test_auth.py"
with open(file, "r") as f:
    content = f.read()

content = content.replace('def _make_user(**overrides) -> User:', 'def _make_user(**overrides) -> User:\n    from app.models.user import User')

with open(file, "w") as f:
    f.write(content)
