import html
from typing import Any

from app.core.sanitize import escape_user_text
from app.models.enums import QuestionType
from app.models.question import Question
from app.services.question_validation import CHOICE_TYPES, IMAGE_UPLOAD_TYPES


def format_answer_display(question: Question, *, value_text: str | None, value_json: Any) -> str:
    if value_json is not None:
        if isinstance(value_json, list):
            rendered = ", ".join(str(item) for item in value_json)
        else:
            rendered = str(value_json)
        if question.question_type in IMAGE_UPLOAD_TYPES or question.question_type == QuestionType.IMAGE_CHOICE:
            return rendered
        return escape_user_text(rendered) or "—"

    text = (value_text or "").strip()
    if not text:
        return "—"

    if question.question_type in IMAGE_UPLOAD_TYPES or question.question_type == QuestionType.IMAGE_CHOICE:
        return text

    return escape_user_text(text) or "—"


def answer_sort_key(value: str) -> str:
    return value.casefold()


def _plain_export_text(value: str) -> str:
    return html.unescape(value)


def _export_image_label(count: int) -> str:
    if count <= 0:
        return ""
    if count == 1:
        return "1 изображение (см. в личном кабинете)"
    return f"{count} изображения (см. в личном кабинете)"


def format_export_value(question: Question, *, value_text: str | None, value_json: Any) -> str:
    if value_json is not None:
        if isinstance(value_json, list):
            if question.question_type in CHOICE_TYPES:
                labels_map = {opt.value: opt.label for opt in question.options}
                parts = [_plain_export_text(labels_map.get(str(item), str(item))) for item in value_json]
                return ", ".join(parts)
            if question.question_type in IMAGE_UPLOAD_TYPES:
                count = sum(1 for item in value_json if str(item).startswith("/uploads/"))
                return _export_image_label(count)
            return ", ".join(
                _plain_export_text(str(item)) if isinstance(item, str) else str(item) for item in value_json
            )
        return _plain_export_text(str(value_json))

    text = (value_text or "").strip()
    if not text:
        return ""
    plain = _plain_export_text(text)
    if question.question_type in IMAGE_UPLOAD_TYPES:
        return _export_image_label(1) if plain.startswith("/uploads/") else ""
    return plain


def format_export_header(title: str) -> str:
    return _plain_export_text(title)
