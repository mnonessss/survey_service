import datetime
import uuid

from pydantic import BaseModel, Field


class SurveyLinkCreate(BaseModel):
    expires_at: datetime.datetime | None = None


class SurveyLinkResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    survey_id: uuid.UUID
    token: str
    is_active: bool
    created_at: datetime.datetime
    expires_at: datetime.datetime | None
    public_url: str


class SurveyLinkCreatedResponse(SurveyLinkResponse):
    token: str = Field(description="Показывается один раз при создании")
