# TODO: Implement actual logic for these endpoints

from unittest import result
from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import SQLModel, create_engine, Session, select

# from backend.core.database.plugins import MetadataPlugin, IndexerPlugin
from backend.core.database.models import *
from backend.core.database.database import get_session
from backend.plugin_manager import plugin_manager
from backend.core.plugins.metadata import MetadataPlugin

router = APIRouter()

@router.get("/collections/", response_model=list[CollectionPublic])
async def read_collections(*, session: Session = Depends(get_session)):
    collections = session.exec(select(Collection)).all()
    return collections

@router.get("/collections/{collection_id}", response_model=CollectionPublic)
async def read_collection(*, session: Session = Depends(get_session), collection_id: int):
    collection = session.get(Collection, collection_id)
    return collection


@router.get("/series-groups/", response_model=list[SeriesGroupPublic])
async def read_seriesgroup_list(*, session: Session = Depends(get_session)):
    series_groups = session.exec(select(SeriesGroup)).all()
    return series_groups

@router.get("/series-groups/{group_id}", response_model=SeriesGroupPublic)
async def read_series_group(*, session: Session = Depends(get_session), group_id: int):
    group = session.get(SeriesGroup, group_id)
    return group

@router.get("/series/", response_model=list[SeriesPublic])
async def read_series_list(*, session: Session = Depends(get_session)):
    series = session.exec(select(Series)).all()
    return series

@router.get("/series/{series_id}", response_model=SeriesPublic)
async def read_series(*, session: Session = Depends(get_session), series_id: int):
    series = session.get(Series, series_id)
    return series


@router.get("/books/", response_model=list[BookPublic])
async def read_book_list(*, session: Session = Depends(get_session)):
    books = session.exec(select(Book)).all()
    return books

@router.get("/books/{book_id}", response_model=BookPublic)
async def read_book(*, session: Session = Depends(get_session), book_id: int):
    book = session.get(Book, book_id)
    return book

