import jwt
from config import settings
from datetime import datetime, timedelta, timezone

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 30

def create_access_token(username: str) -> str:
    data = {
        "sub": username,
        "exp": datetime.now(timezone.utc) + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    }
    return jwt.encode(data, settings.SECRET_KEY, algorithm=ALGORITHM)

def decode_access_token(token: str) -> str | None:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub")
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None