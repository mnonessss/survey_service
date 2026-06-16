import secrets
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_owned_survey
from app.core.config import settings
from app.db.database import get_db
from app.models.response_session import ResponseSession
from app.models.user import User
from app.security.dependencies import get_current_user

router = APIRouter(tags=["media"])

SESSION_TOKEN_HEADER = "X-Session-Token"
RESPONSE_UPLOAD_PREFIX = "/uploads/responses/"


def _upload_root() -> Path:
    return Path(settings.UPLOAD_DIR).resolve()


def _safe_filename(filename: str) -> str:
    if not filename or "/" in filename or "\\" in filename or filename in {".", ".."}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid filename")
    return filename


def _response_file_path(session_id: uuid.UUID, question_id: uuid.UUID, filename: str) -> Path:
    safe_name = _safe_filename(filename)
    path = (_upload_root() / "responses" / str(session_id) / str(question_id) / safe_name).resolve()
    responses_root = (_upload_root() / "responses").resolve()
    if not str(path).startswith(str(responses_root)):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid path")
    if not path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    return path


async def _get_open_session_by_token(
    session_id: uuid.UUID,
    db: AsyncSession,
    *,
    session_token: str | None,
) -> ResponseSession:
    if not session_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session token required")

    result = await db.execute(select(ResponseSession).where(ResponseSession.id == session_id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    if session.is_complete:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Session already completed")
    if not secrets.compare_digest(session.session_token, session_token):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid session token")
    return session


@router.get("/uploads/{survey_id}/{filename}")
async def serve_survey_option_image(survey_id: uuid.UUID, filename: str):
    """Публичные изображения вариантов ответа (IMAGE_CHOICE) для респондентов."""
    safe_name = _safe_filename(filename)
    path = (_upload_root() / str(survey_id) / safe_name).resolve()
    survey_root = (_upload_root() / str(survey_id)).resolve()
    if not str(path).startswith(str(survey_root)):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid path")
    if not path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    return FileResponse(path)


@router.get("/surveys/{survey_id}/response-media/{session_id}/{question_id}/{filename}")
async def serve_response_media_for_owner(
    survey_id: uuid.UUID,
    session_id: uuid.UUID,
    question_id: uuid.UUID,
    filename: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Изображения ответов респондентов — только владелец опроса (или админ)."""
    await get_owned_survey(survey_id, db, current_user)

    result = await db.execute(
        select(ResponseSession).where(
            ResponseSession.id == session_id,
            ResponseSession.survey_id == survey_id,
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    return FileResponse(_response_file_path(session_id, question_id, filename))


@router.get("/public/sessions/{session_id}/media/{question_id}/{filename}")
async def serve_response_media_for_session(
    session_id: uuid.UUID,
    question_id: uuid.UUID,
    filename: str,
    db: AsyncSession = Depends(get_db),
    session_token: str | None = Header(None, alias=SESSION_TOKEN_HEADER),
    st: str | None = Query(None, description="Session token (для <img>, когда нельзя передать заголовок)"),
):
    """Превью загруженного ответа во время незавершённого прохождения опроса."""
    session = await _get_open_session_by_token(
        session_id,
        db,
        session_token=session_token or st,
    )
    if session.id != session_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    return FileResponse(_response_file_path(session_id, question_id, filename))
