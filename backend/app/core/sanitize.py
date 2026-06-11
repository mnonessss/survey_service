import html
import json
from typing import Any


def escape_user_text(value: str | None) -> str | None:
    if value is None:
        return None
    return html.escape(value, quote=True)


def sanitize_answer_payload(value_text: str | None, value_json: Any) -> tuple[str | None, Any]:
    safe_text = escape_user_text(value_text)
    safe_json = value_json
    if isinstance(value_json, list):
        safe_json = [escape_user_text(str(v)) if isinstance(v, str) else v for v in value_json]
    elif isinstance(value_json, str):
        safe_json = escape_user_text(value_json)
    return safe_text, safe_json


def sanitize_export_row(value: Any) -> str:
    """Форматирует значение для экспорта (XLS/JSON API) без HTML-экранирования."""
    if value is None:
        return ""
    if isinstance(value, list):
        text = ", ".join(str(item) for item in value)
    elif isinstance(value, dict):
        text = json.dumps(value, ensure_ascii=False)
    else:
        text = str(value)
    return html.unescape(text)
