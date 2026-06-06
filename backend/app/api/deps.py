import uuid

from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import UserRole
from app.models.survey import Survey
from app.models.user import User


async def get_owned_survey(
    survey_id: uuid.UUID,
    db: AsyncSession,
    current_user: User,
) -> Survey:
    stmt = select(Survey).where(Survey.id == survey_id)
    if current_user.role != UserRole.ADMIN:
        stmt = stmt.where(Survey.created_by == current_user.id)

    result = await db.execute(stmt)
    survey = result.scalar_one_or_none()
    if not survey:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Survey not found")
    return survey
