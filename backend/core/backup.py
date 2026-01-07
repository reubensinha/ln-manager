import json
import zipfile
import logging
from datetime import datetime
from pathlib import Path
from typing import Any
import shutil
from sqlmodel import Session, select
from .database.database import engine, db_dir
from .database.models import (
    Collection,
    SeriesGroup,
    Series,
    Book,
    Chapter,
    Release,
    MetadataSource,
    Indexer,
    DownloadClient,
    Plugin,
    Notification,
)
from .logging_config import get_logger


logger = get_logger(__name__)

BACKUP_VERSION = "1.0"

# Type for progress callback function
from typing import Callable
ProgressCallback = Callable[[int, str], None]


def serialize_model(obj: Any) -> dict | None:
    """Convert SQLModel instance to JSON-serializable dict."""
    if obj is None:
        return None

    data = obj.model_dump(mode="json")
    # Convert datetime/date objects to ISO format strings
    for key, value in data.items():
        if isinstance(value, datetime):
            data[key] = value.isoformat()
    return data


def backup_database(
    backup_path: str | Path | None = None,
    progress_callback: ProgressCallback | None = None
) -> Path:
    """
    Creates a backup of the database, plugin data, and configuration in a portable ZIP format.
    
    The backup includes:
    - All database tables exported as JSON
    - Plugin configuration files
    - Plugin data directories
    - Backup metadata (version, timestamp, etc.)
    
    Args:
        backup_path: Optional path for the backup file. If not provided,
                    creates a timestamped backup in the config directory.
        progress_callback: Optional callback function(progress: int, message: str)
                          to report progress. Progress is 0-100.
    
    Returns:
        Path: The path to the created backup file.
    
    Raises:
        Exception: If backup creation fails.
    """
    def report_progress(progress: int, message: str):
        """Helper to safely call progress callback."""
        if progress_callback:
            progress_callback(progress, message)
    
    logger.info(f"Starting database backup to: {backup_path if backup_path else 'auto-generated path'}")
    
    if backup_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = db_dir / f"backup_{timestamp}.zip"
    else:
        backup_path = Path(backup_path)

    backup_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        report_progress(5, "Initializing backup...")
        logger.debug("Creating backup ZIP file...")
        
        with zipfile.ZipFile(backup_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            # Add metadata
            report_progress(10, "Creating backup metadata...")
            metadata = {
                "version": BACKUP_VERSION,
                "timestamp": datetime.now().isoformat(),
                "database_path": str(db_dir / "lnauto.db"),
            }
            zipf.writestr("metadata.json", json.dumps(metadata, indent=2))

            # Backup database tables
            report_progress(15, "Exporting database tables...")
            with Session(engine) as session:
                tables_data = {}

                # Export each table
                # Order matters for foreign key relationships
                table_models = [
                    ("plugins", Plugin),
                    ("metadata_sources", MetadataSource),
                    ("indexers", Indexer),
                    ("download_clients", DownloadClient),
                    ("collections", Collection),
                    ("series_groups", SeriesGroup),
                    ("series", Series),
                    ("books", Book),
                    ("chapters", Chapter),
                    ("releases", Release),
                    ("notifications", Notification),
                ]

                total_tables = len(table_models)
                for idx, (table_name, model_class) in enumerate(table_models):
                    progress = 15 + int((idx / total_tables) * 40)  # 15-55%
                    report_progress(progress, f"Exporting {table_name}...")
                    
                    records = session.exec(select(model_class)).all()
                    tables_data[table_name] = [serialize_model(record) for record in records]

            report_progress(60, "Writing database export to backup...")
            zipf.writestr("database.json", json.dumps(tables_data, indent=2))

            # Backup plugin configuration directory
            report_progress(65, "Backing up plugin configurations...")
            plugins_config_dir = db_dir / "plugins"
            if plugins_config_dir.exists():
                for file_path in plugins_config_dir.rglob("*"):
                    if file_path.is_file():
                        arcname = f"config/plugins/{file_path.relative_to(plugins_config_dir)}"
                        zipf.write(file_path, arcname)

            # Backup plugin data directory (excluding large cache/temp files)
            report_progress(75, "Backing up plugin data...")
            plugin_data_dir = db_dir / "plugin-data"
            if plugin_data_dir.exists():
                files_to_backup = [
                    f for f in plugin_data_dir.rglob("*") 
                    if f.is_file() and f.suffix not in [".tmp", ".cache", ".lock"]
                ]
                
                total_files = len(files_to_backup)
                for idx, file_path in enumerate(files_to_backup):
                    if total_files > 0 and idx % max(1, total_files // 10) == 0:
                        progress = 75 + int((idx / total_files) * 20)  # 75-95%
                        report_progress(progress, f"Backing up plugin data ({idx}/{total_files})...")
                    
                    arcname = f"plugin-data/{file_path.relative_to(plugin_data_dir)}"
                    zipf.write(file_path, arcname)

        report_progress(100, "Backup completed successfully")
        logger.info(f"Backup created successfully: {backup_path}")
        return backup_path

    except Exception as e:
        logger.error(f"Backup creation failed: {e}", exc_info=True)
        # Clean up partial backup on failure
        if backup_path.exists():
            backup_path.unlink()
            logger.debug(f"Cleaned up partial backup file: {backup_path}")
        raise Exception(f"Backup creation failed: {str(e)}") from e


def restore_database(
    backup_file: str | Path,
    overwrite: bool = False,
    progress_callback: ProgressCallback | None = None
) -> dict[str, Any]:
    """
    Restores the database from a backup file.
    
    Args:
        backup_file: Path to the backup ZIP file.
        overwrite: If True, overwrites existing database. If False, fails if database exists.
        progress_callback: Optional callback function(progress: int, message: str)
                          to report progress. Progress is 0-100.
    
    Returns:
        dict: Restoration summary with counts of restored items.
    
    Raises:
        FileNotFoundError: If backup file doesn't exist.
        ValueError: If backup format is invalid or version incompatible.
        Exception: If restoration fails.
    """
    def report_progress(progress: int, message: str):
        """Helper to safely call progress callback."""
        if progress_callback:
            progress_callback(progress, message)
    
    logger.info(f"Starting database restoration from: {backup_file}")
    logger.info(f"Overwrite mode: {overwrite}")
    
    backup_file = Path(backup_file)
    if not backup_file.exists():
        logger.error(f"Backup file not found: {backup_file}")
        raise FileNotFoundError(f"Backup file not found: {backup_file}")

    summary = {
        "restored_tables": {},
        "restored_files": 0,
        "backup_version": None,
        "backup_timestamp": None,
    }

    try:
        report_progress(5, "Opening backup file...")
        
        with zipfile.ZipFile(backup_file, "r") as zipf:
            # Verify backup format
            report_progress(10, "Validating backup format...")
            if "metadata.json" not in zipf.namelist():
                raise ValueError("Invalid backup file: missing metadata.json")

            # Read and validate metadata
            report_progress(15, "Reading backup metadata...")
            metadata = json.loads(zipf.read("metadata.json"))
            summary["backup_version"] = metadata.get("version")
            summary["backup_timestamp"] = metadata.get("timestamp")

            if metadata.get("version") != BACKUP_VERSION:
                raise ValueError(
                    f"Incompatible backup version: {metadata.get('version')} "
                    f"(expected {BACKUP_VERSION})"
                )

            # Check if database exists
            report_progress(20, "Checking existing database...")
            db_file = db_dir / "lnauto.db"
            if db_file.exists() and not overwrite:
                raise Exception(
                    "Database already exists. Set overwrite=True to replace it."
                )

            # Backup existing database if it exists
            if db_file.exists():
                report_progress(25, "Creating safety backup of existing database...")
                ## TODO: Workshop naming conventions
                backup_existing = db_dir / f"lnauto.db.pre-restore.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                shutil.copy2(db_file, backup_existing)

            # Clear existing data
            report_progress(30, "Preparing database...")
            from .database.database import init_db
            from sqlmodel import SQLModel

            # Drop and recreate all tables
            SQLModel.metadata.drop_all(engine)
            init_db()

            # Restore database tables
            if "database.json" in zipf.namelist():
                report_progress(35, "Loading database export...")
                tables_data = json.loads(zipf.read("database.json"))

                with Session(engine) as session:
                    # Restore in correct order (respecting foreign keys)
                    restore_order = [
                        ("plugins", Plugin),
                        ("metadata_sources", MetadataSource),
                        ("indexers", Indexer),
                        ("download_clients", DownloadClient),
                        ("collections", Collection),
                        ("series_groups", SeriesGroup),
                        ("series", Series),
                        ("books", Book),
                        ("chapters", Chapter),
                        ("releases", Release),
                        ("notifications", Notification),
                    ]

                    total_tables = len(restore_order)
                    for idx, (table_name, model_class) in enumerate(restore_order):
                        progress = 35 + int((idx / total_tables) * 35)  # 35-70%
                        
                        if table_name in tables_data:
                            records = tables_data[table_name]
                            report_progress(progress, f"Restoring {table_name} ({len(records)} records)...")
                            
                            for record_data in records:
                                # Create model instance from dict
                                instance = model_class.model_validate(record_data)
                                session.add(instance)

                            summary["restored_tables"][table_name] = len(records)

                    report_progress(70, "Committing database changes...")
                    session.commit()

            # Restore plugin configuration files
            report_progress(75, "Restoring plugin configurations...")
            config_files = [f for f in zipf.filelist if f.filename.startswith("config/plugins/")]
            for idx, file_info in enumerate(config_files):
                if idx % max(1, len(config_files) // 5) == 0:
                    progress = 75 + int((idx / max(1, len(config_files))) * 10)  # 75-85%
                    report_progress(progress, f"Restoring config files ({idx}/{len(config_files)})...")
                
                target_path = db_dir / file_info.filename.replace("config/", "")
                target_path.parent.mkdir(parents=True, exist_ok=True)
                with zipf.open(file_info) as source, open(target_path, "wb") as target:
                    shutil.copyfileobj(source, target)
                summary["restored_files"] += 1

            # Restore plugin data files
            report_progress(85, "Restoring plugin data...")
            data_files = [f for f in zipf.filelist if f.filename.startswith("plugin-data/")]
            for idx, file_info in enumerate(data_files):
                if idx % max(1, len(data_files) // 5) == 0:
                    progress = 85 + int((idx / max(1, len(data_files))) * 15)  # 85-100%
                    report_progress(progress, f"Restoring data files ({idx}/{len(data_files)})...")
                
                target_path = db_dir / file_info.filename
                target_path.parent.mkdir(parents=True, exist_ok=True)
                with zipf.open(file_info) as source, open(target_path, "wb") as target:
                    shutil.copyfileobj(source, target)
                summary["restored_files"] += 1

        report_progress(100, "Restore completed successfully")
        return summary

    except Exception as e:
        raise Exception(f"Database restoration failed: {str(e)}") from e


def list_backups(backup_dir: Path | None = None) -> list[dict[str, Any]]:
    """
    Lists all available backup files in the specified directory.
    
    Args:
        backup_dir: Directory to search for backups. Defaults to config directory.
    
    Returns:
        list: List of backup info dictionaries with filename, size, and metadata.
    """
    if backup_dir is None:
        backup_dir = db_dir

    backups = []
    for backup_file in backup_dir.glob("backup_*.zip"):
        try:
            with zipfile.ZipFile(backup_file, "r") as zipf:
                if "metadata.json" in zipf.namelist():
                    metadata = json.loads(zipf.read("metadata.json"))
                else:
                    metadata = {}

            backups.append(
                {
                    "filename": backup_file.name,
                    "path": str(backup_file),
                    "size": backup_file.stat().st_size,
                    "created": datetime.fromtimestamp(backup_file.stat().st_ctime).isoformat(),
                    "version": metadata.get("version"),
                    "timestamp": metadata.get("timestamp"),
                }
            )
        except Exception:
            # Skip invalid backup files
            continue

    return sorted(backups, key=lambda x: x["created"], reverse=True)
