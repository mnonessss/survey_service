import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.answer import Answer
from app.models.enums import QuestionType
from app.models.question import Question
from app.schemas.public import AnswerSubmitItem
from app.core.sanitize import sanitize_answer_payload
from app.services.question_validation import CHOICE_TYPES, supports_options


async def load_survey_questions(db: AsyncSession, survey_id: uuid.UUID) -> list[Question]:
    result = await db.execute(
        select(Question).where(Question.survey_id == survey_id).order_by(Question.order)
    )
    return list(result.scalars().all())


def validate_answers_for_submit(
    questions: list[Question],
    answers: list[AnswerSubmitItem],
    *,
    require_all_required: bool,
) -> dict[uuid.UUID, AnswerSubmitItem]:
    questions_map = {q.id: q for q in questions}
    submitted: dict[uuid.UUID, AnswerSubmitItem] = {}

    for item in answers:
        question = questions_map.get(item.question_id)
        if not question:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown question_id")

        if item.question_id in submitted:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Duplicate question answer")

        if supports_options(question.question_type):
            values = item.value_json
            if not isinstance(values, list):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Не выбран обязательный вариант ответа",
                )
            if not values:
                if question.required:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Не выбран обязательный вариант ответа",
                    )
                continue
            if question.question_type == QuestionType.SINGLE_CHOICE and len(values) != 1:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="SINGLE_CHOICE allows exactly one option",
                )
        elif question.question_type == QuestionType.IMAGE_UPLOAD_MULTIPLE:
            values = item.value_json if isinstance(item.value_json, list) else []
            if not values:
                if require_all_required and question.required:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Обязательный вопрос не заполнен",
                    )
                continue
            for value in values:
                if not str(value).startswith("/uploads/"):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Ответ должен содержать загруженные изображения",
                    )
        else:
            text = (item.value_text or "").strip()
            if not text:
                if require_all_required and question.required:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Обязательный вопрос не заполнен",
                    )
                if not question.required:
                    continue
            elif question.question_type == QuestionType.RATING:
                try:
                    rating = int(text)
                except ValueError as exc:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Рейтинг должен быть целым числом от 1 до 10",
                    ) from exc
                if rating < 1 or rating > 10:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Рейтинг должен быть от 1 до 10",
                    )
            elif question.question_type == QuestionType.IMAGE_UPLOAD and not text.startswith("/uploads/"):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Ответ должен содержать загруженное изображение",
                )

        submitted[item.question_id] = item

    if require_all_required:
        for question in questions:
            if question.required and question.id not in submitted:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Обязательный вопрос не заполнен",
                )

    return submitted


async def upsert_answers(
    db: AsyncSession,
    session_id: uuid.UUID,
    items: dict[uuid.UUID, AnswerSubmitItem],
) -> None:
    for question_id, item in items.items():
        safe_text, safe_json = sanitize_answer_payload(item.value_text, item.value_json)
        result = await db.execute(
            select(Answer).where(
                Answer.session_id == session_id,
                Answer.question_id == question_id,
            )
        )
        existing = result.scalar_one_or_none()
        if existing:
            existing.value_text = safe_text
            existing.value_json = safe_json
        else:
            db.add(
                Answer(
                    session_id=session_id,
                    question_id=question_id,
                    value_text=safe_text,
                    value_json=safe_json,
                )
            )
