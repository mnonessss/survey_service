import datetime
import uuid

from pydantic import BaseModel

from app.models.enums import SurveyStatus


class CreateSurveyRequest(BaseModel):
    title: str
    description: str | None = None
    status: SurveyStatus = SurveyStatus.DRAFT


class UpdateSurveyRequest(BaseModel):
    title: str | None = None
    description: str | None = None
    status: SurveyStatus | None = None


class SurveyResponse(BaseModel):
    model_config = {"from_attributes": True}
    id: uuid.UUID
    title: str
    description: str | None
    status: SurveyStatus
    created_by: uuid.UUID | None = None
    created_at: datetime.datetime
    updated_at: datetime.datetime
    has_been_published: bool = False