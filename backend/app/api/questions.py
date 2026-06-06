import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_owned_survey
from app.db.database import get_db
from app.models.enums import QuestionType, UserRole
from app.models.user import User
from app.security.dependencies import get_current_user
from app.security.permissions import require_role
from app.models.question import Question
from app.models.question_option import QuestionOption
from app.schemas.question import (
    CreateQuestionRequest,
    QuestionOptionCreate,
    QuestionOptionResponse,
    QuestionOptionUpdate,
    QuestionResponse,
    UpdateQuestionRequest,
)
from app.services.question_validation import (
    ensure_survey_editable,
    supports_options,
    validate_option_create,
    validate_question_type_change,
)

router = APIRouter(tags=["questions"])

_researcher_or_admin = Depends(require_role(UserRole.RESEARCHER, UserRole.ADMIN))


def _questions_query(survey_id: uuid.UUID, question_id: uuid.UUID | None = None):
    stmt = (
        select(Question)
        .where(Question.survey_id == survey_id)
        .options(selectinload(Question.options))
        .order_by(Question.order, Question.created_at)
    )
    if question_id is not None:
        stmt = stmt.where(Question.id == question_id)
    return stmt


async def _get_question_or_404(
    survey_id: uuid.UUID,
    question_id: uuid.UUID,
    db: AsyncSession,
) -> Question:
    result = await db.execute(_questions_query(survey_id, question_id))
    question = result.scalar_one_or_none()
    if not question:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found")
    return question


def _to_question_response(question: Question) -> QuestionResponse:
    return QuestionResponse(
        id=question.id,
        survey_id=question.survey_id,
        title=question.title,
        question_type=question.question_type,
        required=question.required,
        order=question.order,
        created_at=question.created_at,
        options=[
            QuestionOptionResponse.model_validate(opt)
            for opt in sorted(question.options, key=lambda o: (o.order, o.created_at))
        ],
    )


@router.get("/{survey_id}/questions", response_model=List[QuestionResponse])
async def list_questions(
    survey_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await get_owned_survey(survey_id, db, current_user)
    result = await db.execute(_questions_query(survey_id))
    return [_to_question_response(q) for q in result.scalars().all()]


@router.get("/{survey_id}/questions/{question_id}", response_model=QuestionResponse)
async def get_question(
    survey_id: uuid.UUID,
    question_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await get_owned_survey(survey_id, db, current_user)
    question = await _get_question_or_404(survey_id, question_id, db)
    return _to_question_response(question)


@router.post(
    "/{survey_id}/questions",
    response_model=QuestionResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[_researcher_or_admin],
)
async def create_question(
    survey_id: uuid.UUID,
    body: CreateQuestionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    survey = await get_owned_survey(survey_id, db, current_user)
    ensure_survey_editable(survey)

    question = Question(survey_id=survey_id, **body.model_dump())
    db.add(question)
    await db.commit()

    question = await _get_question_or_404(survey_id, question.id, db)
    return _to_question_response(question)


@router.put(
    "/{survey_id}/questions/{question_id}",
    response_model=QuestionResponse,
    dependencies=[_researcher_or_admin],
)
async def update_question(
    survey_id: uuid.UUID,
    question_id: uuid.UUID,
    body: UpdateQuestionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    survey = await get_owned_survey(survey_id, db, current_user)
    ensure_survey_editable(survey)

    question = await _get_question_or_404(survey_id, question_id, db)
    update_data = body.model_dump(exclude_unset=True)

    new_type = update_data.get("question_type", question.question_type)
    if "question_type" in update_data:
        validate_question_type_change(
            question.question_type,
            new_type,
            len(question.options),
        )
        if not supports_options(new_type) and question.options:
            await db.execute(
                delete(QuestionOption).where(QuestionOption.question_id == question.id)
            )

    for field, value in update_data.items():
        setattr(question, field, value)

    await db.commit()
    question = await _get_question_or_404(survey_id, question_id, db)
    return _to_question_response(question)


@router.delete(
    "/{survey_id}/questions/{question_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[_researcher_or_admin],
)
async def delete_question(
    survey_id: uuid.UUID,
    question_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    survey = await get_owned_survey(survey_id, db, current_user)
    ensure_survey_editable(survey)

    question = await _get_question_or_404(survey_id, question_id, db)
    await db.execute(delete(QuestionOption).where(QuestionOption.question_id == question.id))
    await db.delete(question)
    await db.commit()


@router.get(
    "/{survey_id}/questions/{question_id}/options",
    response_model=List[QuestionOptionResponse],
)
async def list_options(
    survey_id: uuid.UUID,
    question_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await get_owned_survey(survey_id, db, current_user)
    question = await _get_question_or_404(survey_id, question_id, db)
    return [
        QuestionOptionResponse.model_validate(opt)
        for opt in sorted(question.options, key=lambda o: (o.order, o.created_at))
    ]


@router.post(
    "/{survey_id}/questions/{question_id}/options",
    response_model=QuestionOptionResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[_researcher_or_admin],
)
async def create_option(
    survey_id: uuid.UUID,
    question_id: uuid.UUID,
    body: QuestionOptionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    survey = await get_owned_survey(survey_id, db, current_user)
    ensure_survey_editable(survey)

    question = await _get_question_or_404(survey_id, question_id, db)
    validate_option_create(
        question,
        image_url=body.image_url,
        options_count=len(question.options),
    )

    option_data = body.model_dump()
    if not option_data.get("value"):
        option_data["value"] = option_data["label"]
    option = QuestionOption(question_id=question.id, **option_data)
    db.add(option)
    await db.commit()
    await db.refresh(option)
    return option


@router.put(
    "/{survey_id}/questions/{question_id}/options/{option_id}",
    response_model=QuestionOptionResponse,
    dependencies=[_researcher_or_admin],
)
async def update_option(
    survey_id: uuid.UUID,
    question_id: uuid.UUID,
    option_id: uuid.UUID,
    body: QuestionOptionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    survey = await get_owned_survey(survey_id, db, current_user)
    ensure_survey_editable(survey)

    question = await _get_question_or_404(survey_id, question_id, db)
    result = await db.execute(
        select(QuestionOption).where(
            QuestionOption.id == option_id,
            QuestionOption.question_id == question.id,
        )
    )
    option = result.scalar_one_or_none()
    if not option:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Option not found")

    update_data = body.model_dump(exclude_unset=True)
    if (
        question.question_type == QuestionType.IMAGE_CHOICE
        and "image_url" in update_data
        and not update_data["image_url"]
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="image_url is required for IMAGE_CHOICE options",
        )
    if not supports_options(question.question_type):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Question type {question.question_type.value} does not support options",
        )

    for field, value in update_data.items():
        setattr(option, field, value)

    await db.commit()
    await db.refresh(option)
    return option


@router.delete(
    "/{survey_id}/questions/{question_id}/options/{option_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[_researcher_or_admin],
)
async def delete_option(
    survey_id: uuid.UUID,
    question_id: uuid.UUID,
    option_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    survey = await get_owned_survey(survey_id, db, current_user)
    ensure_survey_editable(survey)

    question = await _get_question_or_404(survey_id, question_id, db)
    result = await db.execute(
        select(QuestionOption).where(
            QuestionOption.id == option_id,
            QuestionOption.question_id == question.id,
        )
    )
    option = result.scalar_one_or_none()
    if not option:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Option not found")

    await db.delete(option)
    await db.commit()
