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

        # ----- Add or Update Series -----
        existing_series = session.exec(
            select(Series).where(
                Series.source_id == db_plugin.id,
                Series.external_id == request.external_id,
            )
        ).first()

        if existing_series:
            # Update existing series
            for key, value in data.series.model_dump(
                exclude={"id", "source_id", "group_id"}
            ).items():
                setattr(existing_series, key, value)
            existing_series.deleted = False
            
            # Update group if explicitly requested
            if request.series_group:
                existing_series.group_id = uuid.UUID(request.series_group)
            # else: keep existing group_id
            
            series_obj = existing_series
        else:
            # Create new series
            series_obj = Series.model_validate(
                data.series, update={"source_id": db_plugin.id, "group_id": group.id}
            )
            session.add(series_obj)

        session.flush()

        # ----- Add Books -----
        for book_model in data.books:
            existing_book = session.exec(
                select(Book).where(
                    Book.series_id == series_obj.id,
                    Book.external_id == book_model.book.external_id,
                )
            ).first()

            if existing_book:
                for key, value in book_model.book.model_dump(
                    exclude={"id", "series_id"}
                ).items():
                    setattr(existing_book, key, value)
                existing_book.deleted = False
                book_obj = existing_book
            else:
                book_obj = Book.model_validate(
                    book_model.book, update={"series_id": series_obj.id}
                )
                session.add(book_obj)

            session.flush()

            for release_model in book_model.releases:
                existing_release = session.exec(
                    select(Release).where(
                        Release.book_id == book_obj.id,
                        Release.external_id == release_model.external_id,
                    )
                ).first()

                if existing_release:
                    for key, value in release_model.model_dump(
                        exclude={"id", "book_id", "chapter_id"}
                    ).items():
                        setattr(existing_release, key, value)
                    existing_release.deleted = False
                else:
                    release_obj = Release.model_validate(
                        release_model, update={"book_id": book_obj.id}
                    )
                    session.add(release_obj)

        # ----- Add Chapters -----
        for chapter_model in data.chapters:

            exisiting_chapter = session.exec(
                select(Chapter).where(
                    Chapter.series_id == series_obj.id,
                    Chapter.number == chapter_model.number,
                    Chapter.volume == chapter_model.volume,
                )
            ).first()

            if exisiting_chapter:
                for key, value in chapter_model.model_dump(
                    exclude={"id", "series_id"}
                ).items():
                    setattr(exisiting_chapter, key, value)
                exisiting_chapter.deleted = False
                chapter_obj = exisiting_chapter
            else:
                chapter_obj = Chapter.model_validate(
                    chapter_model, update={"series_id": series_obj.id}
                )
                session.add(chapter_obj)
            session.flush()

            for release_model in chapter_model.releases:
                existing_release = session.exec(
                    select(Release).where(
                        Release.chapter_id == chapter_obj.id,
                        Release.external_id == release_model.external_id,
                    )
                ).first()

                if existing_release:
                    for key, value in release_model.model_dump(
                        exclude={"id", "book_id", "chapter_id"}
                    ).items():
                        setattr(existing_release, key, value)
                    existing_release.deleted = False
                else:
                    release_obj = Release.model_validate(
                        release_model, update={"chapter_id": chapter_obj.id}
                    )
                    session.add(release_obj)

        # ----- Mark Missing Books as Deleted -----
        fetched_book_external_ids = {b.book.external_id for b in data.books if b.book.external_id}
        existing_books = session.exec(
            select(Book).where(Book.series_id == series_obj.id)
        ).all()

        for existing_book in existing_books:
            if existing_book.external_id not in fetched_book_external_ids:
                existing_book.deleted = True
        
        session.commit()
        session.refresh(series_obj)
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Error adding series: {e}")

    # series_public = SeriesPublic.model_validate(series_obj)
    return {"success": True, "message": "Series added successfully"}
