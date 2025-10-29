from fastapi import HTTPException, UploadFile
from sqlmodel import Session

import yaml
import zipfile
import shutil
from pathlib import Path
from datetime import date
from tempfile import TemporaryDirectory

from backend.core.database.models import (
    Book,
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


async def _install_plugin_util(file: UploadFile, session: Session) -> dict[str, str]:
    # Validate .lna structure and manifest.yaml
    # Manage dependencies
    # Extract plugin.lna files in appropriate directories
    if not file.filename or not file.filename.endswith(".lna"):
        raise HTTPException(
            status_code=400, detail="Invalid file type. Must be .lna file"
        )

    if not file.filename.endswith(".lna"):
        raise HTTPException(
            status_code=400, detail="Invalid file type. Must be .lna file"
        )

    with TemporaryDirectory() as temp_dir:
        # Save uploaded file to temp directory
        temp_path = Path(temp_dir)
        lna_path = temp_path / file.filename

        # Save uploaded file
        try:
            content = await file.read()
            with open(lna_path, "wb") as f:
                f.write(content)
        except Exception as e:
            raise HTTPException(
                status_code=500, detail="Failed to save uploaded file"
            ) from e

        # Extract .lna (zip) file
        try:
            with zipfile.ZipFile(lna_path, "r") as zip_ref:
                zip_ref.extractall(temp_path)
        except zipfile.BadZipFile as e:
            raise HTTPException(
                status_code=400, detail="Invalid .lna file format"
            ) from e

        manifest_path = temp_path / "manifest.yaml"

        if not manifest_path or not manifest_path.exists():
            raise HTTPException(
                status_code=400, detail="manifest.yaml not found in .lna file"
            )

        try:
            with open(manifest_path, "r") as f:
                manifest = yaml.safe_load(f)
        except Exception as e:
            raise HTTPException(
                status_code=400, detail="Failed to read manifest.yaml"
            ) from e

        required_fields = [
            "name",
            "version",
            "author",
            "description",
            "type",
            "entry_point",
        ]
        missing_fields = [field for field in required_fields if field not in manifest]
        if missing_fields:
            raise HTTPException(
                status_code=400,
                detail=f"Manifest missing required fields: {', '.join(missing_fields)}",
            )

        valid_types = ["metadata", "indexer", "download client", "generic"]
        if manifest["type"] not in valid_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid plugin type. Must be one of: {', '.join(valid_types)}",
            )

        plugin_name = manifest["name"]
        plugin_root = manifest_path.parent

        backend_plugins_dir = Path("./backend/plugins")
        frontend_plugins_dir = Path("./frontend/src/plugins")

        plugin_backend_dest = backend_plugins_dir / plugin_name
        plugin_frontend_dest = frontend_plugins_dir / plugin_name

        if plugin_backend_dest.exists() or plugin_frontend_dest.exists():
            raise HTTPException(
                status_code=409,
                detail=f"Plugin '{plugin_name}' already exists. Please uninstall it first.",
            )

        backend_src = plugin_root / "backend"
        if not backend_src.exists() or not backend_src.is_dir():
            try:
                shutil.copytree(backend_src, plugin_backend_dest)
                shutil.copy2(manifest_path, plugin_backend_dest / "manifest.yaml")
            except Exception as e:
                if plugin_backend_dest.exists():
                    shutil.rmtree(plugin_backend_dest)
                raise HTTPException(
                    status_code=500, detail=f"Failed to install backend: {str(e)}"
                )

        frontend_src = plugin_root / "frontend"
        if frontend_src.exists() and frontend_src.is_dir():
            frontend_manifest = frontend_src / "manifest.tsx"
            if not frontend_manifest.exists():
                # Cleanup backend if frontend manifest is missing
                if plugin_backend_dest.exists():
                    shutil.rmtree(plugin_backend_dest)
                raise HTTPException(
                    status_code=400,
                    detail="Frontend manifest.tsx not found in frontend directory",
                )

            try:
                shutil.copytree(frontend_src, plugin_frontend_dest)
            except Exception as e:
                # Cleanup on failure
                if plugin_backend_dest.exists():
                    shutil.rmtree(plugin_backend_dest)
                if plugin_frontend_dest.exists():
                    shutil.rmtree(plugin_frontend_dest)
                raise HTTPException(
                    status_code=500, detail=f"Failed to install frontend: {str(e)}"
                )

    return {
        "status": "success",
        "message": f"Plugin '{plugin_name}' version {manifest['version']} installed successfully.",
    }
