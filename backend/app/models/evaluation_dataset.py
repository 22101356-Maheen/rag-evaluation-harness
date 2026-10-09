from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.postgres import Base


class EvaluationDataset(Base):
    __tablename__ = "evaluation_datasets"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), index=True)
    mode: Mapped[str] = mapped_column(String(20))
    corpus_fingerprint: Mapped[str] = mapped_column(String(64))
    cache_key: Mapped[str] = mapped_column(String(64), unique=True)
    generator_model: Mapped[str] = mapped_column(String(100))
    prompt_version: Mapped[str] = mapped_column(String(100))
    case_count: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
