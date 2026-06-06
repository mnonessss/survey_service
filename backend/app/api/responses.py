import uuid
from enum import Enum

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_owned_survey
from app.core.sanitize import escape_user_text
from app.db.database import get_db
from app.models.user import User
from app.security.dependencies import get_current_user
from app.models.question import Question
from app.models.response_session import ResponseSession
from app.schemas.responses import (
    ResponseQuestionSchema,
    SurveyResponseAnswerSchema,
    SurveyResponseRowSchema,
    SurveyResponsesListSchema,
)
from app.services.response_display import format_answer_display


class ResponseSortBy(str, Enum):
    COMPLETED_AT = "completed_at"
    STARTED_AT = "started_at"
    SESSION_ID = "session_id"


class SortOrder(str, Enum):
    ASC = "asc"
    DESC = "desc"


router = APIRouter(tags=["responses"])


def _sort_sessions(
    sessions: list[ResponseSession],
    *,
    sort_by: ResponseSortBy,
    sort_order: SortOrder,
) -> list[ResponseSession]:
    reverse = sort_order == SortOrder.DESC

    if sort_by == ResponseSortBy.SESSION_ID:
        return sorted(sessions, key=lambda s: str(s.id), reverse=reverse)

    if sort_by == ResponseSortBy.STARTED_AT:
        return sorted(
            sessions,
            key=lambda s: s.started_at or "",
            reverse=reverse,
        )

    return sorted(
        sessions,
        key=lambda s: s.completed_at or "",
        reverse=reverse,
    )


@router.get("/{survey_id}/responses", response_model=SurveyResponsesListSchema)
async def list_survey_responses(
    survey_id: uuid.UUID,
    sort_by: ResponseSortBy = Query(default=ResponseSortBy.COMPLETED_AT),
    sort_order: SortOrder = Query(default=SortOrder.DESC),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    survey = await get_owned_survey(survey_id, db, current_user)

    questions_result = await db.execute(
        select(Question).where(Question.survey_id == survey_id).order_by(Question.order)
    )
    questions = list(questions_result.scalars().all())
    questions_map = {q.id: q for q in questions}

    sessions_result = await db.execute(
        select(ResponseSession)
        .where(ResponseSession.survey_id == survey_id, ResponseSession.is_complete.is_(True))
        .options(selectinload(ResponseSession.answers))
    )
    sessions = _sort_sessions(list(sessions_result.scalars().all()), sort_by=sort_by, sort_order=sort_order)

    rows: list[SurveyResponseRowSchema] = []
    for session in sessions:
        answers_by_question = {a.question_id: a for a in session.answers}
        answer_items: list[SurveyResponseAnswerSchema] = []
        for question in questions:
            answer = answers_by_question.get(question.id)
            if not answer:
                answer_items.append(
                    SurveyResponseAnswerSchema(
                        question_id=question.id,
                        display_value="—",
                    )
                )
                continue
            answer_items.append(
                SurveyResponseAnswerSchema(
                    question_id=question.id,
                    display_value=format_answer_display(
                        question,
                        value_text=answer.value_text,
                        value_json=answer.value_json,
                    ),
                    value_text=answer.value_text,
                    value_json=answer.value_json,
                )
            )
        rows.append(
            SurveyResponseRowSchema(
                session_id=session.id,
                started_at=session.started_at,
                completed_at=session.completed_at,
                answers=answer_items,
            )
        )

    return SurveyResponsesListSchema(
        survey_id=survey.id,
        survey_title=escape_user_text(survey.title) or "",
        total=len(rows),
        questions=[
            ResponseQuestionSchema(
                id=q.id,
                title=escape_user_text(q.title) or "",
                question_type=q.question_type,
                order=q.order,
            )
            for q in questions
        ],
        rows=rows,
    )
