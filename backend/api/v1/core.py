# TODO: Implement actual logic for these endpoints

from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session, select
from uuid import UUID

# from backend.core.database.plugins import MetadataPlugin, IndexerPlugin
from backend.api.v1.utils import _update_download_status
from backend.core.database.models import *
from backend.core.database.database import get_session
from backend.plugin_manager import plugin_manager
from backend.core.plugins.metadata import MetadataPlugin

router = APIRouter()


@router.get("/collections", response_model=list[CollectionPublicSimple])
async def read_collections(*, session: Session = Depends(get_session)):
    collections = session.exec(select(Collection)).all()
    return collections


@router.get("/collections/{collection_id}", response_model=CollectionPublicWithGroups)
async def read_collection(
    *, session: Session = Depends(get_session), collection_id: UUID
):
    collection = session.get(Collection, collection_id)
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")
    return collection


@router.get("/series-groups", response_model=list[SeriesGroupPublicSimple])
async def read_seriesgroup_list(*, session: Session = Depends(get_session)):
    series_groups = session.exec(select(SeriesGroup)).all()
    return series_groups


@router.get("/series-groups/{group_id}", response_model=SeriesGroupPublicWithSeries)
async def read_series_group(*, session: Session = Depends(get_session), group_id: UUID):
    group = session.get(SeriesGroup, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Series group not found")
    return group


@router.get("/series", response_model=list[SeriesPublicSimple])
async def read_series_list(*, session: Session = Depends(get_session)):
    series = session.exec(select(Series)).all()
    return series


@router.get("/series/{series_id}", response_model=SeriesPublicWithBooks)
async def read_series(*, session: Session = Depends(get_session), series_id: UUID):
    series = session.get(Series, series_id)
    if not series:
        raise HTTPException(status_code=404, detail="Series not found")
    return series


@router.get("/books", response_model=list[BookPublicSimple])
async def read_book_list(*, session: Session = Depends(get_session)):
    books = session.exec(select(Book)).all()
    return books


@router.get("/books/{book_id}", response_model=BookPublicWithReleases)
async def read_book(*, session: Session = Depends(get_session), book_id: UUID):
    book = session.get(Book, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return book

@router.get("/releases", response_model=list[ReleasePublicSimple])
async def read_release_list(*, session: Session = Depends(get_session)):
    releases = session.exec(select(Release)).all()
    return releases

@router.patch("/toggle-book-downloaded/{book_id}", response_model=dict[str, str])
async def toggle_download_status(*, session: Session = Depends(get_session), book_id: UUID):
    book = session.get(Book, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    book.downloaded = not book.downloaded
    session.add(book)
    
    # TODO: Update series download status if needed
    series = session.get(Series, book.series_id)
    if not series:
        # This case should ideally not happen if data integrity is maintained
        raise HTTPException(status_code=404, detail="Series not found for the book")

    _update_download_status(session, series)

    session.commit()
    return {"status": "success"}

@router.patch("/toggle-book-monitored/{book_id}", response_model=dict[str, str])
async def toggle_monitor_status(*, session: Session = Depends(get_session), book_id: UUID):
    book = session.get(Book, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    book.monitored = not book.monitored
    session.add(book)
    session.commit()
    return {"status": "success"}

@router.patch("/toggle-series-downloaded/{series_id}", response_model=dict[str, str])
async def toggle_series_download_status(*, session: Session = Depends(get_session), series_id: UUID):
    series = session.get(Series, series_id)
    if not series:
        raise HTTPException(status_code=404, detail="Series not found")
    # Toggle the downloaded status of all books in the series
    
    target_status = any(not book.downloaded for book in series.books)

    for book in series.books:
        book.downloaded = target_status
        session.add(book)

    _update_download_status(session, series)
        
    session.commit()
    return {"status": "success"}


@router.patch("/toggle-series-monitored/{series_id}", response_model=dict[str, str])
async def toggle_series_monitor_status(*, session: Session = Depends(get_session), series_id: UUID):
    series = session.get(Series, series_id)
    if not series:
        raise HTTPException(status_code=404, detail="Series not found")

    target_status = any(not book.monitored for book in series.books)

    for book in series.books:
        book.monitored = target_status
        session.add(book)
    session.commit()
    return {"status": "success"}
