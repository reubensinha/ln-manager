"""baseline schema

Revision ID: 0001_baseline
Revises:
Create Date: 2026-07-04

Baseline revision for the pre-Alembic schema. Fresh databases run this to create the
full current schema from the SQLModel metadata. Databases that already exist (created via
`SQLModel.metadata.create_all` before Alembic was introduced) are *stamped* at this
revision instead of running it, so their tables are not recreated.
"""
from alembic import op
from sqlmodel import SQLModel

import backend.core.database.models  # noqa: F401  (registers all tables on the metadata)

revision = "0001_baseline"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    SQLModel.metadata.create_all(op.get_bind())


def downgrade() -> None:
    SQLModel.metadata.drop_all(op.get_bind())
