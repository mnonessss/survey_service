import secrets
import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_owned_survey
from app.core.config import settings
from app.db.database import get_db
from app.models.enums import UserRole
from app.models.survey_links import SurveyLinks
from app.models.user import User
from app.schemas.links import SurveyLinkCreate, SurveyLinkResponse
from app.security.dependencies import get_current_user
from app.security.permissions import require_role
from app.services.link_service import deactivate_survey_links
from app.services.question_validation import activate_survey_for_publication

router = APIRouter(tags=["survey-links"])
_researcher_or_admin = Depends(require_role(UserRole.RESEARCHER, UserRole.ADMIN))


def _public_url(token: str) -> str:
    return f"{settings.PUBLIC_APP_URL.rstrip('/')}/s/{token}"


def _to_link_response(link: SurveyLinks) -> SurveyLinkResponse:
    return SurveyLinkResponse(
        id=link.id,
        survey_id=link.survey_id,
        token=link.token,
        is_active=link.is_active,
        created_at=link.created_at,
        expires_at=link.expires_at,
        public_url=_public_url(link.token),
    )


@router.get("/{survey_id}/links", response_model=List[SurveyLinkResponse])
async def list_links(
    survey_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await get_owned_survey(survey_id, db, current_user)
    result = await db.execute(
        select(SurveyLinks)
        .where(SurveyLinks.survey_id == survey_id, SurveyLinks.is_active.is_(True))
        .order_by(SurveyLinks.created_at.desc())
    )
    return [_to_link_response(link) for link in result.scalars().all()]


@router.post(
    "/{survey_id}/links",
    response_model=SurveyLinkResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[_researcher_or_admin],
)
async def create_link(
    survey_id: uuid.UUID,
    body: SurveyLinkCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    survey = await get_owned_survey(survey_id, db, current_user)
    await activate_survey_for_publication(survey, db)
    await deactivate_survey_links(db, survey_id)

    token = secrets.token_urlsafe(48)
    link = SurveyLinks(
        survey_id=survey_id,
        token=token,
        expires_at=body.expires_at,
    )
    db.add(link)
    await db.commit()
    await db.refresh(link)
    return _to_link_response(link)


@router.delete(
    "/{survey_id}/links/{link_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[_researcher_or_admin],
)
async def deactivate_link(
    survey_id: uuid.UUID,
    link_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await get_owned_survey(survey_id, db, current_user)
    result = await db.execute(
        select(SurveyLinks).where(
            SurveyLinks.id == link_id,
            SurveyLinks.survey_id == survey_id,
        )
    )
    link = result.scalar_one_or_none()
    if not link:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Link not found")
    link.is_active = False
    await db.commit()
