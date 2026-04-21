import os
file = "backend/app/tests/test_auth.py"
with open(file, "r") as f:
    content = f.read()

content = content.replace('def _make_user(**overrides) -> MagicMock:', 'def _make_user(**overrides) -> User:')

with open(file, "w") as f:
    f.write(content)
