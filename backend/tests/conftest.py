# backend/tests/conftest.py

import psycopg2
import pytest_asyncio
import redis.asyncio as redis
from motor.motor_asyncio import AsyncIOMotorClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.config.settings import get_settings

settings = get_settings()


def ensure_postgres_test_db():
    """테스트 시작 전에 test_db가 없으면 생성"""
    conn = psycopg2.connect(
        dbname="postgres",
        user=settings.POSTGRES_USER,
        password=settings.POSTGRES_PASSWORD,
        host=settings.POSTGRES_HOST,
        port=settings.POSTGRES_PORT,
    )
    conn.set_session(autocommit=True)
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (settings.POSTGRES_DB,))
    exists = cur.fetchone()
    if not exists:
        cur.execute(f"CREATE DATABASE {settings.POSTGRES_DB}")
    cur.close()
    conn.close()


@pytest_asyncio.fixture(scope="session")
def setup_postgres_test_db():
    ensure_postgres_test_db()


@pytest_asyncio.fixture
async def pg_session():
    engine = create_async_engine(settings.POSTGRES_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        await session.execute(text("CREATE TABLE IF NOT EXISTS test_table (id SERIAL PRIMARY KEY, name TEXT);"))
        await session.commit()
        yield session

        try:
            await session.execute(text("DROP TABLE IF EXISTS test_table;"))
            await session.commit()
        except RuntimeError:
            pass

    await engine.dispose()


@pytest_asyncio.fixture
async def mongo_collection():
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    db = client.test_db
    collection = db.test_collection

    await collection.delete_many({})
    yield collection
    try:
        await collection.drop()
    except RuntimeError:
        pass
    finally:
        client.close()


@pytest_asyncio.fixture
async def redis_client():
    client = redis.from_url(settings.REDIS_URL, decode_responses=True)

    await client.flushdb()
    yield client
    try:
        await client.flushdb()
    except RuntimeError:
        pass
