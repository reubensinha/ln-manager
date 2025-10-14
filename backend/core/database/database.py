from contextlib import contextmanager
from sqlmodel import SQLModel, create_engine, Session, select

connect_args = {"check_same_thread": False}
engine = create_engine("sqlite:///./lnauto.db", echo=False, connect_args=connect_args)

def init_db():
    SQLModel.metadata.create_all(engine)

# @contextmanager
# def get_session():
#     with Session(engine) as session:
#         yield session


def get_session():
    with Session(engine) as session:
        yield session