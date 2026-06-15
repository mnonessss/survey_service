import os
import sys
import uuid
from collections.abc import AsyncGenerator
from pathlib import Path

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.pool import StaticPool

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379")
os.environ.setdefault("APP_SECRET", "test-app-secret-key-for-jwt-signing!!")
os.environ.setdefault("CSRF_SECRET", "test-csrf-secret-key-for-signing!!")
os.environ.setdefault("VK_SERVICE_SECRET_KEY", "wvl68m4dR1UpLrVRli")
os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("PUBLIC_APP_URL", "http://testserver")
os.environ.setdefault("API_PUBLIC_URL", "http://testserver")
os.environ.setdefault("CORS_ORIGINS", "http://testserver")
os.environ.setdefault("DEV_AUTH_BYPASS", "false")
os.environ.setdefault("UPLOAD_DIR", str(ROOT / ".test_uploads"))

from app.db.base import Base  # noqa: E402
from app.models import (  # noqa: E402, F401
    answer,
    external_api_key,
    question,
    question_option,
    response_session,
    survey,
    survey_links,
    user,
)

# SQLite не поддерживает JSONB/UUID из PostgreSQL — подменяем типы при компиляции.
@compiles(JSONB, "sqlite")
def _compile_jsonb_sqlite(_element, _compiler, **_kw):
    return "JSON"


@compiles(PG_UUID, "sqlite")
def _compile_uuid_sqlite(_element, _compiler, **_kw):
    return "CHAR(36)"


class FakeRedis:
    def __init__(self) -> None:
        self._store: dict[str, str] = {}

    async def setex(self, key: str, _ttl: int, value: str) -> None:
        self._store[key] = value

    async def get(self, key: str) -> str | None:
        return self._store.get(key)

    async def delete(self, key: str) -> None:
        self._store.pop(key, None)


# Официальный пример из документации VK.
VK_SILENT_AUTH_PAYLOAD = {
    "vk_user_id": 494075,
    "vk_app_id": 6736218,
    "vk_is_app_user": 1,
    "vk_are_notifications_enabled": 1,
    "vk_language": "ru",
    "vk_access_token_settings": "",
    "vk_platform": "android",
    "sign": "htQFduJpLxz7ribXRZpDFUH-XEUhC9rBPTJkjUFEkRA",
}


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest_asyncio.fixture
async def db_engine():
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    session_factory = async_sessionmaker(db_engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def fake_redis():
    return FakeRedis()


@pytest_asyncio.fixture
async def client(db_session, fake_redis, tmp_path_factory) -> AsyncGenerator[AsyncClient, None]:
    upload_dir = tmp_path_factory.mktemp("uploads")
    os.environ["UPLOAD_DIR"] = str(upload_dir)

    from app.core import redis as redis_module
    from app.db.database import get_db
    from app.main import app
    import app.api.auth as auth_module
    import app.api.public as public_module

    async def _override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    redis_module.redis_client = fake_redis
    public_module.redis_client = fake_redis
    auth_module.redis_client = fake_redis

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def auth_headers(client: AsyncClient) -> dict[str, str]:
    silent = await client.post("/api/auth/silent", json=VK_SILENT_AUTH_PAYLOAD)
    assert silent.status_code == 200, silent.text
    token = silent.json()["access_token"]

    csrf = await client.get("/auth/csrf")
    assert csrf.status_code == 200, csrf.text
    csrf_token = csrf.json()["csrf_token"]

    return {
        "Authorization": f"Bearer {token}",
        "X-CSRF-Token": csrf_token,
    }


@pytest.fixture
def question_id() -> uuid.UUID:
    return uuid.uuid4()
