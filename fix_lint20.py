import os
file = "backend/app/tests/test_auth.py"
with open(file, "r") as f:
    content = f.read()

content = content.replace('from app.schemas.auth import TokenResponse', 'from app.schemas.token import TokenResponse')
content = content.replace('from app.schemas.user import UserResponse', 'from app.schemas.user import UserResponse, User')

with open(file, "w") as f:
    f.write(content)
