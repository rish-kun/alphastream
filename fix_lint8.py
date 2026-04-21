import os
file = "backend/app/tests/test_auth.py"
with open(file, "r") as f:
    content = f.read()

content = content.replace('user = MagicMock(spec=User)', 'user = User()')

with open(file, "w") as f:
    f.write(content)
