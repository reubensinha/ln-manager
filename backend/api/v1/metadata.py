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

class AddSeriesRequest(SQLModel):
    source: str
    external_id: str
    series_group: str | None = None  # optional name of the series group


class AddSeriesResponse(SQLModel):
    success: bool
    message: str


@router.get("/series_details/{source}", response_model=SeriesDetailsResponse)
async def get_series_details(source: str, external_id: str):
    plugin = plugin_manager.get_plugin(source)
    if not plugin or not isinstance(plugin, MetadataPlugin):
        raise HTTPException(status_code=404, detail="Metadata source not found")

    if not external_id:
        raise HTTPException(
            status_code=400, detail="external_id query parameter is required"
        )

    result = await plugin.get_series_by_id(external_id)
    return result


@router.get("/search", response_model=list[SeriesSearchResponse])
async def search_series(query: str, source: str):
    plugin = plugin_manager.get_plugin(source)
    if not plugin or not isinstance(plugin, MetadataPlugin):
        raise HTTPException(status_code=404, detail="Metadata source not found")

    results = await plugin.search_series(query)
    # TODO: Filter out existing series from results
    return results


@router.post("/add/series", response_model=AddSeriesResponse)
async def fetch_series(
    request: AddSeriesRequest,
    session: Session = Depends(get_session),
):
    success = await metadata_service.fetch_series(
        source=request.source,
        external_id=request.external_id,
        series_group=request.series_group,
        session=session,
    )
    if not success:
        raise HTTPException(status_code=500, detail="Failed to add series")

    return {"success": True, "message": "Series added successfully"}

@router.get("/image/{source}/{filepath:path}")  
async def get_image(source: str, filepath: str, request: Request):
    
    # Get the raw, undecoded path from the request scope
    raw_path = request.scope.get("raw_path", b"").decode("utf-8")
    
    # The part of the path we are interested in comes after /image/{source}/
    prefix = f"/api/v1/metadata/image/{source}/"
    if raw_path.startswith(prefix):
        filepath = raw_path[len(prefix):]

    plugin = plugin_manager.get_plugin(source)
    if not plugin or not isinstance(plugin, MetadataPlugin):
        raise HTTPException(status_code=404, detail="Metadata source not found")
    
    # Use the plugin's data directory instead of the plugin code directory
    if not hasattr(plugin, 'data_dir'):
        raise HTTPException(status_code=500, detail="Plugin data directory not configured")
    
    plugin_data_dir = plugin.data_dir
    
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

