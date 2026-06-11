import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api import export as export_api
from app.api import links as links_api
from app.api import questions as questions_api
from app.api import responses as responses_api
from app.api import uploads as uploads_api
from app.db.database import get_db
from app.models.enums import SurveyStatus, UserRole
from app.models.question import Question
from app.models.survey import Survey
from app.models.survey_links import SurveyLinks
from app.models.user import User
from app.schemas.survey import CreateSurveyRequest, SurveyResponse, UpdateSurveyRequest
from app.security.dependencies import get_current_user
from app.security.permissions import require_role
from app.services.link_service import deactivate_survey_links
from app.services.question_validation import validate_choice_options_complete

router = APIRouter(
    prefix="/surveys",
    tags=["surveys"],
    dependencies=[Depends(get_current_user)],
)

_researcher_or_admin = Depends(require_role(UserRole.RESEARCHER, UserRole.ADMIN))


async def _published_survey_ids(db: AsyncSession, survey_ids: list[uuid.UUID]) -> set[uuid.UUID]:
    if not survey_ids:
        return set()
    result = await db.execute(
        select(SurveyLinks.survey_id).where(SurveyLinks.survey_id.in_(survey_ids)).distinct()
    )
    return set(result.scalars().all())


def _to_survey_response(survey: Survey, published_ids: set[uuid.UUID]) -> SurveyResponse:
    return SurveyResponse.model_validate(survey).model_copy(
        update={"has_been_published": survey.id in published_ids},
    )


def _survey_select(survey_id: uuid.UUID | None, current_user: User):
    stmt = select(Survey)
    if survey_id is not None:
        stmt = stmt.where(Survey.id == survey_id)
    if current_user.role != UserRole.ADMIN:
        stmt = stmt.where(Survey.created_by == current_user.id)
    return stmt


@router.get("/", response_model=List[SurveyResponse])
async def get_all_surveys(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        _survey_select(None, current_user).order_by(Survey.created_at.desc())
    )
    surveys = result.scalars().all()
    published_ids = await _published_survey_ids(db, [survey.id for survey in surveys])
    return [_to_survey_response(survey, published_ids) for survey in surveys]


@router.get("/{survey_id}", response_model=SurveyResponse)
async def get_survey(
    survey_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(_survey_select(survey_id, current_user))
    survey = result.scalar_one_or_none()
    if not survey:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Survey not found")
    published_ids = await _published_survey_ids(db, [survey.id])
    return _to_survey_response(survey, published_ids)


@router.post("/", response_model=SurveyResponse, dependencies=[_researcher_or_admin])
async def create_survey(
    survey: CreateSurveyRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    new_survey = Survey(**survey.model_dump(), created_by=current_user.id)
    db.add(new_survey)
    await db.commit()
    await db.refresh(new_survey)
    return new_survey


@router.put("/{survey_id}", response_model=SurveyResponse, dependencies=[_researcher_or_admin])
async def update_survey(
    survey_id: uuid.UUID,
    survey: UpdateSurveyRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(_survey_select(survey_id, current_user))
    existing_survey = result.scalar_one_or_none()
    if not existing_survey:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Survey not found")

    update_data = survey.model_dump(exclude_unset=True)

    if existing_survey.status == SurveyStatus.ACTIVE:
        new_status = update_data.get("status")
        non_status_fields = {k for k in update_data if k != "status"}
        if non_status_fields or (new_status is not None and new_status != SurveyStatus.DRAFT):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Survey in status {existing_survey.status.value} cannot be edited",
            )

    if update_data.get("status") == SurveyStatus.ACTIVE:
        result = await db.execute(
            select(Question)
            .where(Question.survey_id == survey_id)
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

    new_status = update_data.get("status")
    if new_status == SurveyStatus.DRAFT:
        await deactivate_survey_links(db, survey_id)

    for field, value in update_data.items():
        setattr(existing_survey, field, value)

    await db.commit()
    await db.refresh(existing_survey)
    return existing_survey


@router.delete("/{survey_id}", dependencies=[_researcher_or_admin])
async def delete_survey(
    survey_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = delete(Survey).where(Survey.id == survey_id)
    if current_user.role != UserRole.ADMIN:
        stmt = stmt.where(Survey.created_by == current_user.id)

    result = await db.execute(stmt)
    if result.rowcount == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Survey not found")

    await db.commit()
    return {"message": "Survey deleted successfully"}


router.include_router(questions_api.router, prefix="")
router.include_router(uploads_api.router, prefix="")
router.include_router(links_api.router, prefix="")
router.include_router(responses_api.router, prefix="")
router.include_router(export_api.router, prefix="")
