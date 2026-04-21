import os
file = "backend/app/tests/test_auth.py"
with open(file, "r") as f:
    content = f.read()

content = content.replace('user = MagicMock(spec=User)', 'user = User()')
content = content.replace('assert resp.status_code == 422  # Missing Authorization header', 'assert resp.status_code == 401  # Missing Authorization header')

with open(file, "w") as f:
    f.write(content)
