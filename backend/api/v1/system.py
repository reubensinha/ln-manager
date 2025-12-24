import asyncio
from pathlib import Path
from typing import Any
from datetime import datetime
import uuid

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, BackgroundTasks
from fastapi.responses import FileResponse
from sqlmodel import Session, select

from backend.core.database.models import Notification
from backend.core.database.database import get_session, db_dir
from backend.core.backup import backup_database, restore_database, list_backups

router = APIRouter()

# In-memory storage for task progress (in production, use Redis or database)
task_progress: dict[str, dict[str, Any]] = {}

@router.get("/system/notifications", response_model=list[Notification])
async def read_notifications(*, session: Session = Depends(get_session)):
    notifications = session.exec(select(Notification)).all()
    return notifications


@router.post("/system/backup")
async def create_backup() -> dict[str, Any]:
    """
    Creates a complete backup of the database, configuration, and plugin data.
    
    Returns a downloadable backup file path and metadata.
    """
    try:
        backup_path = backup_database()
        return {
            "success": True,
            "message": "Backup created successfully",
            "filename": backup_path.name,
            "path": str(backup_path),
            "size": backup_path.stat().st_size,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Backup failed: {str(e)}")


@router.post("/system/backup/async")
async def create_backup_async(background_tasks: BackgroundTasks) -> dict[str, Any]:
    """
    Creates a backup in the background and allows progress tracking.
    
    Returns a task_id that can be used to check progress.
    """
    task_id = str(uuid.uuid4())
    
    task_progress[task_id] = {
        "status": "pending",
        "progress": 0,
        "message": "Backup task queued",
        "created_at": datetime.now().isoformat(),
        "completed_at": None,
        "result": None,
        "error": None,
    }
    
    background_tasks.add_task(run_backup_task, task_id)
    
    return {
        "success": True,
        "task_id": task_id,
        "message": "Backup task started",
    }


def run_backup_task(task_id: str):
    """Background task to create backup with progress updates."""
    def update_progress(progress: int, message: str):
        """Callback to update task progress."""
        task_progress[task_id]["progress"] = progress
        task_progress[task_id]["message"] = message
        if progress > 0:
            task_progress[task_id]["status"] = "running"
    
    try:
        task_progress[task_id]["status"] = "running"
        
        # Call backup_database with progress callback
        backup_path = backup_database(progress_callback=update_progress)
        
        task_progress[task_id]["status"] = "completed"
        task_progress[task_id]["progress"] = 100
        task_progress[task_id]["message"] = "Backup completed successfully"
        task_progress[task_id]["completed_at"] = datetime.now().isoformat()
        task_progress[task_id]["result"] = {
            "filename": backup_path.name,
            "path": str(backup_path),
            "size": backup_path.stat().st_size,
        }
    except Exception as e:
        task_progress[task_id]["status"] = "failed"
        task_progress[task_id]["progress"] = 100
        task_progress[task_id]["message"] = f"Backup failed: {str(e)}"
        task_progress[task_id]["error"] = str(e)
        task_progress[task_id]["completed_at"] = datetime.now().isoformat()


@router.get("/system/backup/download/{filename}")
async def download_backup(filename: str) -> FileResponse:
    """
    Downloads a specific backup file.
    
    Args:
        filename: Name of the backup file to download.
    """
    backup_path = db_dir / filename
    
    if not backup_path.exists() or not backup_path.name.startswith("backup_"):
        raise HTTPException(status_code=404, detail="Backup file not found")
    
    return FileResponse(
        path=backup_path,
        filename=filename,
        media_type="application/zip",
    )


@router.get("/system/backups")
async def get_backups() -> dict[str, Any]:
    """
    Lists all available backup files.
    
    Returns metadata about each backup including size, creation date, and version.
    """
    try:
        backups = list_backups()
        return {
            "success": True,
            "backups": backups,
            "count": len(backups),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list backups: {str(e)}")


@router.post("/system/restore")
async def restore_backup(
    file: UploadFile = File(...),
    overwrite: bool = False
) -> dict[str, Any]:
    """
    Restores the database from an uploaded backup file.
    
    Args:
        file: The backup ZIP file to restore from.
        overwrite: Whether to overwrite existing database (default: False).
    
    WARNING: This will replace all current data if overwrite=True.
    """
    if not file.filename or not file.filename.endswith(".zip"):
        raise HTTPException(status_code=400, detail="Backup file must be a ZIP file")
    
    temp_backup = db_dir / f"temp_restore_{file.filename}"
    
    try:
        # Save uploaded file temporarily
        
        with open(temp_backup, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # Perform restoration
        summary = restore_database(temp_backup, overwrite=overwrite)
        
        # Clean up temp file
        temp_backup.unlink()
        
        return {
            "success": True,
            "message": "Database restored successfully",
            "summary": summary,
        }
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Clean up temp file on error
        if temp_backup.exists():
            temp_backup.unlink()
        raise HTTPException(status_code=500, detail=f"Restoration failed: {str(e)}")


@router.post("/system/restore/async")
async def restore_backup_async(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    overwrite: bool = False
) -> dict[str, Any]:
    """
    Restores the database from an uploaded backup file in the background.
    
    Returns a task_id that can be used to check progress.
    
    WARNING: This will replace all current data if overwrite=True.
    """
    if not file.filename or not file.filename.endswith(".zip"):
        raise HTTPException(status_code=400, detail="Backup file must be a ZIP file")
    
    # Save uploaded file
    temp_backup = db_dir / f"temp_restore_{file.filename}"
    
    try:
        with open(temp_backup, "wb") as f:
            content = await file.read()
            f.write(content)
    except Exception as e:
        if temp_backup.exists():
            temp_backup.unlink()
        raise HTTPException(status_code=500, detail=f"Failed to save upload: {str(e)}")
    
    # Create task
    task_id = str(uuid.uuid4())
    
    task_progress[task_id] = {
        "status": "pending",
        "progress": 0,
        "message": "Restore task queued",
        "created_at": datetime.now().isoformat(),
        "completed_at": None,
        "result": None,
        "error": None,
    }
    
    background_tasks.add_task(run_restore_task, task_id, temp_backup, overwrite)
    
    return {
        "success": True,
        "task_id": task_id,
        "message": "Restore task started",
    }


def run_restore_task(task_id: str, backup_file: Path, overwrite: bool):
    """Background task to restore database with progress updates."""
    def update_progress(progress: int, message: str):
        """Callback to update task progress."""
        task_progress[task_id]["progress"] = progress
        task_progress[task_id]["message"] = message
        if progress > 0:
            task_progress[task_id]["status"] = "running"
    
    try:
        task_progress[task_id]["status"] = "running"
        
        # Call restore_database with progress callback
        summary = restore_database(backup_file, overwrite=overwrite, progress_callback=update_progress)
        
        # Clean up temp file
        if backup_file.exists():
            backup_file.unlink()
        
        task_progress[task_id]["status"] = "completed"
        task_progress[task_id]["progress"] = 100
        task_progress[task_id]["message"] = "Restore completed successfully"
        task_progress[task_id]["completed_at"] = datetime.now().isoformat()
        task_progress[task_id]["result"] = summary
    except Exception as e:
        # Clean up temp file on error
        if backup_file.exists():
            backup_file.unlink()
        
        task_progress[task_id]["status"] = "failed"
        task_progress[task_id]["progress"] = 100
        task_progress[task_id]["message"] = f"Restore failed: {str(e)}"
        task_progress[task_id]["error"] = str(e)
        task_progress[task_id]["completed_at"] = datetime.now().isoformat()


@router.get("/system/task/{task_id}")
async def get_task_status(task_id: str) -> dict[str, Any]:
    """
    Get the status and progress of a background task.
    
    Args:
        task_id: The task ID returned from async backup/restore operations.
    
    Returns:
        Task status including progress percentage and current message.
    """
    if task_id not in task_progress:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return {
        "success": True,
        "task": task_progress[task_id],
    }


@router.delete("/system/task/{task_id}")
async def clear_task(task_id: str) -> dict[str, Any]:
    """
    Clear a completed or failed task from memory.
    
    Args:
        task_id: The task ID to clear.
    """
    if task_id not in task_progress:
        raise HTTPException(status_code=404, detail="Task not found")
    
    del task_progress[task_id]
    
    return {
        "success": True,
        "message": "Task cleared",
    }


@router.delete("/system/backup/{filename}")
async def delete_backup(filename: str) -> dict[str, Any]:
    """
    Deletes a specific backup file.
    
    Args:
        filename: Name of the backup file to delete.
    """
    backup_path = db_dir / filename
    
    if not backup_path.exists() or not backup_path.name.startswith("backup_"):
        raise HTTPException(status_code=404, detail="Backup file not found")
    
    try:
        backup_path.unlink()
        return {
            "success": True,
            "message": f"Backup {filename} deleted successfully",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete backup: {str(e)}")
