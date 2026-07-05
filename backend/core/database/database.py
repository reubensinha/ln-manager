import logging
from contextlib import contextmanager
from pathlib import Path
from sqlmodel import SQLModel, create_engine, Session, select

from backend.core.logging_config import get_logger


logger = get_logger(__name__)

# Database path relative to backend directory
# TODO: Move to constants.py
backend_dir = Path(
    __file__
).parent.parent.parent  # goes from core/database/ up to backend/
db_dir = backend_dir / "config"
db_dir.mkdir(parents=True, exist_ok=True)

db_path = db_dir / "lnauto.db"
connect_args = {"check_same_thread": False}
engine = create_engine(
    f"sqlite:///{db_path}", echo=False, connect_args=connect_args
)


def init_db():
    logger.info(f"Initializing database at: {db_path}")
    _run_migrations()
    logger.info("Database initialized successfully")


def _run_migrations():
    """Bring the database schema up to date via Alembic.

    Handles three cases:
    - brand-new DB: migrations create the whole schema (baseline) + apply the rest;
    - pre-Alembic DB (created by the old create_all): stamp it at the baseline so its
      existing tables aren't recreated, then apply newer migrations;
    - already-migrated DB: no-op.
    """
    from alembic import command
    from alembic.config import Config
    from sqlalchemy import inspect

    cfg = Config()
    cfg.set_main_option("script_location", str(backend_dir / "migrations"))

    tables = set(inspect(engine).get_table_names())
    if "alembic_version" not in tables and "seriesgroup" in tables:
        logger.info("Pre-Alembic database detected; stamping baseline revision")
        command.stamp(cfg, "0001_baseline")

    command.upgrade(cfg, "head")


# @contextmanager
# def get_session():
#     with Session(engine) as session:
#         yield session


def get_session():
    with Session(engine) as session:
        yield session
