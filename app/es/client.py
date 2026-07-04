from elasticsearch import AsyncElasticsearch
from app.core.config import settings
INDEX_NAME = "documents"

_es: AsyncElasticsearch | None = None

def get_es() -> AsyncElasticsearch:
    global _es
    if _es is None:
        _es = AsyncElasticsearch(settings.elasticsearch_url)
    return _es

async def ensure_index():
    es = get_es()
    if not await es.indices.exists(index=INDEX_NAME):
        await es.indices.create(
            index=INDEX_NAME,
            mappings={
                "properties": {
                    "id": {"type": "keyword"},
                    "text": {"type": "text"},
                }
            },
        )