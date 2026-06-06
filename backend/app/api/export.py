import io
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from openpyxl import Workbook
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_owned_survey
from app.core.sanitize import escape_user_text, sanitize_export_row
from app.db.database import get_db
from app.models.user import User
from app.security.dependencies import get_current_user
from app.models.answer import Answer
from app.models.question import Question
from app.models.response_session import ResponseSession

router = APIRouter(tags=["export"])


@router.get("/{survey_id}/export.xlsx")
async def export_survey_xlsx(
    survey_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    survey = await get_owned_survey(survey_id, db, current_user)

    questions_result = await db.execute(
        select(Question).where(Question.survey_id == survey_id).order_by(Question.order)
    )
    questions = list(questions_result.scalars().all())

    sessions_result = await db.execute(
        select(ResponseSession)
        .where(ResponseSession.survey_id == survey_id, ResponseSession.is_complete.is_(True))
        .options(selectinload(ResponseSession.answers))
        .order_by(ResponseSession.completed_at)
    )
    sessions = list(sessions_result.scalars().all())

    wb = Workbook()
    ws = wb.active
    ws.title = "Responses"

    headers = ["session_id", "completed_at"] + [sanitize_export_row(q.title) for q in questions]
    ws.append(headers)

    answers_by_session: dict[uuid.UUID, dict[uuid.UUID, Answer]] = {}
    for session in sessions:
        answers_by_session[session.id] = {a.question_id: a for a in session.answers}

    for session in sessions:
        row = [
            str(session.id),
            session.completed_at.isoformat() if session.completed_at else "",
        ]
        session_answers = answers_by_session.get(session.id, {})
        for question in questions:
            answer = session_answers.get(question.id)
            if not answer:
                row.append("")
                continue
            if answer.value_json is not None:
                row.append(sanitize_export_row(answer.value_json))
            else:
                row.append(sanitize_export_row(answer.value_text))
        ws.append(row)

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    filename = f"survey_{survey.id}_{datetime.now(timezone.utc).strftime('%Y%m%d')}.xlsx"
    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
