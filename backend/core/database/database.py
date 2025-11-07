from contextlib import contextmanager
from pathlib import Path
from sqlmodel import SQLModel, create_engine, Session, select

# Database path relative to backend directory
backend_dir = Path(__file__).parent.parent.parent  # goes from core/database/ up to backend/
db_dir = backend_dir / "config"
db_dir.mkdir(parents=True, exist_ok=True)

connect_args = {"check_same_thread": False}
engine = create_engine(f"sqlite:///{db_dir}/lnauto.db", echo=False, connect_args=connect_args)

def init_db():
    SQLModel.metadata.create_all(engine)

# @contextmanager
# def get_session():
#     with Session(engine) as session:
#         yield session


def get_session():
    with Session(engine) as session:
        yield session