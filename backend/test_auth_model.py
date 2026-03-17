import sys
import uuid
import datetime
from unittest.mock import MagicMock
sys.path.append('.')
from app.schemas.user import UserResponse, TokenResponse
from app.models.user import User

user_id = uuid.uuid4()

def _make_user(**overrides) -> MagicMock:
    """Create a mock User for testing."""
    defaults = {
        "id": user_id,
        "email": "test@test.com",
        "full_name": "test",
        "oauth_provider": None,
        "is_active": True,
        "created_at": datetime.datetime.now(),
    }
    defaults.update(overrides)
    user = MagicMock(spec=User)
    for k, v in defaults.items():
        setattr(user, k, v)
    return user

mock_user = _make_user()

mock_token = TokenResponse(
    access_token="access",
    refresh_token="refresh",
    token_type="bearer",
    user=UserResponse.model_validate(mock_user)
)

try:
    print(TokenResponse.model_validate(mock_token))
except Exception as e:
    print(e)
