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
    SQLModel.metadata.create_all(engine)
    logger.info("Database initialized successfully")


# @contextmanager
# def get_session():
#     with Session(engine) as session:
#         yield session


def get_session():
    with Session(engine) as session:
        yield session
