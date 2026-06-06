from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.enums import QuestionType, SurveyStatus
from app.models.question import Question
from app.models.question_option import QuestionOption
from app.models.survey import Survey

CHOICE_TYPES = frozenset(
    {
        QuestionType.SINGLE_CHOICE,
        QuestionType.MULTIPLE_CHOICE,
        QuestionType.IMAGE_CHOICE,
    }
)
NO_OPTION_TYPES = frozenset(
    {
        QuestionType.TEXT,
        QuestionType.RATING,
        QuestionType.DATE,
        QuestionType.IMAGE_UPLOAD,
    }
)

EDITABLE_SURVEY_STATUSES = frozenset({SurveyStatus.DRAFT})


def supports_options(question_type: QuestionType) -> bool:
    return question_type in CHOICE_TYPES


def ensure_survey_editable(survey: Survey) -> None:
    if survey.status not in EDITABLE_SURVEY_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Survey in status {survey.status.value} cannot be edited",
        )


async def activate_survey_for_publication(survey: Survey, db: AsyncSession) -> None:
    if survey.status == SurveyStatus.ACTIVE:
        return

    result = await db.execute(
        select(Question)
        .where(Question.survey_id == survey.id)
        .options(selectinload(Question.options))
    )
    questions = result.scalars().all()
    if not questions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot activate survey without questions",
        )
    for question in questions:
        validate_choice_options_complete(question.question_type, list(question.options))
    survey.status = SurveyStatus.ACTIVE


def validate_question_type_change(
    current_type: QuestionType,
    new_type: QuestionType,
    options_count: int,
) -> None:
    if current_type == new_type:
        return

    if new_type in NO_OPTION_TYPES and options_count > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Remove all options before changing to a type without choices",
        )

    if current_type in CHOICE_TYPES and new_type in NO_OPTION_TYPES:
        return

    if new_type in CHOICE_TYPES and current_type in NO_OPTION_TYPES:
        return


def validate_option_create(question: Question, *, image_url: str | None, options_count: int) -> None:
    if not supports_options(question.question_type):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Question type {question.question_type.value} does not support options",
        )

    if question.question_type == QuestionType.IMAGE_CHOICE and not image_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="image_url is required for IMAGE_CHOICE options",
        )


def validate_choice_options_complete(question_type: QuestionType, options: list[QuestionOption]) -> None:
    if not supports_options(question_type):
        if options:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Options are not allowed for this question type",
            )
        return

    if len(options) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Choice questions require at least 2 options",
        )

    if question_type == QuestionType.IMAGE_CHOICE:
        missing = [opt.id for opt in options if not opt.image_url]
        if missing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="All options for IMAGE_CHOICE must have image_url",
            )
