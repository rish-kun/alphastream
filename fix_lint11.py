import os
file = "backend/app/tests/test_auth.py"
with open(file, "r") as f:
    content = f.read()

content = content.replace('for k, v in defaults.items():\n        setattr(user, k, v)\n    return user', 'for k, v in defaults.items():\n        setattr(user, k, v)\n    \n    # ensure these are concrete for serialization\n    user.id = defaults["id"]\n    user.email = defaults["email"]\n    user.full_name = defaults["full_name"]\n    user.oauth_provider = defaults["oauth_provider"]\n    \n    return user')

with open(file, "w") as f:
    f.write(content)
