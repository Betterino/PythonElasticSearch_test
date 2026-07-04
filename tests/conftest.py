import pytest_asyncio
from datetime import datetime
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from elasticsearch import AsyncElasticsearch
import app.es.client as es_client_module

from app.main import app
from app.db.session import Base, get_db
from app.db.model import Document
from app.es.client import INDEX_NAME

TEST_DB_URL = "postgresql+asyncpg://docsearch:docsearch@postgres:5432/docsearch_test"
TEST_ES_URL = "http://elasticsearch:9200"
TEST_INDEX = "documents_test"


@pytest_asyncio.fixture
async def engine():
    engine = create_async_engine(TEST_DB_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def session(engine):
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as sess:
        yield sess
        await sess.rollback()


@pytest_asyncio.fixture
async def es_client():
    es = AsyncElasticsearch(TEST_ES_URL)
    if await es.indices.exists(index=TEST_INDEX):
        await es.indices.delete(index=TEST_INDEX)
    await es.indices.create(
        index=TEST_INDEX,
        mappings={"properties": {"id": {"type": "keyword"}, "text": {"type": "text"}}},
    )
    yield es
    await es.indices.delete(index=TEST_INDEX, ignore_unavailable=True)
    await es.close()


@pytest_asyncio.fixture
async def client(session):
    async def override_get_session():
        yield session

    app.dependency_overrides[get_db] = override_get_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


async def make_document(session, es, text, rubrics=None, created_date=None) -> Document:
    doc = Document(
        text=text,
        rubrics=rubrics or [],
        created_date=created_date or datetime(2024, 1, 1),
    )
    session.add(doc)
    await session.flush()
    await es.index(
        index=TEST_INDEX,
        id=str(doc.id),
        document={"id": doc.id, "text": doc.text},
        refresh="wait_for",  
    )
    await session.commit()
    return doc

@pytest_asyncio.fixture(autouse=True)
async def reset_es_singleton():
    es_client_module._es = None
    yield
    if es_client_module._es is not None:
        await es_client_module._es.close()
        es_client_module._es = None