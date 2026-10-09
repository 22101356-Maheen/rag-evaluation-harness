"""Add reusable evaluation datasets and nullable answer scores.

Revision ID: a19d90000001
Revises: ef4fefd98f39
"""

import sqlalchemy as sa
from alembic import op

revision = "a19d90000001"
down_revision = "ef4fefd98f39"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "evaluation_datasets",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("mode", sa.String(20), nullable=False),
        sa.Column("corpus_fingerprint", sa.String(64), nullable=False),
        sa.Column("cache_key", sa.String(64), nullable=False, unique=True),
        sa.Column("generator_model", sa.String(100), nullable=False),
        sa.Column("prompt_version", sa.String(100), nullable=False),
        sa.Column("case_count", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_evaluation_datasets_project_id", "evaluation_datasets", ["project_id"])
    op.create_table(
        "evaluation_cases",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("dataset_id", sa.Integer(), sa.ForeignKey("evaluation_datasets.id"), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("reference_answer", sa.Text(), nullable=False),
        sa.Column("source_evidence", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_evaluation_cases_dataset_id", "evaluation_cases", ["dataset_id"])
    with op.batch_alter_table("experiment_runs") as batch:
        batch.add_column(sa.Column("evaluation_dataset_id", sa.Integer(), nullable=True))
        batch.create_foreign_key(
            "fk_experiment_runs_evaluation_dataset", "evaluation_datasets",
            ["evaluation_dataset_id"], ["id"],
        )
        for name in ("faithfulness", "relevance", "correctness", "hallucination"):
            batch.add_column(sa.Column(name, sa.Float(), nullable=True))
        for name in ("generation_model", "evaluator_model"):
            batch.add_column(sa.Column(name, sa.String(100), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("experiment_runs") as batch:
        batch.drop_constraint("fk_experiment_runs_evaluation_dataset", type_="foreignkey")
        for name in (
            "evaluation_dataset_id", "faithfulness", "relevance", "correctness",
            "hallucination", "generation_model", "evaluator_model",
        ):
            batch.drop_column(name)
    op.drop_table("evaluation_cases")
    op.drop_table("evaluation_datasets")
