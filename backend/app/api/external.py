import hashlib
import secrets
import uuid
from typing import List

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.sanitize import escape_user_text, sanitize_export_row
from app.core.vault import get_secret
from app.db.database import get_db
from app.models.external_api_key import ExternalApiKey
from app.models.question import Question
from app.models.response_session import ResponseSession
from app.models.survey import Survey
from app.models.user import User
from app.security.dependencies import get_current_user

router = APIRouter(prefix="/api/v1/external", tags=["external-api"])
integrations_router = APIRouter(prefix="/integrations", tags=["integrations"])


class ApiKeyCreate(BaseModel):
    name: str


class ApiKeyCreated(BaseModel):
    id: uuid.UUID
    name: str
    key_prefix: str
    api_key: str


class ApiKeyResponse(BaseModel):
    id: uuid.UUID
    name: str
    key_prefix: str
    is_active: bool


class ExternalSurveySummary(BaseModel):
    id: uuid.UUID
    title: str
    status: str


class ExternalResponseRow(BaseModel):
    session_id: uuid.UUID
    completed_at: str | None
    answers: dict[str, str]


def _hash_key(raw_key: str) -> str:
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()


async def verify_external_api_key(
    x_api_key: str = Header(..., alias="X-API-Key"),
    db: AsyncSession = Depends(get_db),
) -> ExternalApiKey:
    vault_key = get_secret("external_api_master", vault_path=settings.VAULT_EXTERNAL_KEYS_PATH)
    if vault_key and secrets.compare_digest(x_api_key, vault_key):
        result = await db.execute(select(ExternalApiKey).limit(1))
        key = result.scalar_one_or_none()
        if key:
            return key

    key_hash = _hash_key(x_api_key)
    result = await db.execute(
        select(ExternalApiKey).where(
            ExternalApiKey.key_hash == key_hash,
            ExternalApiKey.is_active.is_(True),
        )
    )
    api_key = result.scalar_one_or_none()
    if not api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")
    return api_key


@integrations_router.post("/api-keys", response_model=ApiKeyCreated)
async def create_api_key(
    body: ApiKeyCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    raw_key = secrets.token_urlsafe(32)
    prefix = raw_key[:8]
    record = ExternalApiKey(
        name=body.name,
        key_prefix=prefix,
        key_hash=_hash_key(raw_key),
        created_by=current_user.id,
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return ApiKeyCreated(id=record.id, name=record.name, key_prefix=prefix, api_key=raw_key)


@integrations_router.get("/api-keys", response_model=List[ApiKeyResponse])
async def list_api_keys(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(ExternalApiKey).where(ExternalApiKey.created_by == current_user.id)
    )
    return [
        ApiKeyResponse(id=k.id, name=k.name, key_prefix=k.key_prefix, is_active=k.is_active)
        for k in result.scalars().all()
    ]


@router.get("/surveys", response_model=List[ExternalSurveySummary])
async def external_list_surveys(
    db: AsyncSession = Depends(get_db),
    _: ExternalApiKey = Depends(verify_external_api_key),
):
    result = await db.execute(select(Survey).order_by(Survey.created_at.desc()))
    return [
        ExternalSurveySummary(id=s.id, title=escape_user_text(s.title) or "", status=s.status.value)
        for s in result.scalars().all()
    ]


@router.get("/surveys/{survey_id}/responses", response_model=List[ExternalResponseRow])
async def external_survey_responses(
    survey_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: ExternalApiKey = Depends(verify_external_api_key),
):
    questions_result = await db.execute(select(Question).where(Question.survey_id == survey_id))
    questions = {q.id: q for q in questions_result.scalars().all()}

    sessions_result = await db.execute(
        select(ResponseSession)
        .where(ResponseSession.survey_id == survey_id, ResponseSession.is_complete.is_(True))
        .options(selectinload(ResponseSession.answers))
    )

    rows: list[ExternalResponseRow] = []
    for session in sessions_result.scalars().all():
        answers_out: dict[str, str] = {}
        for answer in session.answers:
            question = questions.get(answer.question_id)
            title = escape_user_text(question.title) if question else str(answer.question_id)
            if answer.value_json is not None:
                answers_out[title or ""] = sanitize_export_row(answer.value_json)
            else:
                answers_out[title or ""] = sanitize_export_row(answer.value_text)
        rows.append(
            ExternalResponseRow(
                session_id=session.id,
                completed_at=session.completed_at.isoformat() if session.completed_at else None,
                answers=answers_out,
            )
        )
    return rows
