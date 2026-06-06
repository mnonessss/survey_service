import datetime
import uuid

from pydantic import BaseModel, Field

from app.models.enums import QuestionType


class QuestionOptionCreate(BaseModel):
    label: str = Field(min_length=1, max_length=255)
    value: str | None = Field(default=None, max_length=255)
    image_url: str | None = Field(default=None, max_length=255)
    order: int = Field(default=0, ge=0)


class QuestionOptionUpdate(BaseModel):
    label: str | None = Field(default=None, min_length=1, max_length=255)
    value: str | None = Field(default=None, min_length=1, max_length=255)
    image_url: str | None = Field(default=None, max_length=255)
    order: int | None = Field(default=None, ge=0)


class QuestionOptionResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    question_id: uuid.UUID
    label: str
    value: str
    image_url: str | None
    order: int
    created_at: datetime.datetime


class CreateQuestionRequest(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    question_type: QuestionType
    required: bool = False
    order: int = Field(default=0, ge=0)


class UpdateQuestionRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    question_type: QuestionType | None = None
    required: bool | None = None
    order: int | None = Field(default=None, ge=0)


class QuestionResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    survey_id: uuid.UUID
    title: str
    question_type: QuestionType
    required: bool
    order: int
    created_at: datetime.datetime
    options: list[QuestionOptionResponse] = []
