import asyncio

from fastapi import APIRouter, HTTPException, Depends, UploadFile
from sqlmodel import Session, select
from uuid import UUID

# from backend.core.database.plugins import MetadataPlugin, IndexerPlugin
from backend.api.v1.utils import _install_plugin_util, _uninstall_plugin_util
from backend.core.database.models import *
from backend.core.database.database import get_session
from backend.plugin_manager import plugin_manager
from backend.core.plugins.metadata import MetadataPlugin
from backend.core.services import library_service
from backend.core.exceptions import ResourceNotFoundError, InvalidStateError, ValidationError

router = APIRouter()


@router.get("/collections", response_model=list[CollectionPublicSimple])
async def read_collections(*, session: Session = Depends(get_session)):
    return library_service.get_all_collections(session)


@router.get("/collections/{collection_id}", response_model=CollectionPublicWithGroups)
async def read_collection(
    *, session: Session = Depends(get_session), collection_id: UUID
):
    return library_service.get_collection_by_id(session, collection_id)


@router.get("/series-groups", response_model=list[SeriesGroupPublicSimple])
async def read_seriesgroup_list(*, session: Session = Depends(get_session)):
    return library_service.get_all_series_groups(session)


@router.get("/series-groups/{group_id}", response_model=SeriesGroupPublicWithSeries)
async def read_series_group(*, session: Session = Depends(get_session), group_id: UUID):
    return library_service.get_series_group_by_id(session, group_id)


@router.get("/series", response_model=list[SeriesPublicSimple])
async def read_series_list(*, session: Session = Depends(get_session)):
    return library_service.get_all_series(session)


@router.get("/series/{series_id}", response_model=SeriesPublicWithBooks)
async def read_series(*, session: Session = Depends(get_session), series_id: UUID):
    return library_service.get_series_by_id(session, series_id)


@router.get("/books", response_model=list[BookPublicSimple])
async def read_book_list(*, session: Session = Depends(get_session)):
    return library_service.get_all_books(session)


@router.get("/books/{book_id}", response_model=BookPublicWithReleases)
async def read_book(*, session: Session = Depends(get_session), book_id: UUID):
    return library_service.get_book_by_id(session, book_id)


@router.get("/releases", response_model=list[ReleasePublicSimple])
async def read_release_list(*, session: Session = Depends(get_session)):
    return library_service.get_all_releases(session)


@router.patch("/toggle-book-downloaded/{book_id}", response_model=dict[str, str])
async def toggle_download_status(
    *, session: Session = Depends(get_session), book_id: UUID
):
    return library_service.toggle_book_downloaded(session, book_id)

@router.patch("/set-book-downloaded/{book_id}", response_model=dict[str, str])
async def set_download_status(
    *, session: Session = Depends(get_session), book_id: UUID, downloaded: bool
):
    return library_service.set_book_downloaded(session, book_id, downloaded)


@router.patch("/toggle-book-monitored/{book_id}", response_model=dict[str, str])
async def toggle_monitor_status(
    *, session: Session = Depends(get_session), book_id: UUID
):
    return library_service.toggle_book_monitored(session, book_id)


@router.patch("/toggle-series-downloaded/{series_id}", response_model=dict[str, str])
async def toggle_series_download_status(
    *, session: Session = Depends(get_session), series_id: UUID
):
    return library_service.toggle_series_downloaded(session, series_id)


@router.patch("/toggle-series-monitored/{series_id}", response_model=dict[str, str])
async def toggle_series_monitor_status(
    *, session: Session = Depends(get_session), series_id: UUID
):
    return library_service.toggle_series_monitored(session, series_id)

@router.get("/plugins", response_model=list[PluginPublic])
async def list_plugins(*, session: Session = Depends(get_session)):
    plugins = session.exec(select(Plugin)).all()
    return plugins

@router.post("/install-plugin", response_model=dict[str, str])
async def install_plugin(*, file: UploadFile, session: Session = Depends(get_session)):
    return await _install_plugin_util(file, session)

@router.delete("/plugins/{plugin_id}", response_model=dict[str, str])
async def uninstall_plugin(*, plugin_id: UUID, session: Session = Depends(get_session)):
    return await _uninstall_plugin_util(plugin_id, session)

