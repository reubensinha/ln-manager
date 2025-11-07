from contextlib import contextmanager
from pathlib import Path
from sqlmodel import SQLModel, create_engine, Session, select

# Ensure the config directory exists before creating the database
db_path = Path("./config")
db_path.mkdir(parents=True, exist_ok=True)

connect_args = {"check_same_thread": False}
engine = create_engine("sqlite:///./config/lnauto.db", echo=False, connect_args=connect_args)

def init_db():
    SQLModel.metadata.create_all(engine)

# @contextmanager
# def get_session():
#     with Session(engine) as session:
#         yield session


def get_session():
    with Session(engine) as session:
        yield session