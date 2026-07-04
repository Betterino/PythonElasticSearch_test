import argparse
import asyncio
import csv
from ast import literal_eval
from datetime import datetime

from elasticsearch import AsyncElasticsearch
from elasticsearch.helpers import async_bulk
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.db.model import Document
from app.es.client import INDEX_NAME, ensure_index

BATCH_SIZE = 200


def parse_rubrics(raw: str) -> list[str]:
    if not raw or not raw.strip():
        return []
    try:
        value = literal_eval(raw)
    except (ValueError, SyntaxError):
        return []
    if isinstance(value, list):
        return [str(x) for x in value]
    return []


def parse_date(raw: str) -> datetime:
    return datetime.fromisoformat(raw)


def read_rows(csv_path: str):
    with open(csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            yield {
                "text": row["text"],
                "created_date": parse_date(row["created_date"]),
                "rubrics": parse_rubrics(row["rubrics"]),
            }


async def import_csv(csv_path: str, db_url: str, es_url: str):
    engine = create_async_engine(db_url)
    session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    es = AsyncElasticsearch(es_url)

    await ensure_index()

    rows = list(read_rows(csv_path))
    print(f"Прочитано {len(rows)} строк из {csv_path}")

    total_inserted = 0

    async with session_factory() as session:
        for i in range(0, len(rows), BATCH_SIZE):
            batch = rows[i : i + BATCH_SIZE]
            
            documents = [Document(**row) for row in batch]
            session.add_all(documents)
            await session.flush()
            
            es_actions = [
                {
                    "_index": INDEX_NAME,
                    "_id": str(doc.id),
                    "_source": {"id": doc.id, "text": doc.text},
                }
                for doc in documents
            ]
            await async_bulk(es, es_actions)

            await session.commit()
            total_inserted += len(batch)
            print(f"  Импортировано {total_inserted}/{len(rows)}")

    await es.close()
    await engine.dispose()
    print("Готово.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Импорт CSV в Postgres и Elasticsearch")
    parser.add_argument("csv_path", help="путь до CSV файла")
    parser.add_argument("--db-url", default=settings.database_url)
    parser.add_argument("--es-url", default=settings.elasticsearch_url)
    args = parser.parse_args()

    asyncio.run(import_csv(args.csv_path, args.db_url, args.es_url))