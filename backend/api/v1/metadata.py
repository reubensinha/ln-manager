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



class AddSeriesRequest(SQLModel):
    external_id: str
    source: str
    series_group: str | None = None  # optional name of the series group

# TODO: Check if this is the correct HTTP method to use.
@router.post("/add/series/{external_id}", response_model=SeriesPublic)
async def fetch_series(
    request: AddSeriesRequest,
    session: Session = Depends(get_session),
):
    #  TODO: Add series to database.

    # ----- Lookup Plugin -----
    plugin = plugin_manager.get_plugin(request.source)
    if not plugin or not isinstance(plugin, MetadataPlugin):
        raise HTTPException(status_code=404, detail="Metadata source not found")

    # ----- Fetch From Plugin-----
    data: SeriesFetchModel = await plugin.fetch_series(request.external_id)
    if not data or not data.series:
        raise HTTPException(
            status_code=404,
            detail=f"{request.source} Could not find series with id {request.external_id}",
        )

    try:
        # ----- Handle Series Group -----
        if request.series_group:
            group = session.get(SeriesGroup, uuid.UUID(request.series_group))
            if not group:
                raise HTTPException(
                    status_code=404, detail=f"Series group {request.series_group} not found"
                )

        else:
            group = SeriesGroup(title=data.series.title)
            session.add(group)
            session.flush()  # To get the ID of the new group

        # ----- Lookup Plugin in Database -----
        db_plugin = session.exec(
            select(MetadataPluginTable).where(MetadataPluginTable.name == request.source)
        ).first()
        if not db_plugin:
            raise HTTPException(
                status_code=404,
                detail=f"Metadata source {request.source} not found in database",
            )

        # ----- Add Series -----
        series_obj = Series(
            title=data.series.title,
            author=data.series.author,
            description=data.series.description,
            source_id=db_plugin.id,
            group_id=group.id,
        )
        session.add(series_obj)
        session.flush()

        # ----- Add Books -----
        for book in data.books:
            book_obj = Book(
                title=book.title,
                author=book.author,
                description=book.description,
                volume=book.volume,
                series_id=series_obj.id,
            )
            session.add(book_obj)
            session.flush()

            for release in book.releases:
                release_obj = Release(
                    url=release.url,
                    format=release.format,
                    release_date=release.release_date,
                    book_id=book_obj.id,
                )
                session.add(release_obj)

        # ----- Add Chapters -----
        for chapter in data.chapters:
            chapter_obj = Chapter(
                title=chapter.title,
                author=chapter.author,
                number=chapter.number,
                volume=chapter.volume,
                description=chapter.description,
                series_id=series_obj.id,
            )
            session.add(chapter_obj)
            session.flush()

            for release in chapter.releases:
                release_obj = Release(
                    url=release.url,
                    format=release.format,
                    release_date=release.release_date,
                    chapter_id=chapter_obj.id,
                )
                session.add(release_obj)

        session.commit()
        session.refresh(series_obj)
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Error adding series: {e}")

    series_public = SeriesPublic.model_validate(series_obj)
    return series_public
