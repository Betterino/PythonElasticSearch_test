from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class DocumentOut(BaseModel):
    id: int = Field(..., description="Уникальный идентификатор документа")
    rubrics: list[str] = Field(..., description="Список рубрик документа")
    text: str = Field(..., description="Текст документа")
    created_date: datetime = Field(..., description="Дата создания документа")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 42,
                "rubrics": ["VK-1603736028819866", "VK-11879320040"],
                "text": "кот сидит на подоконнике",
                "created_date": "2024-01-15T12:30:00",
            }
        },
    )