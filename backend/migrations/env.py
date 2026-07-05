"""Alembic environment.

Reuses the application's SQLAlchemy engine and SQLModel metadata so migrations always
target the same database the app uses. Works both from the CLI (`uv run alembic ...`)
and programmatically from `init_db()`.
"""
import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlmodel import SQLModel

# Make the `backend` package importable when run via the Alembic CLI from backend/.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.core.database import models  # noqa: E402,F401  (registers all tables)
from backend.core.database.database import engine  # noqa: E402

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = SQLModel.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=str(engine.url),
        target_metadata=target_metadata,
        literal_binds=True,
        render_as_batch=True,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    with engine.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=True,  # SQLite needs batch mode for ALTER TABLE
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
