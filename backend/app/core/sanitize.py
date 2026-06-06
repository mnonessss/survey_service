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
    if value is None:
        return ""
    if isinstance(value, (list, dict)):
        return html.escape(json.dumps(value, ensure_ascii=False), quote=True)
    return html.escape(str(value), quote=True)
