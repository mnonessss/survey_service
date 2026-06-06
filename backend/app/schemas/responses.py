import datetime
import uuid
from typing import Any

from pydantic import BaseModel

from app.models.enums import QuestionType


class ResponseQuestionSchema(BaseModel):
    id: uuid.UUID
    title: str
    question_type: QuestionType
    order: int


class SurveyResponseAnswerSchema(BaseModel):
    question_id: uuid.UUID
    display_value: str
    value_text: str | None = None
    value_json: Any = None


class SurveyResponseRowSchema(BaseModel):
    session_id: uuid.UUID
    started_at: datetime.datetime
    completed_at: datetime.datetime | None
    answers: list[SurveyResponseAnswerSchema]


class SurveyResponsesListSchema(BaseModel):
    survey_id: uuid.UUID
    survey_title: str
    total: int
    questions: list[ResponseQuestionSchema]
    rows: list[SurveyResponseRowSchema]
