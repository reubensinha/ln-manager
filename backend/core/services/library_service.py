from sqlmodel import Session, select
from uuid import UUID
from datetime import date

from backend.core.database.models import (
    Collection,
    SeriesGroup,
    Series,
    Book,
    Release,
    DownloadStatus,
    PublishingStatus,
    LanguageCode,
)
from backend.core.exceptions import ResourceNotFoundError, InvalidStateError


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
# TODO: Add downloaded percentage
def _update_download_status(session: Session, series: Series):
    """
    Update the download status of a series based on its books' download status.
    Also updates the series group download status if this is the main series.
    """
    today = date.today()

    all_books: list[Book] = series.books
    english_books: list[Book] = [b for b in all_books if b.language == LanguageCode.EN]

    # Filter books that have been released (release_date is set and in the past)
    released_books: list[Book] = []
    for b in all_books:
        parsed_date = b.release_date
        if parsed_date is not None and parsed_date <= today:
            released_books.append(b)

    released_english_books: list[Book] = []
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
        print(
            f"  - {b.title}: downloaded={b.downloaded}, release_date={b.release_date}"
        )

    all_books_downloaded = all(b.downloaded for b in all_books) if all_books else False
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
        elif released_english_books[-1].downloaded or released_books[-1].downloaded:
            target_status = DownloadStatus.MISSING
        else:
            target_status = DownloadStatus.NONE

    elif series.publishing_status == PublishingStatus.ONGOING:
        if released_all_downloaded:
            target_status = DownloadStatus.CONTINUING_orig
        elif released_english_downloaded:
            target_status = DownloadStatus.CONTINUING
        elif released_english_books[-1].downloaded or released_books[-1].downloaded:
            target_status = DownloadStatus.MISSING
        else:
            target_status = DownloadStatus.NONE

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
        elif released_english_books[-1].downloaded or released_books[-1].downloaded:
            target_status = DownloadStatus.MISSING
        else:
            target_status = DownloadStatus.NONE
    else:
        raise InvalidStateError(f"Unhandled publishing status: {series.publishing_status}")

    print(f"Target status: {target_status}\n")

    series.download_status = target_status
    session.add(series)

    # Update series group if this is the main series
    series_group = session.get(SeriesGroup, series.group_id)
    if not series_group:
        raise ResourceNotFoundError("Series group", str(series.group_id))

    if str(series_group.main_series_id) == str(series.id):
        series_group.download_status = target_status
        session.add(series_group)


def get_all_collections(session: Session) -> list[Collection]:
    """Get all collections from the database."""
    collections = session.exec(select(Collection)).all()
    return list(collections)


def get_collection_by_id(session: Session, collection_id: UUID) -> Collection:
    """Get a specific collection by ID."""
    collection = session.get(Collection, collection_id)
    if not collection:
        raise ResourceNotFoundError("Collection", str(collection_id))
    return collection


def get_all_series_groups(session: Session) -> list[SeriesGroup]:
    """Get all series groups from the database."""
    series_groups = session.exec(select(SeriesGroup)).all()
    return list(series_groups)


def get_series_group_by_id(session: Session, group_id: UUID) -> SeriesGroup:
    """Get a specific series group by ID."""
    group = session.get(SeriesGroup, group_id)
    if not group:
        raise ResourceNotFoundError("Series group", str(group_id))
    return group


def get_all_series(session: Session) -> list[Series]:
    """Get all series from the database."""
    series = session.exec(select(Series)).all()
    return list(series)


def get_series_by_id(session: Session, series_id: UUID) -> Series:
    """Get a specific series by ID."""
    series = session.get(Series, series_id)
    if not series:
        raise ResourceNotFoundError("Series", str(series_id))
    return series


def get_all_books(session: Session) -> list[Book]:
    """Get all books from the database."""
    books = session.exec(select(Book)).all()
    return list(books)


def get_book_by_id(session: Session, book_id: UUID) -> Book:
    """Get a specific book by ID."""
    book = session.get(Book, book_id)
    if not book:
        raise ResourceNotFoundError("Book", str(book_id))
    return book


def get_all_releases(session: Session) -> list[Release]:
    """Get all releases from the database."""
    releases = session.exec(select(Release)).all()
    return list(releases)


def toggle_book_downloaded(session: Session, book_id: UUID) -> dict[str, str]:
    """Toggle the downloaded status of a book and update the series status."""
    book = session.get(Book, book_id)
    if not book:
        raise ResourceNotFoundError("Book", str(book_id))

    book.downloaded = not book.downloaded
    session.add(book)

    series = session.get(Series, book.series_id)
    if not series:
        raise ResourceNotFoundError("Series", str(book.series_id))

    _update_download_status(session, series)

    session.commit()
    return {"status": "success"}


def set_book_downloaded(session: Session, book_id: UUID, downloaded: bool) -> dict[str, str]:
    """Set the downloaded status of a book and update the series status."""
    book = session.get(Book, book_id)
    if not book:
        raise ResourceNotFoundError("Book", str(book_id))

    book.downloaded = downloaded
    session.add(book)

    series = session.get(Series, book.series_id)
    if not series:
        raise ResourceNotFoundError("Series", str(book.series_id))

    _update_download_status(session, series)

    session.commit()
    return {"status": "success"}


def toggle_book_monitored(session: Session, book_id: UUID) -> dict[str, str]:
    """Toggle the monitored status of a book."""
    book = session.get(Book, book_id)
    if not book:
        raise ResourceNotFoundError("Book", str(book_id))

    book.monitored = not book.monitored
    session.add(book)
    session.commit()
    return {"status": "success"}


def toggle_series_downloaded(session: Session, series_id: UUID) -> dict[str, str]:
    """Toggle the downloaded status of all books in a series."""
    series = session.get(Series, series_id)
    if not series:
        raise ResourceNotFoundError("Series", str(series_id))

    # Toggle the downloaded status of all books in the series
    target_status = any(not book.downloaded for book in series.books)

    for book in series.books:
        book.downloaded = target_status
        session.add(book)

    _update_download_status(session, series)

    session.commit()
    return {"status": "success"}


def toggle_series_monitored(session: Session, series_id: UUID) -> dict[str, str]:
    """Toggle the monitored status of all books in a series."""
    series = session.get(Series, series_id)
    if not series:
        raise ResourceNotFoundError("Series", str(series_id))

    target_status = any(not book.monitored for book in series.books)

    for book in series.books:
        book.monitored = target_status
        session.add(book)
    session.commit()
    return {"status": "success"}
