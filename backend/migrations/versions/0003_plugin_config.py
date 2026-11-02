"""add config to plugin

Revision ID: 0003_plugin_config
Revises: 0002_seriesgroup_created_at
Create Date: 2026-09-24

Adds Plugin.config, the JSON blob holding plugin-wide user settings. Idempotent: fresh
databases already have the column (the baseline creates it from the model), so this only
runs on pre-existing rows. Uses batch mode for SQLite.
"""
from alembic import op
import sqlalchemy as sa

revision = "0003_plugin_config"
down_revision = "0002_seriesgroup_created_at"
branch_labels = None
depends_on = None


def _has_column(bind, table: str, column: str) -> bool:
    return column in [c["name"] for c in sa.inspect(bind).get_columns(table)]


def upgrade() -> None:
    bind = op.get_bind()
    if not _has_column(bind, "plugin", "config"):
        with op.batch_alter_table("plugin") as batch_op:
            batch_op.add_column(sa.Column("config", sa.JSON(), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    if _has_column(bind, "plugin", "config"):
        with op.batch_alter_table("plugin") as batch_op:
            batch_op.drop_column("config")
