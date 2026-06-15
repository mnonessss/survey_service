import pytest
from fastapi import HTTPException
from starlette.requests import Request

from app.security.csrf import (
    CSRF_COOKIE,
    CSRF_HEADER,
    generate_csrf_token,
    unwrap_csrf_token,
    validate_csrf,
    wrap_csrf_token,
)


def _make_request(
    method: str = "POST",
    path: str = "/surveys/",
    headers: dict | None = None,
):
    header_list = []
    for key, value in (headers or {}).items():
        header_list.append((key.lower().encode(), value.encode()))
    scope = {
        "type": "http",
        "method": method,
        "path": path,
        "headers": header_list,
    }
    return Request(scope)


def test_wrap_and_unwrap_csrf_token():
    raw = generate_csrf_token()
    wrapped = wrap_csrf_token(raw)
    assert unwrap_csrf_token(wrapped) == raw


def test_validate_csrf_allows_get_without_token():
    validate_csrf(_make_request(method="GET", path="/surveys/"))


def test_validate_csrf_allows_bearer_with_header_only():
    raw = generate_csrf_token()
    wrapped = wrap_csrf_token(raw)
    validate_csrf(
        _make_request(
            headers={
                "Authorization": "Bearer test-token",
                CSRF_HEADER: wrapped,
            },
        ),
    )


def test_validate_csrf_requires_header_for_bearer():
    with pytest.raises(HTTPException) as exc:
        validate_csrf(_make_request(headers={"Authorization": "Bearer test-token"}))
    assert exc.value.status_code == 403
    assert "missing" in exc.value.detail.lower()


def test_validate_csrf_requires_matching_cookie_without_bearer():
    raw = generate_csrf_token()
    wrapped = wrap_csrf_token(raw)
    validate_csrf(
        _make_request(
            headers={
                CSRF_HEADER: wrapped,
                "cookie": f"{CSRF_COOKIE}={wrapped}",
            },
        ),
    )
