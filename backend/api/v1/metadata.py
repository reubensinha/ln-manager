import asyncio
from pathlib import Path
from urllib.parse import unquote
from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import FileResponse
from sqlmodel import SQLModel, Session, select
import uuid

# from backend.core.database.plugins import MetadataPlugin, IndexerPlugin
from backend.core.database.models import *
from backend.core.database.database import get_session
from backend.core.plugins.metadata import MetadataPlugin, SeriesFetchModel
from backend.core.services import metadata_service
from backend.plugin_manager import plugin_manager

router = APIRouter()


@router.get("/sources", response_model=list[MetadataSourcePublic])
async def get_metadata_sources(session: Session = Depends(get_session)):
    """Get all metadata sources from database.
    
    Returns:
        List of all MetadataSource instances
    """
    sources = session.exec(select(MetadataSource)).all()
    return sources


class AddSeriesRequest(SQLModel):
    source_id: str  # UUID of MetadataSource
    external_id: str
    series_group: str | None = None  # optional UUID of the series group


class AddSeriesResponse(SQLModel):
    success: bool
    message: str


@router.get("/series_details", response_model=SeriesDetailsResponse)
async def get_series_details(source_id: str, external_id: str, session: Session = Depends(get_session)):
    """Get series details from a metadata source.
    
    Args:
        source_id: UUID of MetadataSource
        external_id: External series ID
    """
    return await metadata_service.get_series_details(source_id, external_id, session)


@router.get("/search", response_model=list[SeriesSearchResponse])
async def search_series(query: str, source_id: str, session: Session = Depends(get_session)):
    """Search for series using a metadata source.
    
    Args:
        query: Search query
        source_id: UUID of MetadataSource
    """
    return await metadata_service.search_series(query, source_id, session)


@router.post("/add/series", response_model=AddSeriesResponse)
async def fetch_series(
    request: AddSeriesRequest,
    session: Session = Depends(get_session),
):
    """Add a series to the library from a metadata source.
    
    Args:
        request: Contains source_id (UUID), external_id, and optional series_group UUID
    """
    success = await metadata_service.fetch_series(
        source_id=request.source_id,
        external_id=request.external_id,
        series_group=request.series_group,
        session=session,
    )
    if not success:
        raise HTTPException(status_code=500, detail="Failed to add series")
    
    return AddSeriesResponse(success=True, message="Series added successfully")

@router.get("/image/{plugin_name}/{source_name}/{filepath:path}")  
async def get_image(plugin_name: str, source_name: str, filepath: str, request: Request, session: Session = Depends(get_session)):
    """Get an image from a metadata source's data directory.
    
    Args:
        plugin_name: Name of the plugin
        source_name: Name of the metadata source
        filepath: Path to the image file
    """
    
    # Get the raw, undecoded path from the request scope
    raw_path = request.scope.get("raw_path", b"").decode("utf-8")
    
    # The part of the path we are interested in comes after /image/{plugin_name}/{source_name}/
    prefix = f"/api/v1/image/{plugin_name}/{source_name}/"
    if raw_path.startswith(prefix):
        filepath = raw_path[len(prefix):]

    # Query the metadata source by plugin name and source name
    statement = (
        select(MetadataSource)
        .join(Plugin)
        .where(Plugin.name == plugin_name, MetadataSource.name == source_name)
    )
    metadata_source = session.exec(statement).first()
    
    if not metadata_source or not metadata_source.enabled:
        raise HTTPException(status_code=404, detail="Metadata source not found")
    
    if not metadata_source.plugin:
        raise HTTPException(status_code=404, detail="Plugin for metadata source not found")

    # Get the plugin instance and create a configured source
    plugin = plugin_manager.get_plugin(metadata_source.plugin.name)
    if not plugin:
        raise HTTPException(status_code=404, detail="Plugin not found")
    
    source_instance = None
    try:
        # Use plugin's factory method to create configured source
        source_instance = plugin.create_metadata_source(metadata_source.config or {})
        if not isinstance(source_instance, MetadataPlugin):
            raise HTTPException(status_code=404, detail="Metadata plugin not found")
        
        # Use the plugin's data directory
        if not hasattr(source_instance, 'data_dir'):
            raise HTTPException(status_code=500, detail="Plugin data directory not configured")
        
        plugin_data_dir = source_instance.data_dir
        
        # The filepath is URL-encoded, so we need to decode it for filesystem access
        decoded_filepath = unquote(filepath)
        
        img_path = plugin_data_dir / decoded_filepath

        if not img_path.exists():
            raise HTTPException(status_code=404, detail="File not found")
        
        if not img_path.is_file():
            raise HTTPException(status_code=400, detail="Not a file")
        
        try:
            img_path.resolve().relative_to(plugin_data_dir.resolve())
        except ValueError:
            raise HTTPException(status_code=403, detail="Access denied")

        return FileResponse(img_path)
    finally:
        # Clean up plugin instance
        if source_instance and hasattr(source_instance, 'stop'):
            source_instance.stop()

