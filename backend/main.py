import os
import sys
import time
import asyncio
from pathlib import Path

from fastapi import (
    FastAPI,
    HTTPException,
    WebSocket,
    WebSocketDisconnect,
    BackgroundTasks,
    Request,
)
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from fastapi.responses import FileResponse
from sqlmodel import Session, select
import yaml

from backend.core.database.database import init_db, engine
from backend.core.database.models import (
    NotificationMessage,
    PluginBase,
    Plugin,
    PluginType,
    MetadataSource,
    Indexer,
    DownloadClient,
)
from backend.core.notifications import notification_manager
from backend.plugin_manager import PluginManager, PLUGIN_DIRS, plugin_manager
from backend.core.exceptions import (
    ResourceNotFoundError,
    InvalidStateError,
    ValidationError,
)

from backend.core.scheduler import (
    UPDATE_SERIES_INTERVAL_MINUTES,
    check_release_day,
    update_all_series_metadata,
    run_automated_pipeline,
)


from .api.v1 import core, metadata, system

STATIC_DIR = Path(__file__).parent / "static"


scheduler = AsyncIOScheduler()
scheduler.add_job(
    update_all_series_metadata,
    "interval",
    minutes=UPDATE_SERIES_INTERVAL_MINUTES,
)
scheduler.add_job(check_release_day, "cron", hour=0, minute=0)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Perform startup tasks
    init_db()

    with Session(engine) as session:
        # Scan all plugin directories for manifests
        for plugin_dir in PLUGIN_DIRS:
            if not plugin_dir.exists():
                continue

            for folder in plugin_dir.iterdir():
                if not folder.is_dir():
                    continue
                manifest_file = folder / "manifest.yaml"
                if not manifest_file.exists():
                    continue

                manifest = yaml.safe_load(manifest_file.open())
                name = manifest.get("name")
                version = manifest.get("version")
                description = manifest.get("description", "")
                author = manifest.get("author", "")
                ptype = manifest.get("type")

                db_plugin = session.exec(
                    select(Plugin).where(Plugin.name == name)
                ).first()

                if not db_plugin:
                    db_plugin = Plugin(
                        name=name,
                        version=version,
                        author=author,
                        description=description,
                        enabled=True,
                    )
                    session.add(db_plugin)
                else:
                    db_plugin.version = version
                    db_plugin.description = description
                    db_plugin.author = author

        session.commit()

        # Ensure PluginBase table exists
        enabled_plugins = list(
            session.exec(select(Plugin).where(Plugin.enabled == True)).all()
        )

        for plugin in enabled_plugins:
            # Try to find the plugin in any of the plugin directories
            manifest_file = None
            for plugin_dir in PLUGIN_DIRS:
                candidate = plugin_dir / plugin.name / "manifest.yaml"
                if candidate.exists():
                    manifest_file = candidate
                    break

            if manifest_file and manifest_file.exists():
                manifest = yaml.safe_load(manifest_file.open())
                plugin_manager.load_plugin_from_manifest(plugin.name, manifest)
                # try:
                #     plugin_manager.load_plugin_from_manifest(plugin.name, manifest)
                # except Exception as e:
                #     print(f"Failed to load plugin {plugin.name}: {e}")

        # Check if there are any enabled indexers and download clients configured
        has_indexer = (
            session.exec(select(Indexer).where(Indexer.enabled == True)).first()
            is not None
        )
        has_download_client = (
            session.exec(
                select(DownloadClient).where(DownloadClient.enabled == True)
            ).first()
            is not None
        )

        if has_indexer and has_download_client:
            scheduler.add_job(
                run_automated_pipeline,
                "interval",
                minutes=15,
            )
            print(
                "Automated pipeline job scheduled (Indexer and Download Client plugins found)"
            )
        else:
            missing = []
            if not has_indexer:
                missing.append("Indexer")
            if not has_download_client:
                missing.append("Download Client")
            print(
                f"Automated pipeline job NOT scheduled - missing enabled plugins: {', '.join(missing)}"
            )

    scheduler.start()
    yield
    # Perform shutdown tasks
    scheduler.shutdown()


app = FastAPI(
    title="LN Auto",
    description="Light Novel Automation Tool",
    version="0.1.0",
    lifespan=lifespan,
)

origins = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handlers for custom domain exceptions
@app.exception_handler(ResourceNotFoundError)
async def resource_not_found_handler(request: Request, exc: ResourceNotFoundError):
    return JSONResponse(
        status_code=404,
        content={"detail": str(exc)},
    )


@app.exception_handler(InvalidStateError)
async def invalid_state_handler(request: Request, exc: InvalidStateError):
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc)},
    )


@app.exception_handler(ValidationError)
async def validation_error_handler(request: Request, exc: ValidationError):
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc)},
    )


@app.get("/api")
async def read_root():
    return {"Hello": "World"}


@app.get("/api/health")
async def health_check():
    return {"status": "ok"}


@app.websocket("/ws/notifications")
async def websocket_endpoint(websocket: WebSocket):
    await notification_manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()  # keep connection alive if needed
    except WebSocketDisconnect:
        notification_manager.disconnect(websocket)


@app.post("/api/v1/notify")
async def notify_clients(message: NotificationMessage):
    await notification_manager.broadcast(message)
    return {"message": "Notifications sent"}


def restart_server():
    """
    Restart the server. Method depends on how it's running.
    TODO: Test in production.
    """
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Initiating restart...")

    # Try to touch file for uvicorn --reload
    try:
        Path(__file__).touch()
        print("Triggered uvicorn auto-reload")
    except Exception as e:
        print(f"Could not trigger auto-reload: {e}")
        # Fallback to exec
        python = sys.executable
        os.execl(python, python, *sys.argv)


## TODO: Endpoint to restart backend server
@app.post("/api/v1/restart")
async def restart_backend(background_tasks: BackgroundTasks):
    """
    Restart the backend server.

    This endpoint schedules a server restart as a background task.
    The server will shut down gracefully and restart with the same arguments.

    Note: This works best when the server is run with a process manager
    (like systemd, supervisor, or PM2) that can automatically restart it.
    """
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Restart endpoint called")

    await notification_manager.broadcast(
        NotificationMessage(message="Backend server is restarting...")
    )

    async def delayed_restart():
        await asyncio.sleep(1)
        restart_server()

    # Schedule restart as background task to allow response to be sent
    background_tasks.add_task(delayed_restart)

    return {"success": True, "message": "Backend server restart initiated"}


app.include_router(core.router, prefix="/api/v1", tags=["core"])
app.include_router(metadata.router, prefix="/api/v1", tags=["metadata"])
app.include_router(system.router, prefix="/api/v1", tags=["system"])


@app.get("/", include_in_schema=False)
async def root_index():
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    raise HTTPException(status_code=404)


# Catch-all to serve static files or SPA index
@app.get("/{full_path:path}", include_in_schema=False)
async def spa_fallback(full_path: str):
    # Avoid interfering with API or websocket paths (these are registered above)
    # If a file exists in STATIC_DIR, serve it
    candidate = STATIC_DIR / full_path
    if candidate.exists() and candidate.is_file():
        return FileResponse(candidate)

    # Otherwise, return index.html so client-side routing can handle the path
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)

    # nothing found
    raise HTTPException(status_code=404)
