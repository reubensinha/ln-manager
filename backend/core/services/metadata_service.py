import asyncio
from urllib.parse import unquote
from fastapi import HTTPException, Depends
from sqlmodel import Session, select

# from backend.core.database.plugins import MetadataPlugin, IndexerPlugin
from backend.api.v1.utils import _update_download_status
from backend.plugin_manager import plugin_manager
from backend.core.database.models import *
import uuid

from backend.core.database.database import get_session
from backend.core.plugins.metadata import MetadataPlugin, SeriesFetchModel
from backend.core.notifications import notification_manager


async def fetch_series(
    source: str,
    external_id: str,
    series_group: str | None = None,
    session: Session = Depends(get_session),
):
    success = False

    notifications = []

    plugin = plugin_manager.get_plugin(source)
    if not plugin or not isinstance(plugin, MetadataPlugin):
        raise HTTPException(status_code=404, detail="Metadata source not found")

    # ----- Fetch From Plugin-----
    data: SeriesFetchModel | None = await plugin.fetch_series(external_id)
    if not data or not data.series:
        raise HTTPException(
            status_code=404,
            detail=f"{source} Could not find series with id {external_id}",
        )

    try:
        # ----- Lookup Plugin in Database (do this once) -----
        db_plugin = session.exec(
            select(MetadataPluginTable).where(MetadataPluginTable.name == source)
        ).first()
        if not db_plugin:
            raise HTTPException(
                status_code=404,
                detail=f"Metadata source {source} not found in database",
            )

        # ----- Check if Series Already Exists -----
        existing_series = session.exec(
            select(Series).where(
                Series.source_id == db_plugin.id,
                Series.external_id == external_id,
            )
        ).first()

        if not existing_series:
            notifications.append(
                NotificationMessage(
                    message=f"Added '{data.series.title}' to library.",
                    type=NotificationType.SUCCESS,
                )
            )

        # ----- Handle Series Group -----
        if series_group:
            # User explicitly specified a group - just use it, don't modify it
            group = session.get(SeriesGroup, uuid.UUID(series_group))
            if not group:
                raise HTTPException(
                    status_code=404,
                    detail=f"Series group {series_group} not found",
                )
        else:
            # No group specified - determine group based on existing series
            if existing_series and existing_series.group_id and existing_series.group:
                # Series exists and has a group - use that group
                group = existing_series.group

                # Only update group if this series is the main series
                if str(group.main_series_id) == str(existing_series.id):
                    group.title = data.series.title
                    group.description = data.series.description
                    group.img_url = data.series.img_url
                    group.nsfw_img = data.series.nsfw_img
            else:
                # Series doesn't exist or has no group - create new group
                group = SeriesGroup(
                    title=data.series.title,
                    description=data.series.description,
                    img_url=data.series.img_url,
                    nsfw_img=data.series.nsfw_img,
                    main_series_id="",  # Will be set after series is created
                )
                session.add(group)
                session.flush()  # Get the group ID

        # ----- Add or Update Series -----
        if existing_series:
            # Update existing series
            ## TODO: Explicitly check for changes and notify user
            for key, value in data.series.model_dump(
                exclude={"id", "source_id", "group_id"}
            ).items():
                setattr(existing_series, key, value)
            existing_series.deleted = False

            # Update group_id if explicitly requested
            if series_group:
                existing_series.group_id = uuid.UUID(series_group)
            # else: keep existing group_id

            series_obj = existing_series

            # Update group if this is the main series (and no explicit group requested)
            if (
                not series_group
                and series_obj.group
                and str(series_obj.group.main_series_id) == str(series_obj.id)
            ):
                series_obj.group.title = data.series.title
                series_obj.group.description = data.series.description
                series_obj.group.img_url = data.series.img_url
                series_obj.group.nsfw_img = data.series.nsfw_img
        else:
            # Create new series
            series_obj = Series.model_validate(
                data.series, update={"source_id": db_plugin.id, "group_id": group.id}
            )
            session.add(series_obj)
            session.flush()

            # Set this as the main series if we created a new group
            if not series_group and not group.main_series_id:
                group.main_series_id = str(series_obj.id)

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
                # TODO: Explicitly check for changes and notify user
                saved_monitored = existing_book.monitored
                saved_downloaded = existing_book.downloaded

                for key, value in book_model.book.model_dump(
                    exclude={"id", "series_id", "monitored", "downloaded"}
                ).items():
                    setattr(existing_book, key, value)
                existing_book.deleted = False

                existing_book.monitored = saved_monitored
                existing_book.downloaded = saved_downloaded

                book_obj = existing_book
            else:
                book_obj = Book.model_validate(
                    book_model.book, update={"series_id": series_obj.id}
                )
                session.add(book_obj)

                if existing_series:
                    notifications.append(
                        NotificationMessage(
                            message=f"New book added to '{series_obj.title}'.",
                            type=NotificationType.INFO,
                        )
                    )

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
                    
                    if existing_series and existing_book:
                        notifications.append(
                            NotificationMessage(
                                message=f"New release added to '{book_obj.title}'.",
                                type=NotificationType.INFO,
                            )
                        )

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
                
                if existing_series:
                    notifications.append(
                        NotificationMessage(
                            message=f"New chapter added to '{series_obj.title}'.",
                            type=NotificationType.INFO,
                        )
                    )
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
                    if existing_series and exisiting_chapter:
                        notifications.append(
                            NotificationMessage(
                                message=f"New release added to chapter {chapter_obj.volume}x{chapter_obj.number} of '{series_obj.title}'.",
                                type=NotificationType.INFO,
                            )
                        )

        # ----- Mark Missing Books as Deleted -----
        fetched_book_external_ids = {
            b.book.external_id for b in data.books if b.book.external_id
        }
        existing_books = session.exec(
            select(Book).where(Book.series_id == series_obj.id)
        ).all()

        for existing_book in existing_books:
            if existing_book.external_id not in fetched_book_external_ids:
                existing_book.deleted = True

        session.commit()
        session.refresh(series_obj)

        _update_download_status(session, series_obj)
        session.commit()

        success = True

    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Error adding series: {e}")

    for notif in notifications:
        await notification_manager.broadcast(notif)
    
    return success
