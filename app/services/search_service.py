from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.es.client import get_es, INDEX_NAME
from app.db.model import Document

CANDIDATE_POOL = 200
RESULT_LIMIT = 20

async def search_documents(session: AsyncSession, query_text: str) -> list[Document]:
    es = get_es()
    resp = await es.search(
        index=INDEX_NAME,
        query={"match": {"text": query_text}},
        size=CANDIDATE_POOL,
        _source=False,
    )
    candidate_ids = [int(hit["_id"]) for hit in resp["hits"]["hits"]]

    if not candidate_ids:
        return []

    stmt = (
        select(Document)
        .where(Document.id.in_(candidate_ids))
        .order_by(Document.created_date.desc())
        .limit(RESULT_LIMIT)
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def delete_document(session: AsyncSession, doc_id: int) -> bool:
    doc = await session.get(Document, doc_id)
    if doc is None:
        return False
    await session.delete(doc)
    await session.commit()

    es = get_es()
    try:
        await es.delete(index=INDEX_NAME, id=str(doc_id))
    except Exception:
        pass

    return True