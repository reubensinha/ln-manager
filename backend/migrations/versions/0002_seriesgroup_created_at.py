"""add created_at to seriesgroup

Revision ID: 0002_seriesgroup_created_at
Revises: 0001_baseline
Create Date: 2026-07-04

Adds SeriesGroup.created_at ("date added"). Idempotent: fresh databases already have the
column (the baseline created it from the model), so this only runs on pre-existing rows.
Uses batch mode so SQLite can backfill existing rows with CURRENT_TIMESTAMP.
"""
from alembic import op
import sqlalchemy as sa

revision = "0002_seriesgroup_created_at"
down_revision = "0001_baseline"
branch_labels = None
depends_on = None


def _has_column(bind, table: str, column: str) -> bool:
    return column in [c["name"] for c in sa.inspect(bind).get_columns(table)]


def upgrade() -> None:
    bind = op.get_bind()
    if not _has_column(bind, "seriesgroup", "created_at"):
        with op.batch_alter_table("seriesgroup") as batch_op:
            batch_op.add_column(
                sa.Column(
                    "created_at",
                    sa.DateTime(),
                    nullable=False,
                    server_default=sa.text("CURRENT_TIMESTAMP"),
                )
            )


def downgrade() -> None:
    bind = op.get_bind()
    if _has_column(bind, "seriesgroup", "created_at"):
        with op.batch_alter_table("seriesgroup") as batch_op:
            batch_op.drop_column("created_at")
