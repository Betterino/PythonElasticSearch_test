from fastapi import APIRouter, Depends, HTTPException,Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.services import search_service
from app.schemas.document import DocumentOut

router = APIRouter()

@router.get(
    "/search",
    response_model=list[DocumentOut],
    summary="Поиск документов по постам",
    description=(
        "Ищет документы, текст которых соответствует запросу. "
        "Возвращает не более 20 документов, отсортированных по дате создания (сначала новые)."
    ),
)
async def search(
    q: str = Query(..., description="Текстовый поисковый запрос", min_length=1),
    session: AsyncSession = Depends(get_db),
):
    return await search_service.search_documents(session, q)

@router.delete(
    "/documents/{doc_id}",
    summary="Удалить документ",
    description="Удаляет документ по id одновременно из БД и поискового индекса.",
    responses={404: {"description": "Документ с указанным id не найден"}},
)
async def delete(doc_id: int, session: AsyncSession = Depends(get_db)):
    ok = await search_service.delete_document(session, doc_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"status": "deleted"}