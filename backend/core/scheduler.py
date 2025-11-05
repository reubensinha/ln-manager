import asyncio
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
)
from backend.core.services import metadata_service
from backend.core.notifications import notification_manager
from backend.core.database.models import NotificationType

scheduler = AsyncIOScheduler()

## TODO: Make interval configurable once configs are implemented
UPDATE_SERIES_INTERVAL_MINUTES = 6 * 60  # Update series every 6 hours


async def update_all_series_metadata():
    print("Updating all series metadata...")
    with Session(engine) as session:
        series_list = session.exec(select(Series)).all()

        print(f"Found {len(series_list)} series to update.")

        for series in series_list:
            # TODO: Log series without plugin or external_id are missing
            if not series.plugin or not series.external_id:
                continue

            success = await metadata_service.fetch_series(
                series.plugin.name, series.external_id, session=session
            )

            # TODO: Log success/failure
            if not success:
                print(f"Failed to update series {series.id} ({series.title})")


# TODO: Better message text
async def check_release_day():
    today = date.today()
    with Session(engine) as session:
        releases_today = session.exec(
            select(Release).where(Release.release_date == today)
        ).all()

        for release in releases_today:
            await notification_manager.broadcast(
                NotificationMessage(
                    type=NotificationType.INFO,
                    message=f"New release today: {release.title} for book {release.book.title if release.book else 'Unknown'}",
                )
            )
