import httpx
from jose import JWTError, jwt

from app.core.config import settings
from app.security.vk_oidc import get_jwks_uri

_jwks_cache: dict | None = None


def _load_jwks() -> dict:
    global _jwks_cache
    if _jwks_cache is None:
        with httpx.Client(timeout=15.0) as client:
            response = client.get(get_jwks_uri())
            response.raise_for_status()
            _jwks_cache = response.json()
    return _jwks_cache


def _decode_token(token: str) -> dict:
    header = jwt.get_unverified_header(token)
    algorithms = [header.get("alg", "RS256")]
    jwks = _load_jwks()
    last_error: Exception | None = None
    for key in jwks.get("keys", []):
        try:
            return jwt.decode(
                token,
                key,
                algorithms=algorithms,
                audience=settings.vk_audience or None,
                options={"verify_aud": bool(settings.vk_audience)},
            )
        except JWTError as exc:
            last_error = exc
            continue
    if last_error:
        raise last_error
    raise JWTError("Unable to validate token")


def decode_vk_access_token(token: str) -> dict:
    return _decode_token(token)


def decode_vk_id_token(token: str) -> dict:
    return _decode_token(token)
