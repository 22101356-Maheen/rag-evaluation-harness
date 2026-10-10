"""Add the deterministic Day 10 analysis report.

Revision ID: b20d10000001
Revises: a19d90000001
"""

import sqlalchemy as sa
from alembic import op

revision = "b20d10000001"
down_revision = "a19d90000001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("experiment_runs") as batch:
        batch.add_column(sa.Column("analysis_report", sa.JSON(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("experiment_runs") as batch:
        batch.drop_column("analysis_report")
