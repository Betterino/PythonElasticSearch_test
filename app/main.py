from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.es.client import ensure_index
from app.api.routes import router
from app.db.session import init_db
@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    await ensure_index()
    yield

app = FastAPI(
    title="Document Search Service",
    description=(
        "Простой поисковый сервис по текстам постов. "
        "Данные хранятся в PostgreSQL, поиск — через Elasticsearch."
    ),
    version="1.0.0",
    lifespan=lifespan,
)
app.include_router(router)