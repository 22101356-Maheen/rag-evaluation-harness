from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.postgres import Base


# -----------------------------
# Experiment Run Model
# -----------------------------

class ExperimentRun(Base):
    __tablename__ = "experiment_runs"

    # this is the unique ID for every saved experiment run.
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    # this connects the experiment to an existing project.
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id"),
        nullable=False,
    )

    # these fields store the configuration that won the comparison.
    strategy: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    chunk_size: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    chunk_overlap: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    top_k: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    # these fields store the main retrieval evaluation scores.
    hit_at_k: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    precision_at_k: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    recall_at_k: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    mrr: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    evaluation_dataset_id: Mapped[int | None] = mapped_column(
        ForeignKey("evaluation_datasets.id"), nullable=True
    )
    faithfulness: Mapped[float | None] = mapped_column(Float, nullable=True)
    relevance: Mapped[float | None] = mapped_column(Float, nullable=True)
    correctness: Mapped[float | None] = mapped_column(Float, nullable=True)
    hallucination: Mapped[float | None] = mapped_column(Float, nullable=True)
    generation_model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    evaluator_model: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # this stores when the experiment result was saved.
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
