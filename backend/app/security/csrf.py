import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from starlette.requests import Request

from app.core.config import settings

CSRF_COOKIE = "csrf_token"
CSRF_HEADER = "X-CSRF-Token"
CSRF_MAX_AGE = 60 * 60 * 12


def _sign(value: str) -> str:
    return hmac.new(
        settings.CSRF_SECRET.encode("utf-8"),
        value.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def generate_csrf_token() -> str:
    return secrets.token_urlsafe(32)


def wrap_csrf_token(raw: str) -> str:
    expires = int((datetime.now(timezone.utc) + timedelta(seconds=CSRF_MAX_AGE)).timestamp())
    payload = f"{raw}.{expires}"
    return f"{payload}.{_sign(payload)}"


def unwrap_csrf_token(wrapped: str) -> str | None:
    parts = wrapped.split(".")
    if len(parts) != 3:
        return None
    raw, expires_str, sig = parts
    payload = f"{raw}.{expires_str}"
    if not hmac.compare_digest(_sign(payload), sig):
        return None
    try:
        expires = int(expires_str)
    except ValueError:
        return None
    if datetime.now(timezone.utc).timestamp() > expires:
        return None
    return raw


def validate_csrf(request: Request) -> None:
    if request.method in {"GET", "HEAD", "OPTIONS"}:
        return

    path = request.url.path
    exempt_prefixes = (
        "/public/",
        "/api/v1/external/",
        "/auth/",
        "/docs",
        "/redoc",
        "/health",
        "/openapi.json",
    )
    if any(path.startswith(p) for p in exempt_prefixes):
        return

    cookie = request.cookies.get(CSRF_COOKIE)
    header = request.headers.get(CSRF_HEADER)
    if not cookie or not header:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="CSRF token missing")

    cookie_raw = unwrap_csrf_token(cookie)
    header_raw = unwrap_csrf_token(header)
    if not cookie_raw or not header_raw or not hmac.compare_digest(cookie_raw, header_raw):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid CSRF token")
