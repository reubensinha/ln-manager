from fastapi import APIRouter, HTTPException, Depends
from httpx import get
from sqlmodel import SQLModel, Session, select

# from backend.core.database.plugins import MetadataPlugin, IndexerPlugin
from backend.plugin_manager import plugin_manager
from backend.core.database.models import *
import uuid

from backend.core.database.database import get_session
from backend.core.plugins.metadata import MetadataPlugin, SeriesFetchModel

router = APIRouter()


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


class AddSeriesRequest(SQLModel):
    source: str
    external_id: str
    series_group: str | None = None  # optional name of the series group


class AddSeriesResponse(SQLModel):
    success: bool
    message: str


@router.post("/add/series", response_model=AddSeriesResponse)
async def fetch_series(
    request: AddSeriesRequest,
    session: Session = Depends(get_session),
):
    #  TODO: Update add to Database Fields.

    # ----- Lookup Plugin -----
    plugin = plugin_manager.get_plugin(request.source)
    if not plugin or not isinstance(plugin, MetadataPlugin):
        raise HTTPException(status_code=404, detail="Metadata source not found")

    # ----- Fetch From Plugin-----
    data: SeriesFetchModel | None = await plugin.fetch_series(request.external_id)
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
                    status_code=404,
                    detail=f"Series group {request.series_group} not found",
                )

        else:
            group = SeriesGroup(title=data.series.title)
            session.add(group)
            session.flush()  # To get the ID of the new group

        # ----- Lookup Plugin in Database -----
        db_plugin = session.exec(
            select(MetadataPluginTable).where(
                MetadataPluginTable.name == request.source
            )
        ).first()
        if not db_plugin:
            raise HTTPException(
                status_code=404,
                detail=f"Metadata source {request.source} not found in database",
            )

        # ----- Add Series -----
        series_obj = Series.model_validate(
            data.series, update={"source_id": db_plugin.id, "group_id": group.id}
        )

        session.add(series_obj)
        session.flush()

        # ----- Add Books -----
        for book_model in data.books:
            book_obj = Book.model_validate(
                book_model.book, update={"series_id": series_obj.id}
            )
            session.add(book_obj)
            session.flush()

            for release_model in book_model.releases:
                release_obj = Release.model_validate(
                    release_model, update={"book_id": book_obj.id}
                )
                session.add(release_obj)

        # ----- Add Chapters -----
        for chapter_model in data.chapters:
            chapter_obj = Chapter.model_validate(
                chapter_model, update={"series_id": series_obj.id}
            )
            session.add(chapter_obj)
            session.flush()

            for release_model in chapter_model.releases:
                release_obj = Release.model_validate(
                    release_model, update={"chapter_id": chapter_obj.id}
                )
                session.add(release_obj)

        session.commit()
        session.refresh(series_obj)
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Error adding series: {e}")

    # series_public = SeriesPublic.model_validate(series_obj)
    return {"success": True, "message": "Series added successfully"}
