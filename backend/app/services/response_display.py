import html
from typing import Any

from app.core.sanitize import escape_user_text
from app.models.enums import QuestionType
from app.models.question import Question
from app.services.question_validation import CHOICE_TYPES


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


def _plain_export_text(value: str) -> str:
    return html.unescape(value)


def format_export_value(question: Question, *, value_text: str | None, value_json: Any) -> str:
    if value_json is not None:
        if isinstance(value_json, list):
            if question.question_type in CHOICE_TYPES:
                labels_map = {opt.value: opt.label for opt in question.options}
                parts = [_plain_export_text(labels_map.get(str(item), str(item))) for item in value_json]
                return ", ".join(parts)
            return ", ".join(
                _plain_export_text(str(item)) if isinstance(item, str) else str(item) for item in value_json
            )
        return _plain_export_text(str(value_json))

    text = (value_text or "").strip()
    if not text:
        return ""
    return _plain_export_text(text)


def format_export_header(title: str) -> str:
    return _plain_export_text(title)
