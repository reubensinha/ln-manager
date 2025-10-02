from click import group
from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import SQLModel, create_engine, Session, select

# from backend.core.database.plugins import MetadataPlugin, IndexerPlugin
from backend.plugin_manager import plugin_manager
from backend.core.database.models import *

from backend.core.database.database import get_session
from backend.core.plugins.metadata import MetadataPlugin, SeriesFetchModel

router = APIRouter()

@router.get("/search", response_model=list[SeriesPublic])
async def search_series(query: str, source: str):
    # TODO: Determine response model
    plugin = plugin_manager.get_plugin(source)
    if not plugin or not isinstance(plugin, MetadataPlugin):
        raise HTTPException(status_code=404, detail="Metadata source not found")

    results = await plugin.search_series(query)
    # TODO: Filter out existing series from results
    return results

# TODO: Check if this is the correct HTTP method to use.
@router.get("/add/series/{external_id}", response_model=SeriesPublic)
async def fetch_series(external_id: str, source: str, series_group: str = "", session: Session = Depends(get_session)):
    #  TODO: Add series to database.
    
    # ----- Lookup Plugin -----
    plugin = plugin_manager.get_plugin(source)
    if not plugin or not isinstance(plugin, MetadataPlugin):
        raise HTTPException(status_code=404, detail="Metadata source not found")

    # ----- Fetch From Plugin-----
    series_data = await plugin.fetch_series(external_id)
    if not series_data or not series_data.series:
        raise HTTPException(status_code=404, detail=f"{source} Could not find series with id {external_id}")
    
    
    # ----- Handle Series Group -----
    if series_group:
        group = session.get(SeriesGroup, uuid.UUID(series_group))
        if not group:
            raise HTTPException(status_code=404, detail=f"Series group {series_group} not found")
    
    else:
        group = SeriesGroup(title=series_data.series.title)
        session.add(group)
        session.flush()  # To get the ID of the new group
    
    # ----- Lookup Plugin in Database -----
    db_plugin = session.exec(
        select(MetadataPluginTable).where(MetadataPluginTable.name == source)
    ).first()
    if not db_plugin:
        raise HTTPException(status_code=404, detail=f"Metadata source {source} not found in database")
    
    
    # ----- Add Series -----
    series_obj = series_data.series
    series_obj.group_id = group.id
    series_obj.source_id = db_plugin.id
    session.add(series_obj)
    session.flush()
    
    
    # ----- Add Books -----
    for book in series_data.books:
        book.series_id = series_obj.id
        session.add(book)
        session.flush()
        
        for release in series_data.releases:
            if release.book_id == book.id:
                release.series_id = series_obj.id
                release.book_id = book.id
                session.add(release)
    
    # ----- Add Chapters -----
    for chapter in series_data.chapters:
        chapter.series_id = series_obj.id
        session.add(chapter)
        session.flush()
        
        for release in series_data.releases:
            if release.chapter_id == chapter.id:
                release.series_id = series_obj.id
                release.chapter_id = chapter.id
                session.add(release)
    
    
    session.commit()
    session.refresh(series_obj)
    
    return series_obj
