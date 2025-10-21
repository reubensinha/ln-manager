import asyncio

from fastapi import HTTPException, Depends
from sqlmodel import Session, select
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from backend.core.database.database import engine
from backend.core.database.models import Series
from backend.core.services import metadata_service

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

            success = await metadata_service.fetch_series(series.plugin.name, series.external_id, session=session)
            
            # TODO: Log success/failure
            if not success:
                print(f"Failed to update series {series.id} ({series.title})")

