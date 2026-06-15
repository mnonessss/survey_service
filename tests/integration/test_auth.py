import pytest
from httpx import AsyncClient

from tests.conftest import VK_SILENT_AUTH_PAYLOAD


@pytest.mark.asyncio
async def test_health(client: AsyncClient):
    response = await client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["env"] == "test"


@pytest.mark.asyncio
async def test_silent_auth_success(client: AsyncClient):
    response = await client.post("/api/auth/silent", json=VK_SILENT_AUTH_PAYLOAD)
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["access_token"]


@pytest.mark.asyncio
async def test_silent_auth_invalid_sign(client: AsyncClient):
    payload = {**VK_SILENT_AUTH_PAYLOAD, "sign": "invalid-sign"}
    response = await client.post("/api/auth/silent", json=payload)
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_me_requires_auth(client: AsyncClient):
    response = await client.get("/auth/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_me_with_session_token(client: AsyncClient, auth_headers: dict[str, str]):
    response = await client.get("/auth/me", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["email"] == "vk494075@mini.vk"
