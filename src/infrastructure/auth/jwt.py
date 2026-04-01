from jose import jwt, JWTError
from datetime import datetime, timedelta, timezone
from uuid import UUID
from src.config.settings import settings

# Фиксированные UUID для dummyLogin (одинаковые при каждом вызове)
DUMMY_ADMIN_UUID = "00000000-0000-0000-0000-000000000001"
DUMMY_USER_UUID = "00000000-0000-0000-0000-000000000002"

def create_token(user_id: str, role: str)->str:
    payload={
        "user_id": user_id,
        "role": role,
        "exp": datetime.now(timezone.utc)+timedelta(hours=24)
    }

    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

def decoe_token(token: str)->dict:
    try:
        payload = jwt.decode(token=token, key=settings.JWT_SECRET_KEY, algorithms=settings.JWT_ALGORITHM)
        return payload
    
    except JWTError:
        raise ValueError("Invalid token")