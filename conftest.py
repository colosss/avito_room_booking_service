import os
import pytest
from dotenv import load_dotenv

load_dotenv(".test.env", override=True)

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import delete

from src.infrastructure.database.db_helper import db_helper
from src.infrastructure.database.base import Base
from src.infrastructure.database.models import User, Room, Schedule, Slot, Booking

_TEST_URL = (
    f"postgresql+asyncpg://{os.environ['DB_USER']}:{os.environ['DB_PASSWORD']}"
    f"@{os.environ['DB_HOST']}:{os.environ['DB_PORT']}/{os.environ['DB_NAME']}"
)

_test_engine = create_async_engine(_TEST_URL, echo=False)
_test_session_factory = async_sessionmaker(
    bind=_test_engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)

db_helper.engine = _test_engine
db_helper.session_factory = _test_session_factory


class _FakeRedis:
    def __init__(self):
        self._store: dict = {}

    async def get(self, key: str):
        return self._store.get(key)

    async def setex(self, key: str, ttl: int, value: str):
        self._store[key] = value

    async def delete(self, key: str):
        self._store.pop(key, None)

    def lock(self, name: str, timeout: int = 10):
        return _FakeLock()

    def clear(self):
        self._store.clear()


class _FakeLock:
    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False


_fake_redis = _FakeRedis()


@pytest.fixture(scope="session", autouse=True)
def patch_redis():
    import src.infrastructure.cache.redis_client as redis_mod
    import src.application.use_case.slots as slots_mod
    import src.application.use_case.bookings as bookings_mod

    async def _get_fake():
        return _fake_redis

    async def _fake_invalidate(room_id, slot_date):
        _fake_redis.clear()

    redis_mod.get_redis = _get_fake
    slots_mod.get_redis = _get_fake
    redis_mod.invalidate_slots_cache = _fake_invalidate
    bookings_mod.invalidate_slots_cache = _fake_invalidate


@pytest.fixture(scope="session")
async def db_tables(patch_redis):
    async with _test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with _test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture()
async def clean_db(db_tables):
    yield
    _fake_redis.clear()
    async with _test_session_factory() as session:
        await session.execute(delete(Booking))
        await session.execute(delete(Slot))
        await session.execute(delete(Schedule))
        await session.execute(delete(Room))
        await session.execute(delete(User))
        await session.commit()


@pytest.fixture(scope="session")
async def async_client(db_tables):
    """
    Асинхронный HTTP-клиент через ASGI transport.
    Работает в том же event loop что и db_tables/clean_db fixtures,
    поэтому asyncpg соединения не конфликтуют между двумя loop.
    """
    from httpx import AsyncClient, ASGITransport
    from run.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac


@pytest.fixture(scope="session")
def client(async_client):
    """
    Обёртка для обратной совместимости с синхронными тестами.
    Возвращает async_client — тесты должны вызывать await client.get(...).
    """
    return async_client
