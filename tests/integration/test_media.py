import uuid

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_response_media_requires_auth(client: AsyncClient, auth_headers: dict[str, str]):
    session_id = uuid.uuid4()
    question_id = uuid.uuid4()
    filename = "photo.jpg"

    survey = await client.post(
        "/surveys/",
        headers=auth_headers,
        json={"title": "Медиа тест", "description": ""},
    )
    survey_id = survey.json()["id"]

    anonymous = await client.get(
        f"/surveys/{survey_id}/response-media/{session_id}/{question_id}/{filename}",
    )
    assert anonymous.status_code == 401


@pytest.mark.asyncio
async def test_public_response_upload_path_not_served_anonymously(client: AsyncClient):
    session_id = uuid.uuid4()
    question_id = uuid.uuid4()
    filename = "photo.jpg"

    response = await client.get(f"/uploads/responses/{session_id}/{question_id}/{filename}")
    assert response.status_code == 404
