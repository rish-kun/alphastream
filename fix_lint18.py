import os
file = "backend/app/tests/test_auth.py"
with open(file, "r") as f:
    content = f.read()

content = content.replace('''
        with patch("app.api.v1.auth.AuthService") as MockService:
            instance = MockService.return_value
            instance.authenticate_user = AsyncMock(return_value=user)
''', '''
        user = _make_user()
        with patch("app.api.v1.auth.AuthService") as MockService:
            instance = MockService.return_value
            instance.authenticate_user = AsyncMock(return_value=user)
''')
content = content.replace('''
        with patch("app.api.v1.auth.AuthService") as MockService:
            instance = MockService.return_value
            instance.refresh_token = AsyncMock(
''', '''
        user = _make_user()
        with patch("app.api.v1.auth.AuthService") as MockService:
            instance = MockService.return_value
            instance.refresh_token = AsyncMock(
''')

with open(file, "w") as f:
    f.write(content)
