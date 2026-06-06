import json
from typing import Any

from app.core.sanitize import escape_user_text
from app.models.enums import QuestionType
from app.models.question import Question


def format_answer_display(question: Question, *, value_text: str | None, value_json: Any) -> str:
    if value_json is not None:
        if isinstance(value_json, list):
            rendered = ", ".join(str(item) for item in value_json)
        else:
            rendered = str(value_json)
        if question.question_type in {QuestionType.IMAGE_UPLOAD, QuestionType.IMAGE_CHOICE}:
            return rendered
        return escape_user_text(rendered) or "—"

    text = (value_text or "").strip()
    if not text:
        return "—"

    if question.question_type in {QuestionType.IMAGE_UPLOAD, QuestionType.IMAGE_CHOICE}:
        return text

    return escape_user_text(text) or "—"


def answer_sort_key(value: str) -> str:
    return value.casefold()
