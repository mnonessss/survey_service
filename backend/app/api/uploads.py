import uuid

from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_owned_survey
from app.db.database import get_db
from app.models.enums import UserRole
from app.models.user import User
from app.security.dependencies import get_current_user
from app.security.permissions import require_role
from app.services.image_storage import save_image_file
from app.services.question_validation import ensure_survey_editable

router = APIRouter(tags=["uploads"])

_researcher_or_admin = Depends(require_role(UserRole.RESEARCHER, UserRole.ADMIN))


@router.post("/{survey_id}/images", dependencies=[_researcher_or_admin])
async def upload_survey_image(
    survey_id: uuid.UUID,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    survey = await get_owned_survey(survey_id, db, current_user)
    ensure_survey_editable(survey)
    url = await save_image_file(file, relative_dir=str(survey_id))
    return {"url": url}
