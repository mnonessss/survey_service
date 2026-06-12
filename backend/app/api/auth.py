import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import RedirectResponse
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.redis import redis_client
from app.db.database import get_db
from app.models.user import User
from app.schemas.auth import AuthConfigResponse, TokenResponse
from app.schemas.user import UserResponse
from app.security.csrf import CSRF_COOKIE, generate_csrf_token, wrap_csrf_token
from app.security.dependencies import get_current_user, get_or_create_user_from_claims
from app.security.session_token import create_session_token
from app.security.vk_auth import decode_vk_access_token, decode_vk_id_token
from app.security.vk_oidc import (
    build_authorization_url,
    exchange_code_for_tokens,
    fetch_userinfo,
    generate_nonce,
    generate_state,
    get_oidc_metadata,
)

router = APIRouter(prefix="/auth", tags=["auth"])

OAUTH_STATE_TTL = 600


@router.get("/config", response_model=AuthConfigResponse)
async def auth_config():
    discovery_error = None
    authorization_url = ""
    try:
        if settings.vk_oauth_configured:
            get_oidc_metadata()
            authorization_url = build_authorization_url(
                state="preview",
                nonce=generate_nonce(),
            ).replace("state=preview", "state={state}")
    except (httpx.HTTPError, KeyError, ValueError) as exc:
        discovery_error = str(exc)

    return AuthConfigResponse(
        oauth_configured=settings.vk_oauth_configured,
        dev_auth_bypass=settings.DEV_AUTH_BYPASS and not settings.is_production,
        login_url=f"{settings.API_PUBLIC_URL.rstrip('/')}/auth/login",
        authorization_url=authorization_url,
        discovery_url=settings.vk_discovery_url,
        discovery_error=discovery_error,
    )


@router.get("/login/init")
async def login_init():
    if not settings.vk_oauth_configured:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="OAuth not configured")

    state = generate_state()
    nonce = generate_nonce()
    await redis_client.setex(f"oauth:state:{state}", OAUTH_STATE_TTL, nonce)

    return {
        "authorization_url": build_authorization_url(state=state, nonce=nonce),
        "state": state,
    }


@router.get("/login")
async def login_redirect():
    if not settings.vk_oauth_configured:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="OAuth not configured")

    state = generate_state()
    nonce = generate_nonce()
    await redis_client.setex(f"oauth:state:{state}", OAUTH_STATE_TTL, nonce)
    return RedirectResponse(build_authorization_url(state=state, nonce=nonce))


@router.get("/callback")
async def oauth_callback(
    code: str = Query(default=""),
    state: str = Query(default=""),
    error: str = Query(default=""),
    error_description: str = Query(default=""),
    db: AsyncSession = Depends(get_db),
):
    if error:
        redirect = f"{settings.VK_AUTH_FRONTEND_URL.rstrip('/')}/auth/callback?error={error}"
        if error_description:
            redirect += f"&error_description={error_description}"
        return RedirectResponse(redirect)

    if not code or not state:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing code or state")

    stored_nonce = await redis_client.get(f"oauth:state:{state}")
    if not stored_nonce:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired state")
    await redis_client.delete(f"oauth:state:{state}")

    try:
        tokens = await exchange_code_for_tokens(code)
        id_token = tokens.get("id_token")
        access_token = tokens.get("access_token")
        claims = decode_vk_id_token(id_token) if id_token else decode_vk_access_token(access_token)
        if claims.get("nonce") and claims.get("nonce") != stored_nonce:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid nonce")

        user = await get_or_create_user_from_claims(db, claims)
        session_token = create_session_token(str(user.id))
        frontend = settings.VK_AUTH_FRONTEND_URL.rstrip("/")
        return RedirectResponse(f"{frontend}/auth/callback?access_token={session_token}")
    except (JWTError, KeyError, httpx.HTTPError) as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"OAuth failed: {exc}") from exc


@router.post("/token", response_model=TokenResponse)
async def exchange_token(
    code: str,
    state: str,
    db: AsyncSession = Depends(get_db),
):
    stored_nonce = await redis_client.get(f"oauth:state:{state}")
    if not stored_nonce:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired state")
    await redis_client.delete(f"oauth:state:{state}")

    try:
        tokens = await exchange_code_for_tokens(code)
        access_token = tokens.get("access_token")
        if not access_token:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No access token")

        userinfo = await fetch_userinfo(access_token)
        user = await get_or_create_user_from_claims(db, userinfo)
        return TokenResponse(access_token=create_session_token(str(user.id)))
    except (JWTError, KeyError, httpx.HTTPError) as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"OAuth failed: {exc}") from exc


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)) -> User:
    return current_user


@router.get("/csrf")
async def issue_csrf():
    raw = generate_csrf_token()
    wrapped = wrap_csrf_token(raw)
    response = {"csrf_token": wrapped}
    from fastapi.responses import JSONResponse

    json_response = JSONResponse(content=response)
    json_response.set_cookie(
        CSRF_COOKIE,
        wrapped,
        httponly=True,
        samesite="none" if settings.is_production else "lax",
        secure=settings.is_production,
        max_age=60 * 60 * 12,
    )
    return json_response
