import pytest
from httpx import AsyncClient


async def _create_published_survey(client: AsyncClient, auth_headers: dict[str, str]) -> tuple[str, str]:
    survey = await client.post(
        "/surveys/",
        headers=auth_headers,
        json={"title": "Публичный опрос", "description": ""},
    )
    assert survey.status_code == 200, survey.text
    survey_id = survey.json()["id"]

    question = await client.post(
        f"/surveys/{survey_id}/questions",
        headers=auth_headers,
        json={
            "title": "Комментарий",
            "question_type": "TEXT",
            "required": True,
            "order": 0,
        },
    )
    assert question.status_code == 201, question.text
    question_id = question.json()["id"]

    link = await client.post(
        f"/surveys/{survey_id}/links",
        headers=auth_headers,
        json={},
    )
    assert link.status_code == 201, link.text
    token = link.json()["token"]
    return token, question_id


@pytest.mark.asyncio
async def test_public_survey_submit_flow(client: AsyncClient, auth_headers: dict[str, str]):
    token, question_id = await _create_published_survey(client, auth_headers)

    public = await client.get(f"/public/surveys/{token}")
    assert public.status_code == 200, public.text
    body = public.json()
    assert body["title"] == "Публичный опрос"
    assert len(body["questions"]) == 1

    session = await client.post(f"/public/surveys/{token}/sessions")
    assert session.status_code == 200, session.text
    session_id = session.json()["session_id"]
    session_token = session.json()["session_token"]

    draft = await client.put(
        f"/public/sessions/{session_id}/draft",
        headers={"X-Session-Token": session_token},
        json={
            "answers": [
                {"question_id": question_id, "value_text": "Черновик ответа"},
            ],
        },
    )
    assert draft.status_code == 204, draft.text

    loaded_draft = await client.get(
        f"/public/sessions/{session_id}/draft",
        headers={"X-Session-Token": session_token},
    )
    assert loaded_draft.status_code == 200
    assert loaded_draft.json()["answers"]

    submit = await client.post(
        f"/public/sessions/{session_id}/submit",
        headers={"X-Session-Token": session_token},
        json={
            "answers": [
                {"question_id": question_id, "value_text": "Финальный ответ"},
            ],
        },
    )
    assert submit.status_code == 204, submit.text

    responses = await client.get(
        f"/surveys/{body['id']}/responses",
        headers=auth_headers,
    )
    assert responses.status_code == 200, responses.text
    payload = responses.json()
    assert payload["total"] == 1
    assert payload["rows"][0]["answers"][0]["display_value"] == "Финальный ответ"


@pytest.mark.asyncio
async def test_public_survey_unknown_token(client: AsyncClient):
    response = await client.get("/public/surveys/unknown-token-value")
    assert response.status_code == 404
