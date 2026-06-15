import httpx
import uuid
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.database import get_db
from app.models.enums import UserRole
from app.models.user import User
from app.security.session_token import decode_session_token
from app.security.vk_auth import decode_vk_access_token

security = HTTPBearer(auto_error=False)


async def _get_dev_user(db: AsyncSession) -> User:
    result = await db.execute(
        select(User).where(User.external_id == settings.DEV_USER_EXTERNAL_ID)
    )
    user = result.scalar_one_or_none()
    if user:
        return user
    user = User(
        external_id=settings.DEV_USER_EXTERNAL_ID,
        email=settings.DEV_USER_EMAIL,
        role=UserRole.RESEARCHER,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def get_or_create_user_by_external_id(
    db: AsyncSession,
    *,
    external_id: str,
    email: str,
) -> User:
    result = await db.execute(select(User).where(User.external_id == external_id))
    user = result.scalar_one_or_none()
    if user:
        if not user.is_active:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User is inactive")
        return user
    user = User(external_id=external_id, email=email, role=UserRole.RESEARCHER)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def get_or_create_user_from_claims(db: AsyncSession, claims: dict) -> User:
    external_id = claims.get("sub")
    if not external_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing subject (sub)",
            headers={"WWW-Authenticate": "Bearer"},
        )

    result = await db.execute(select(User).where(User.external_id == str(external_id)))
    user = result.scalar_one_or_none()
    if user is not None:
        if not user.is_active:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User is inactive")
        return user

    email = claims.get("email") or claims.get("preferred_username")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing email for user provisioning",
        )

    user = User(external_id=str(external_id), email=str(email), role=UserRole.RESEARCHER)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    if settings.DEV_AUTH_BYPASS and not settings.is_production:
        return await _get_dev_user(db)

    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    try:
        user_id = decode_session_token(token)
        result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
        user = result.scalar_one_or_none()
        if user and user.is_active:
            return user
    except JWTError:
        pass

    if settings.vk_oauth_configured:
        try:
            claims = decode_vk_access_token(token)
            return await get_or_create_user_from_claims(db, claims)
        except (JWTError, httpx.HTTPError):
            pass

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )
