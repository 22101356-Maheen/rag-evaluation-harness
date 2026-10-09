from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.postgres import Base


class EvaluationCase(Base):
    __tablename__ = "evaluation_cases"

    id: Mapped[int] = mapped_column(primary_key=True)
    dataset_id: Mapped[int] = mapped_column(
        ForeignKey("evaluation_datasets.id"), index=True
    )
    question: Mapped[str] = mapped_column(Text)
    reference_answer: Mapped[str] = mapped_column(Text)
    source_evidence: Mapped[list[dict]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
