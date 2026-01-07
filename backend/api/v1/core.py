import asyncio
from typing import Any

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


@router.get("/plugin-capabilities")
async def get_plugin_capabilities(*, session: Session = Depends(get_session)):
    """Get a summary of what capabilities are available from enabled plugins."""
    plugins = session.exec(select(Plugin).where(Plugin.enabled == True)).all()
    
    capabilities = {
        "has_indexers": False,
        "has_download_clients": False,
        "has_metadata_sources": False,
        "has_parsers": False,
    }
    
    for plugin in plugins:
        try:
            plugin_instance = plugin_manager.get_plugin(plugin.name)
            if plugin_instance:
                # Check for indexer capability
                try:
                    indexers = plugin_instance.get_available_indexers()
                    if indexers:
                        capabilities["has_indexers"] = True
                except (NotImplementedError, AttributeError):
                    pass
                
                # Check for download client capability
                try:
                    clients = plugin_instance.get_available_clients()
                    if clients:
                        capabilities["has_download_clients"] = True
                except (NotImplementedError, AttributeError):
                    pass
                
                # Check for metadata source capability
                try:
                    sources = plugin_instance.get_available_sources()
                    if sources:
                        capabilities["has_metadata_sources"] = True
                except (NotImplementedError, AttributeError):
                    pass
                
                # Check for parser capability
                try:
                    parsers = plugin_instance.get_available_parsers()
                    if parsers:
                        capabilities["has_parsers"] = True
                except (NotImplementedError, AttributeError):
                    pass
        except Exception:
            pass
    
    return capabilities


@router.post("/install-plugin", response_model=dict[str, str])
async def install_plugin(*, file: UploadFile, session: Session = Depends(get_session)):
    return await _install_plugin_util(file, session)

@router.delete("/plugins/{plugin_id}", response_model=dict[str, str])
async def uninstall_plugin(*, plugin_id: UUID, session: Session = Depends(get_session)):
    return await _uninstall_plugin_util(plugin_id, session)


@router.get("/indexers", response_model=list[IndexerPublic])
async def list_indexers(*, session: Session = Depends(get_session)):
    """Get all configured indexers."""
    indexers = session.exec(select(Indexer)).all()
    return indexers


@router.post("/indexers/test-connection")
async def test_indexer_connection(*, config: dict[str, Any], session: Session = Depends(get_session)):
    """Test connection to an indexer without saving it.
    
    Args:
        config: Indexer configuration including plugin_id, url, api_key, etc.
    
    Returns:
        Dictionary with success status and message
    """
    try:
        plugin_id = config.get("plugin_id")
        if not plugin_id:
            return {"success": False, "message": "plugin_id is required"}
        
        # Get the plugin
        plugin = session.get(Plugin, UUID(plugin_id))
        if not plugin:
            return {"success": False, "message": "Plugin not found"}
        
        # Get the plugin instance
        plugin_instance = plugin_manager.get_plugin(plugin.name)
        if not plugin_instance:
            return {"success": False, "message": "Plugin instance not found"}
        
        # Create a temporary indexer instance to test
        try:
            indexer_instance = plugin_instance.create_indexer(config.get("config", {}))
            
            # Test the connection
            connection_ok = await indexer_instance.connect()
            
            if connection_ok:
                return {"success": True, "message": "Connection successful!"}
            else:
                return {"success": False, "message": "Connection failed - unable to reach indexer"}
        except Exception as e:
            return {"success": False, "message": f"Connection test failed: {str(e)}"}
    except Exception as e:
        return {"success": False, "message": f"Error testing connection: {str(e)}"}


@router.post("/indexers", response_model=IndexerPublic)
async def create_indexer(*, session: Session = Depends(get_session), indexer: IndexerBase):
    """Create a new indexer instance."""
    db_indexer = Indexer.model_validate(indexer)
    session.add(db_indexer)
    session.commit()
    session.refresh(db_indexer)
    return db_indexer


@router.patch("/indexers/{indexer_id}", response_model=IndexerPublic)
async def update_indexer(
    *, session: Session = Depends(get_session), indexer_id: UUID, indexer: IndexerBase
):
    """Update an existing indexer instance."""
    db_indexer = session.get(Indexer, indexer_id)
    if not db_indexer:
        raise HTTPException(status_code=404, detail="Indexer not found")
    
    indexer_data = indexer.model_dump(exclude_unset=True)
    db_indexer.sqlmodel_update(indexer_data)
    session.add(db_indexer)
    session.commit()
    session.refresh(db_indexer)
    return db_indexer


@router.delete("/indexers/{indexer_id}", response_model=dict[str, str])
async def delete_indexer(*, session: Session = Depends(get_session), indexer_id: UUID):
    """Delete an indexer instance."""
    db_indexer = session.get(Indexer, indexer_id)
    if not db_indexer:
        raise HTTPException(status_code=404, detail="Indexer not found")
    
    session.delete(db_indexer)
    session.commit()
    return {"success": "true", "message": "Indexer deleted successfully"}


@router.get("/download-clients", response_model=list[DownloadClientPublic])
async def list_download_clients(*, session: Session = Depends(get_session)):
    """Get all configured download clients."""
    clients = session.exec(select(DownloadClient)).all()
    return clients

