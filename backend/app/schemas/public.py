import uuid
from typing import Any

from pydantic import BaseModel, Field

from app.models.enums import QuestionType
from app.schemas.question import QuestionOptionResponse


class PublicQuestionSchema(BaseModel):
    id: uuid.UUID
    title: str
    question_type: QuestionType
    required: bool
    order: int
    options: list[QuestionOptionResponse] = []


class PublicSurveySchema(BaseModel):
    id: uuid.UUID
    title: str
    description: str | None
    questions: list[PublicQuestionSchema]


class SessionCreateResponse(BaseModel):
    session_id: uuid.UUID
    session_token: str


class AnswerSubmitItem(BaseModel):
    question_id: uuid.UUID
    value_text: str | None = None
    value_json: list[str] | str | int | None = None


class DraftSaveRequest(BaseModel):
    answers: list[AnswerSubmitItem]


class SubmitSurveyRequest(BaseModel):
    answers: list[AnswerSubmitItem]


class AnswerDisplaySchema(BaseModel):
    question_id: uuid.UUID
    value_text: str | None = None
    value_json: Any = None
