"""add uid to plugin

Revision ID: 0004_plugin_uid
Revises: 0003_plugin_config
Create Date: 2026-10-31

Adds Plugin.uid, the stable globally-unique id a plugin declares in its manifest. Used to
identify the same plugin across repositories and reinstalls, where `name` is only a
display label. Idempotent: fresh databases already have the column and index (the
baseline creates them from the model), so this only runs on pre-existing rows. Uses batch
mode for SQLite.

The column is left NULL here rather than backfilled. Startup reconciliation matches a
manifest's uid first and falls back to `name`, writing the uid onto the existing row -
that path has to exist anyway for plugins added later, so duplicating it in SQL would
mean two implementations of the same rule.
"""
from alembic import op
import sqlalchemy as sa

revision = "0004_plugin_uid"
down_revision = "0003_plugin_config"
branch_labels = None
depends_on = None

# Matches what SQLModel's Field(index=True, unique=True) generates via create_all, so a
# migrated database ends up identical to a freshly created one.
INDEX_NAME = "ix_plugin_uid"


def _has_column(bind, table: str, column: str) -> bool:
    return column in [c["name"] for c in sa.inspect(bind).get_columns(table)]


def _has_index(bind, table: str, index: str) -> bool:
    return index in [i["name"] for i in sa.inspect(bind).get_indexes(table)]


def upgrade() -> None:
    bind = op.get_bind()
    if not _has_column(bind, "plugin", "uid"):
        with op.batch_alter_table("plugin") as batch_op:
            batch_op.add_column(sa.Column("uid", sa.String(), nullable=True))
    if not _has_index(bind, "plugin", INDEX_NAME):
        op.create_index(INDEX_NAME, "plugin", ["uid"], unique=True)


def downgrade() -> None:
    bind = op.get_bind()
    if _has_index(bind, "plugin", INDEX_NAME):
        op.drop_index(INDEX_NAME, table_name="plugin")
    if _has_column(bind, "plugin", "uid"):
        with op.batch_alter_table("plugin") as batch_op:
            batch_op.drop_column("uid")
