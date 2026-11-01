"""add plugin repositories and plugin provenance

Revision ID: 0005_plugin_repositories
Revises: 0004_plugin_uid
Create Date: 2026-10-31

Adds the `pluginrepository` table (user-added sources of installable plugins, plus their
last fetched catalog) and `plugin.source_repo_id` recording which repository an installed
plugin came from.

`source_repo_id` is ON DELETE SET NULL: removing a repository must not uninstall the
plugins that came from it. There is no companion "source" column - whether a plugin is
bundled is derived from whether it lives in BUNDLED_PLUGIN_DIR, so it cannot drift.

Idempotent: fresh databases already have both (the baseline creates them from the model),
so this only runs on pre-existing rows. Uses batch mode for SQLite.
"""
from alembic import op
import sqlalchemy as sa

revision = "0005_plugin_repositories"
down_revision = "0004_plugin_uid"
branch_labels = None
depends_on = None

# Matches the index create_all generates from PluginRepositoryBase.url's
# Field(index=True, unique=True), so a migrated database matches a fresh one.
URL_INDEX_NAME = "ix_pluginrepository_url"
FK_NAME = "fk_plugin_source_repo_id"


def _has_table(bind, table: str) -> bool:
    return table in sa.inspect(bind).get_table_names()


def _has_column(bind, table: str, column: str) -> bool:
    return column in [c["name"] for c in sa.inspect(bind).get_columns(table)]


def _has_index(bind, table: str, index: str) -> bool:
    return index in [i["name"] for i in sa.inspect(bind).get_indexes(table)]


def upgrade() -> None:
    bind = op.get_bind()

    if not _has_table(bind, "pluginrepository"):
        op.create_table(
            "pluginrepository",
            sa.Column("name", sa.String(), nullable=False),
            sa.Column("url", sa.String(), nullable=False),
            sa.Column("enabled", sa.Boolean(), nullable=False),
            sa.Column("id", sa.Uuid(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("last_refreshed_at", sa.DateTime(), nullable=True),
            sa.Column("last_error", sa.String(), nullable=True),
            sa.Column("catalog", sa.JSON(), nullable=True),
            sa.PrimaryKeyConstraint("id"),
        )
    if not _has_index(bind, "pluginrepository", URL_INDEX_NAME):
        op.create_index(URL_INDEX_NAME, "pluginrepository", ["url"], unique=True)

    # The table must exist before a column can reference it, hence the ordering above.
    if not _has_column(bind, "plugin", "source_repo_id"):
        with op.batch_alter_table("plugin") as batch_op:
            batch_op.add_column(
                sa.Column(
                    "source_repo_id",
                    sa.Uuid(),
                    sa.ForeignKey(
                        "pluginrepository.id",
                        ondelete="SET NULL",
                        # Named explicitly: batch mode recreates the table to add the
                        # column, and SQLAlchemy refuses to render an unnamed constraint
                        # when doing so ("Constraint must have a name"). create_all
                        # leaves it unnamed, so a migrated database differs from a fresh
                        # one in this constraint's name only - the app nulls the column
                        # itself when a repository is removed rather than relying on
                        # SQLite's FK enforcement, which is off by default.
                        name=FK_NAME,
                    ),
                    nullable=True,
                )
            )


def downgrade() -> None:
    bind = op.get_bind()

    if _has_column(bind, "plugin", "source_repo_id"):
        with op.batch_alter_table("plugin") as batch_op:
            batch_op.drop_column("source_repo_id")

    if _has_index(bind, "pluginrepository", URL_INDEX_NAME):
        op.drop_index(URL_INDEX_NAME, table_name="pluginrepository")
    if _has_table(bind, "pluginrepository"):
        op.drop_table("pluginrepository")
