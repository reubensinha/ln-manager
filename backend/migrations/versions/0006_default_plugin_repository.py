"""seed the default plugin repository

Revision ID: 0006_default_plugin_repository
Revises: 0005_plugin_repositories
Create Date: 2026-11-01

Inserts the repository every install starts with, so a fresh install can browse and
install plugins without being told to go and find a URL first.

Seeding here rather than at startup is what makes the row the user's to keep or discard:
a migration runs exactly once per database, so removing the repository in the UI is
permanent, while a startup check would re-add it on the next boot. The restore flow
rebuilds the schema through migrations, so a restored database is seeded again - correct,
since it is a new database.

The row is written without a catalog. Migrations must not do network I/O, so startup
fetches the index for any repository that has never been refreshed; until that succeeds
the repository is listed with nothing on offer, and a failure is reported on the row the
same way a failed manual refresh is.

Idempotent, and skipped when the URL is already present - an install that added this
repository by hand before upgrading must not end up with it twice, and `url` is unique.
"""
import uuid
from datetime import datetime

import sqlalchemy as sa
from alembic import op

from backend.core.constants import (
    DEFAULT_PLUGIN_REPOSITORY_NAME,
    DEFAULT_PLUGIN_REPOSITORY_URL,
)

revision = "0006_default_plugin_repository"
down_revision = "0005_plugin_repositories"
branch_labels = None
depends_on = None

# Named rather than reflected: this migration only touches columns 0005 created, and
# reflecting the live table would make it follow later schema changes.
repository = sa.table(
    "pluginrepository",
    sa.column("id", sa.Uuid()),
    sa.column("name", sa.String()),
    sa.column("url", sa.String()),
    sa.column("enabled", sa.Boolean()),
    sa.column("created_at", sa.DateTime()),
    sa.column("last_error", sa.String()),
    sa.column("catalog", sa.JSON()),
)


def upgrade() -> None:
    bind = op.get_bind()
    existing = bind.execute(
        sa.select(repository.c.id).where(
            repository.c.url == DEFAULT_PLUGIN_REPOSITORY_URL
        )
    ).first()
    if existing is not None:
        return

    op.bulk_insert(
        repository,
        [
            {
                "id": uuid.uuid4(),
                "name": DEFAULT_PLUGIN_REPOSITORY_NAME,
                "url": DEFAULT_PLUGIN_REPOSITORY_URL,
                "enabled": True,
                "created_at": datetime.utcnow(),
            }
        ],
    )


def downgrade() -> None:
    bind = op.get_bind()
    # Only the untouched seed is removed. A row carrying a catalog, an error or a
    # changed name has been used or edited since, and discarding that on a downgrade
    # would lose the user's own state.
    bind.execute(
        sa.delete(repository).where(
            repository.c.url == DEFAULT_PLUGIN_REPOSITORY_URL,
            repository.c.name == DEFAULT_PLUGIN_REPOSITORY_NAME,
            repository.c.catalog.is_(None),
            repository.c.last_error.is_(None),
        )
    )
