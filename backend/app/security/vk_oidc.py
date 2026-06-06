import secrets
from functools import lru_cache
from urllib.parse import urlencode

import httpx

from app.core.config import settings

_DISCOVERY_TIMEOUT_SECONDS = 10.0


@lru_cache(maxsize=1)
def get_oidc_metadata() -> dict:
    with httpx.Client(timeout=_DISCOVERY_TIMEOUT_SECONDS) as client:
        response = client.get(settings.vk_discovery_url)
        response.raise_for_status()
        return response.json()


def get_authorization_endpoint() -> str:
    return get_oidc_metadata()["authorization_endpoint"]


def get_token_endpoint() -> str:
    return get_oidc_metadata()["token_endpoint"]


def get_userinfo_endpoint() -> str:
    return get_oidc_metadata()["userinfo_endpoint"]


def get_jwks_uri() -> str:
    if settings.VK_AUTH_JWKS_URL:
        return settings.VK_AUTH_JWKS_URL
    return get_oidc_metadata()["jwks_uri"]


def build_authorization_url(*, state: str, nonce: str) -> str:
    params = urlencode(
        {
            "response_type": "code",
            "client_id": settings.VK_AUTH_CLIENT_ID,
            "redirect_uri": settings.VK_AUTH_REDIRECT_URI,
            "scope": settings.VK_AUTH_SCOPES,
            "state": state,
            "nonce": nonce,
        }
    )
    return f"{get_authorization_endpoint()}?{params}"


async def exchange_code_for_tokens(code: str) -> dict:
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.post(
            get_token_endpoint(),
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": settings.VK_AUTH_REDIRECT_URI,
                "client_id": settings.VK_AUTH_CLIENT_ID,
                "client_secret": settings.VK_AUTH_CLIENT_SECRET,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        response.raise_for_status()
        return response.json()


async def fetch_userinfo(access_token: str) -> dict:
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.get(
            get_userinfo_endpoint(),
            headers={"Authorization": f"Bearer {access_token}"},
        )
        response.raise_for_status()
        return response.json()


def generate_state() -> str:
    return secrets.token_urlsafe(32)


def generate_nonce() -> str:
    return secrets.token_urlsafe(32)
