from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt

from app.core.config import settings

ALGORITHM = "HS256"
SESSION_TTL = timedelta(hours=12)


def _secret() -> str:
    secret = settings.APP_SECRET or settings.CSRF_SECRET
    if not secret:
        raise RuntimeError("APP_SECRET or CSRF_SECRET must be set")
    return secret


def create_session_token(user_id: str) -> str:
    payload = {
        "sub": str(user_id),
        "exp": datetime.now(timezone.utc) + SESSION_TTL,
    }
    return jwt.encode(payload, _secret(), algorithm=ALGORITHM)


def decode_session_token(token: str) -> str:
    payload = jwt.decode(token, _secret(), algorithms=[ALGORITHM])
    sub = payload.get("sub")
    if not sub:
        raise JWTError("Missing sub")
    return str(sub)
