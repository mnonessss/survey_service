from datetime import datetime, timezone
import json
import secrets
import uuid

from fastapi import APIRouter, Depends, File, Header, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.redis import redis_client
from app.core.sanitize import escape_user_text, sanitize_answer_payload
from app.db.database import get_db
from app.models.answer import Answer
from app.models.enums import QuestionType, SurveyStatus
from app.models.question import Question
from app.models.response_session import ResponseSession
from app.models.survey import Survey
from app.models.survey_links import SurveyLinks
from app.schemas.public import (
    DraftSaveRequest,
    PublicQuestionSchema,
    PublicSurveySchema,
    SessionCreateResponse,
    SubmitSurveyRequest,
)
from app.schemas.question import QuestionOptionResponse
from app.services.answer_service import load_survey_questions, upsert_answers, validate_answers_for_submit
from app.services.image_storage import save_image_file

router = APIRouter(prefix="/public", tags=["public"])

SESSION_TOKEN_HEADER = "X-Session-Token"


async def _get_published_survey(db: AsyncSession, link: SurveyLinks) -> Survey:
    result = await db.execute(select(Survey).where(Survey.id == link.survey_id))
    survey = result.scalar_one_or_none()
    if not survey:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Survey not found")
    if survey.status != SurveyStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Опрос не опубликован. В личном кабинете нажмите «Опубликовать» перед использованием ссылки.",
        )
    return survey


async def _get_active_link(db: AsyncSession, token: str) -> SurveyLinks:
    result = await db.execute(select(SurveyLinks).where(SurveyLinks.token == token))
    link = result.scalar_one_or_none()
    if not link or not link.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Survey link not found")
    if link.expires_at and link.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="Survey link expired")
    return link


async def _get_open_session(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    session_token: str = Header(..., alias=SESSION_TOKEN_HEADER),
) -> ResponseSession:
    result = await db.execute(select(ResponseSession).where(ResponseSession.id == session_id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    if session.is_complete:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Session already completed")
    if not secrets.compare_digest(session.session_token, session_token):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid session token")
    return session


@router.get("/surveys/{token}", response_model=PublicSurveySchema)
async def get_public_survey(token: str, db: AsyncSession = Depends(get_db)):
    link = await _get_active_link(db, token)
    survey = await _get_published_survey(db, link)

    questions_result = await db.execute(
        select(Question)
        .where(Question.survey_id == survey.id)
        .options(selectinload(Question.options))
        .order_by(Question.order)
    )
    questions = list(questions_result.scalars().all())
    return PublicSurveySchema(
        id=survey.id,
        title=escape_user_text(survey.title) or "",
        description=escape_user_text(survey.description),
        questions=[
            PublicQuestionSchema(
                id=q.id,
                title=escape_user_text(q.title) or "",
                question_type=q.question_type,
                required=q.required,
                order=q.order,
                options=[QuestionOptionResponse.model_validate(o) for o in sorted(q.options, key=lambda o: o.order)],
            )
            for q in questions
        ],
    )


@router.post("/surveys/{token}/sessions", response_model=SessionCreateResponse)
async def start_session(token: str, db: AsyncSession = Depends(get_db)):
    link = await _get_active_link(db, token)
    await _get_published_survey(db, link)

    session_token = secrets.token_urlsafe(32)
    session = ResponseSession(
        survey_id=link.survey_id,
        link_id=link.id,
        session_token=session_token,
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return SessionCreateResponse(session_id=session.id, session_token=session_token)


def _draft_key(session_id: uuid.UUID) -> str:
    return f"draft:{session_id}"


@router.put("/sessions/{session_id}/draft", status_code=status.HTTP_204_NO_CONTENT)
async def save_draft(
    session_id: uuid.UUID,
    body: DraftSaveRequest,
    db: AsyncSession = Depends(get_db),
    session: ResponseSession = Depends(_get_open_session),
):
    questions = await load_survey_questions(db, session.survey_id)
    items = validate_answers_for_submit(questions, body.answers, require_all_required=False)
    payload = {}
    for k, v in items.items():
        safe_text, safe_json = sanitize_answer_payload(v.value_text, v.value_json)
        payload[str(k)] = {"value_text": safe_text, "value_json": safe_json}
    await redis_client.setex(_draft_key(session_id), settings.DRAFT_TTL_SECONDS, json.dumps(payload))


@router.get("/sessions/{session_id}/draft")
async def get_draft(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    session: ResponseSession = Depends(_get_open_session),
):
    raw = await redis_client.get(_draft_key(session_id))
    if not raw:
        return {"answers": []}
    return {"answers": json.loads(raw)}


@router.post("/sessions/{session_id}/questions/{question_id}/image")
async def upload_answer_image(
    session_id: uuid.UUID,
    question_id: uuid.UUID,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    session: ResponseSession = Depends(_get_open_session),
):
    result = await db.execute(
        select(Question).where(
            Question.id == question_id,
            Question.survey_id == session.survey_id,
        )
    )
    question = result.scalar_one_or_none()
    if not question:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found")
    if question.question_type != QuestionType.IMAGE_UPLOAD:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This question does not accept image uploads",
        )

    relative_dir = f"responses/{session_id}/{question_id}"
    url = await save_image_file(file, relative_dir=relative_dir)
    return {"url": url}


@router.post("/sessions/{session_id}/submit", status_code=status.HTTP_204_NO_CONTENT)
async def submit_survey(
    session_id: uuid.UUID,
    body: SubmitSurveyRequest,
    db: AsyncSession = Depends(get_db),
    session: ResponseSession = Depends(_get_open_session),
):
    questions = await load_survey_questions(db, session.survey_id)
    items = validate_answers_for_submit(questions, body.answers, require_all_required=True)
    await upsert_answers(db, session.id, items)

    session.is_complete = True
    session.completed_at = datetime.now(timezone.utc)
    await db.commit()
    await redis_client.delete(_draft_key(session_id))
