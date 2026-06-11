from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.database import get_db
from app.security.dependencies import get_or_create_user_by_external_id
from app.security.session_token import create_session_token
from app.security.vk_mini_app import verify_vk_launch_signature

router = APIRouter(prefix="/api/auth", tags=["silent-auth"])


class VkSilentAuthRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    vk_user_id: int
    sign: str = Field(min_length=1)


@router.post("/silent")
async def silent_authorization(payload: VkSilentAuthRequest, db: AsyncSession = Depends(get_db)):
    """Сквозная авторизация при запуске из VK Mini Apps (без кнопки «Войти»)."""
    secret_key = settings.VK_SERVICE_SECRET_KEY
    if not secret_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Не задан VK_SERVICE_SECRET_KEY",
        )

    data_dict = payload.model_dump(exclude_none=True)
    if not verify_vk_launch_signature(data_dict, secret_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверная подпись VK. Доступ запрещен.",
        )

    user = await get_or_create_user_by_external_id(
        db,
        external_id=str(payload.vk_user_id),
        email=f"vk{payload.vk_user_id}@mini.vk",
    )

    return {
        "status": "success",
        "message": "Бесшовная авторизация успешна",
        "vk_user_id": payload.vk_user_id,
        "access_token": create_session_token(str(user.id)),
    }
