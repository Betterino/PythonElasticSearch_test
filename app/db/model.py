from sqlalchemy import String, Text, DateTime, ARRAY
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from app.db.session import Base

class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    rubrics: Mapped[list[str]] = mapped_column(ARRAY(String))
    text: Mapped[str] = mapped_column(Text)
    created_date: Mapped[datetime] = mapped_column(DateTime)