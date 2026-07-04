# tests/test_search_service.py
import pytest
from datetime import datetime
from app.services.search_service import search_documents, delete_document
from tests.conftest import make_document


@pytest.mark.asyncio
async def test_search_finds_matching_document(session, es_client, monkeypatch):
    monkeypatch.setattr("app.services.search_service.INDEX_NAME", "documents_test")
    doc = await make_document(session, es_client, "кот сидит на подоконнике")

    results = await search_documents(session, "кот")

    assert len(results) == 1
    assert results[0].id == doc.id


@pytest.mark.asyncio
async def test_search_orders_by_created_date_desc(session, es_client, monkeypatch):
    monkeypatch.setattr("app.services.search_service.INDEX_NAME", "documents_test")
    old_doc = await make_document(
        session, es_client, "кот старый пост", created_date=datetime(2020, 1, 1)
    )
    new_doc = await make_document(
        session, es_client, "кот новый пост", created_date=datetime(2024, 1, 1)
    )

    results = await search_documents(session, "кот")

    assert [r.id for r in results] == [new_doc.id, old_doc.id]


@pytest.mark.asyncio
async def test_search_returns_all_db_fields(session, es_client, monkeypatch):
    monkeypatch.setattr("app.services.search_service.INDEX_NAME", "documents_test")
    doc = await make_document(session, es_client, "кот на окне", rubrics=["VK-1", "VK-2"])

    results = await search_documents(session, "кот")

    assert results[0].rubrics == ["VK-1", "VK-2"]
    assert results[0].text == "кот на окне"
    assert results[0].created_date is not None


@pytest.mark.asyncio
async def test_delete_removes_document_from_db_and_search(session, es_client, monkeypatch):
    """Удаление должно вернуть True и убрать документ из обоих хранилищ - БД и ES."""
    monkeypatch.setattr("app.services.search_service.INDEX_NAME", "documents_test")
    doc = await make_document(session, es_client, "кот перед удалением")

    # убедимся, что документ вообще находится до удаления - иначе тест ничего не проверяет
    results_before = await search_documents(session, "кот")
    assert doc.id in [r.id for r in results_before]

    # само удаление
    was_deleted = await delete_document(session, doc.id)
    assert was_deleted is True

    # документ пропал из поиска
    results_after = await search_documents(session, "кот")
    assert doc.id not in [r.id for r in results_after] 