from fastapi import HTTPException
from sqlmodel import Session

from backend.core.database.models import DownloadStatus, PublishingStatus, Series, SeriesGroup


def _update_download_status(session: Session, series: Series):
    """
    Update the download status of a series based on its books' download status.
    Also updates the series group download status if this is the main series.
    """
    all_books_downloaded = all(b.downloaded for b in series.books)
    any_books_downloaded = any(b.downloaded for b in series.books)
    
    target_status = DownloadStatus.NONE

    if all_books_downloaded:
        if series.publishing_status in {
            PublishingStatus.COMPLETED,
            PublishingStatus.CANCELLED,
        }:
            target_status = DownloadStatus.COMPLETED
        elif series.publishing_status == PublishingStatus.ONGOING:
            target_status = DownloadStatus.CONTINUING
        else:  # STALLED, HIATUS, UNKNOWN
            target_status = DownloadStatus.STALLED
    elif any_books_downloaded:
        target_status = DownloadStatus.MISSING

    series.download_status = target_status
    session.add(series)
    
    # Update series group if this is the main series
    series_group = session.get(SeriesGroup, series.group_id)
    if not series_group:
        raise HTTPException(status_code=404, detail="Series group not found for the series")

    if str(series_group.main_series_id) == str(series.id):
        series_group.download_status = target_status
        session.add(series_group)