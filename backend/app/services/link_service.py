import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.survey_links import SurveyLinks


async def deactivate_survey_links(db: AsyncSession, survey_id: uuid.UUID) -> None:
    result = await db.execute(
        select(SurveyLinks).where(
            SurveyLinks.survey_id == survey_id,
            SurveyLinks.is_active.is_(True),
        )
    )
    for link in result.scalars().all():
        link.is_active = False
