import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_survey_crud_flow(client: AsyncClient, auth_headers: dict[str, str]):
    create = await client.post(
        "/surveys/",
        headers=auth_headers,
        json={"title": "Тестовый опрос", "description": "Описание"},
    )
    assert create.status_code == 200, create.text
    survey = create.json()
    survey_id = survey["id"]
    assert survey["title"] == "Тестовый опрос"
    assert survey["status"] == "DRAFT"

    listed = await client.get("/surveys/", headers=auth_headers)
    assert listed.status_code == 200
    assert any(item["id"] == survey_id for item in listed.json())

    question = await client.post(
        f"/surveys/{survey_id}/questions",
        headers=auth_headers,
        json={
            "title": "Ваше имя?",
            "question_type": "TEXT",
            "required": True,
            "order": 0,
        },
    )
    assert question.status_code == 201, question.text
    question_id = question.json()["id"]

    updated = await client.put(
        f"/surveys/{survey_id}",
        headers=auth_headers,
        json={"title": "Обновлённый опрос"},
    )
    assert updated.status_code == 200
    assert updated.json()["title"] == "Обновлённый опрос"

    questions = await client.get(f"/surveys/{survey_id}/questions", headers=auth_headers)
    assert questions.status_code == 200
    assert len(questions.json()) == 1
    assert questions.json()[0]["id"] == question_id


@pytest.mark.asyncio
async def test_list_surveys_requires_auth(client: AsyncClient):
    response = await client.get("/surveys/")
    assert response.status_code == 401
