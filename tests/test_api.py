import pytest
from tests.conftest import make_document


@pytest.mark.asyncio
async def test_search_endpoint_returns_200_and_matches(client, session, es_client, monkeypatch):
    monkeypatch.setattr("app.services.search_service.INDEX_NAME", "documents_test")
    await make_document(session, es_client, "уникальный_тестовый_текст_xyz")

    response = await client.get("/search", params={"q": "уникальный_тестовый_текст_xyz"})

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["text"] == "уникальный_тестовый_текст_xyz"

@pytest.mark.asyncio
async def test_delete_endpoint_nonexistent_document_returns_404(client):
    response = await client.delete("/documents/999999")
    assert response.status_code == 404