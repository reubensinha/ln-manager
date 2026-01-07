import asyncio
import logging
from datetime import date

from fastapi import HTTPException, Depends
from sqlmodel import Session, select
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from backend.core.database.database import engine
from backend.core.database.models import (
    Notification,
    NotificationMessage,
    Release,
    Series,
    MetadataSource,
)
from backend.core.services import metadata_service
from backend.core.notifications import notification_manager
from backend.core.database.models import NotificationType
from backend.core.services.library_service import get_all_series_groups
from backend.core.logging_config import get_logger


logger = get_logger(__name__)

scheduler = AsyncIOScheduler()

## TODO: Make interval configurable once configs are implemented
UPDATE_SERIES_INTERVAL_MINUTES = 6 * 60  # Update series every 6 hours


async def update_all_series_metadata():
    logger.info("Starting scheduled metadata update for all series...")
    with Session(engine) as session:
        series_list = session.exec(select(Series)).all()

        logger.info(f"Found {len(series_list)} series to update")

        for series in series_list:
            # Skip series without metadata source or external_id
            if not series.metadata_source or not series.external_id:
                logger.debug(f"Skipping series {series.id} ({series.title}) - no metadata source or external ID")
                continue

            # Get the metadata source
            metadata_source = series.metadata_source
            if not metadata_source.enabled:
                logger.debug(f"Skipping series {series.id} ({series.title}) - metadata source disabled")
                continue

            try:
                logger.debug(f"Updating series {series.id} ({series.title})")
                success = await metadata_service.fetch_series(
                    str(metadata_source.id), series.external_id, session=session
                )

                if not success:
                    logger.warning(f"Failed to update series {series.id} ({series.title})")
            except Exception as e:
                logger.error(f"Error updating series {series.id} ({series.title}): {e}", exc_info=True)
        
        logger.info("Series metadata update completed")
        await notification_manager.broadcast(
            NotificationMessage(
                type=NotificationType.INFO,
                message="Series metadata update completed.",
            )
        )


# TODO: Better message text
async def check_release_day():
    today = date.today()
    logger.info(f"Checking for releases on {today}")
    
    with Session(engine) as session:
        releases_today = session.exec(
            select(Release).where(Release.release_date == today)
        ).all()

        logger.info(f"Found {len(releases_today)} releases today")
        
        for release in releases_today:
            logger.info(f"Release notification: {release.title}")
            await notification_manager.broadcast(
                NotificationMessage(
                    type=NotificationType.INFO,
                    message=f"New release today: {release.title} for book {release.book.title if release.book else 'Unknown'}",
                )
            )
