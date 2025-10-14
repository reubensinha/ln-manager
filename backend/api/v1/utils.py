from datetime import date, datetime
from fastapi import HTTPException
from sqlmodel import Session

from backend.core.database.models import (
    DownloadStatus,
    PublishingStatus,
    Series,
    SeriesGroup,
    LanguageCode,
)


def _get_earliest_english_release_date(book) -> date | None:
    """Get the earliest English release date from a book's releases."""
    english_releases = [r for r in book.releases if r.language == LanguageCode.EN]
    if not english_releases:
        return None
    
    release_dates = []
    for release in english_releases:
        parsed_date = release.release_date
        if parsed_date is not None:
            release_dates.append(parsed_date)
    
    return min(release_dates) if release_dates else None

# TODO: Once configs are implemented should make language configurable.
def _update_download_status(session: Session, series: Series):
    """
    Update the download status of a series based on its books' download status.
    Also updates the series group download status if this is the main series.
    """
    today = date.today()

    all_books = series.books
    english_books = [b for b in all_books if b.language == LanguageCode.EN]

    # Filter books that have been released (release_date is set and in the past)
    released_books = []
    for b in all_books:
        parsed_date = b.release_date
        if parsed_date is not None and parsed_date <= today:
            released_books.append(b)

    released_english_books = []
    for b in english_books:
        earliest_en_release = _get_earliest_english_release_date(b)
        if earliest_en_release is not None and earliest_en_release <= today:
            released_english_books.append(b)

    # Debug logging
    # print(f"\n=== Series: {series.title} ===")
    # print(f"Total books: {len(all_books)}")
    # print(f"English books: {len(english_books)}")
    # print(f"Released books: {len(released_books)}")
    # print(f"Released English books: {len(released_english_books)}")
    # print(f"Publishing status: {series.publishing_status}")
    
    for b in released_english_books:
        print(f"  - {b.title}: downloaded={b.downloaded}, release_date={b.release_date}")

    all_books_downloaded = (
        all(b.downloaded for b in all_books) if all_books else False
    )
    released_all_downloaded = (
        all(b.downloaded for b in released_books) if released_books else False
    )
    released_english_downloaded = (
        all(b.downloaded for b in released_english_books)
        if released_english_books
        else False
    )
    any_books_downloaded = any(b.downloaded for b in all_books)

    # print(f"all_books_downloaded: {all_books_downloaded}")
    # print(f"released_all_downloaded: {released_all_downloaded}")
    # print(f"released_english_downloaded: {released_english_downloaded}")
    # print(f"any_books_downloaded: {any_books_downloaded}")

    if not any_books_downloaded:
        target_status = DownloadStatus.NONE

    elif series.publishing_status in {
        PublishingStatus.COMPLETED,
        PublishingStatus.CANCELLED,
    }:
        if all_books_downloaded:
            target_status = DownloadStatus.COMPLETED
        elif released_all_downloaded:
            target_status = DownloadStatus.CONTINUING_orig
        elif released_english_downloaded:
            target_status = DownloadStatus.CONTINUING
        else:
            target_status = DownloadStatus.MISSING

    elif series.publishing_status == PublishingStatus.ONGOING:
        if released_all_downloaded:
            target_status = DownloadStatus.CONTINUING_orig
        elif released_english_downloaded:
            target_status = DownloadStatus.CONTINUING
        else:
            target_status = DownloadStatus.MISSING

    elif series.publishing_status in {
        PublishingStatus.STALLED,
        PublishingStatus.HIATUS,
        PublishingStatus.UNKNOWN,
    }:
        if all_books_downloaded:
            target_status = DownloadStatus.STALLED
        elif released_all_downloaded:
            target_status = DownloadStatus.CONTINUING_orig
        elif released_english_downloaded:
            target_status = DownloadStatus.CONTINUING
        else:
            target_status = DownloadStatus.MISSING
    else:
        raise HTTPException(status_code=500, detail="Unhandled publishing status")

    print(f"Target status: {target_status}\n")

    series.download_status = target_status
    session.add(series)

    # Update series group if this is the main series
    series_group = session.get(SeriesGroup, series.group_id)
    if not series_group:
        raise HTTPException(
            status_code=404, detail="Series group not found for the series"
        )

    if str(series_group.main_series_id) == str(series.id):
        series_group.download_status = target_status
        session.add(series_group)