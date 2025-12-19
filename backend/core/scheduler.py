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
    MetadataSource,
)
from backend.core.services import metadata_service
from backend.core.notifications import notification_manager
from backend.core.database.models import NotificationType
from backend.core.services.pipeline.automated_pipe import automated_pipe
from backend.core.services.library_service import get_all_series_groups

scheduler = AsyncIOScheduler()

## TODO: Make interval configurable once configs are implemented
UPDATE_SERIES_INTERVAL_MINUTES = 6 * 60  # Update series every 6 hours


async def update_all_series_metadata():
    print("Updating all series metadata...")
    with Session(engine) as session:
        series_list = session.exec(select(Series)).all()

        print(f"Found {len(series_list)} series to update.")

        for series in series_list:
            # Skip series without metadata source or external_id
            if not series.metadata_source or not series.external_id:
                print(f"Skipping series {series.id} ({series.title}) - no metadata source or external ID")
                continue

            # Get the metadata source
            metadata_source = series.metadata_source
            if not metadata_source.enabled:
                print(f"Skipping series {series.id} ({series.title}) - metadata source disabled")
                continue

            try:
                success = await metadata_service.fetch_series(
                    str(metadata_source.id), series.external_id, session=session
                )

                if not success:
                    print(f"Failed to update series {series.id} ({series.title})")
            except Exception as e:
                print(f"Error updating series {series.id} ({series.title}): {e}")
        
        await notification_manager.broadcast(
            NotificationMessage(
                type=NotificationType.INFO,
                message="Series metadata update completed.",
            )
        )


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


async def run_automated_pipeline():
    print("Running automated pipeline...")
    try:
        initial_data = {}
        result = await automated_pipe.execute(initial_data)
        
        # Extract results from pipeline execution
        indexer_results = result.get("indexer_results", [])
        parsed_results = result.get("parsed_results", {})
        sent_items = result.get("sent_items", [])
        
        # Log results
        print(f"Indexer found {len(indexer_results)} results")
        print(f"Parser matched {len(parsed_results)} items")
        print(f"Sent {len(sent_items)} items to download client")
        
        # Send notification based on results
        if sent_items:
            await notification_manager.broadcast(
                NotificationMessage(
                    type=NotificationType.INFO,
                    message=f"Automated pipeline completed: {len(sent_items)} item(s) sent to download client.",
                )
            )
        elif indexer_results:
            await notification_manager.broadcast(
                NotificationMessage(
                    type=NotificationType.INFO,
                    message=f"Automated pipeline completed: {len(indexer_results)} result(s) found, but none matched monitored series.",
                )
            )
        else:
            print("No new releases found in indexer feeds")
            
    except Exception as e:
        print(f"Error running automated pipeline: {e}")
        await notification_manager.broadcast(
            NotificationMessage(
                type=NotificationType.ERROR,
                message=f"Automated pipeline failed: {str(e)}",
            )
        )