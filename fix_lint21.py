import os
file = "backend/app/tests/test_auth.py"
with open(file, "r") as f:
    content = f.read()

content = content.replace('from app.schemas.token import TokenResponse', 'from app.schemas.auth import TokenResponse')
content = content.replace('from app.schemas.user import UserResponse, User', 'from app.schemas.user import UserResponse\n            from app.models.user import User')

with open(file, "w") as f:
    f.write(content)
