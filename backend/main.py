import os
import sys
import time
import asyncio
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from sqlmodel import Session, select
import yaml

from backend.core.database.database import init_db, engine
from backend.core.database.models import (
    NotificationMessage,
    PluginBase,
    MetadataPluginTable,
    IndexerPlugin,
    DownloadClientPlugin,
    GenericPlugin,
)
from backend.core.notifications import notification_manager
from backend.plugin_manager import PluginManager, PLUGIN_DIR, plugin_manager

from backend.core.scheduler import (
    UPDATE_SERIES_INTERVAL_MINUTES,
    update_all_series_metadata,
)


from .api.v1 import core, metadata, system

scheduler = AsyncIOScheduler()
scheduler.add_job(
    update_all_series_metadata,
    "interval",
    minutes=UPDATE_SERIES_INTERVAL_MINUTES,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Perform startup tasks
    init_db()

    with Session(engine) as session:
        for folder in PLUGIN_DIR.iterdir():
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

            if ptype == "metadata":
                plugin_cls = MetadataPluginTable
            elif ptype == "indexer":
                plugin_cls = IndexerPlugin
            elif ptype == "downloader":
                plugin_cls = DownloadClientPlugin
            else:
                plugin_cls = GenericPlugin

            db_plugin = session.exec(
                select(plugin_cls).where(plugin_cls.name == name)
            ).first()

            if not db_plugin:
                db_plugin = plugin_cls(
                    name=name,
                    version=version,
                    description=description,
                    author=author,
                    enabled=True,
                )
                session.add(db_plugin)
            else:
                db_plugin.version = version
                db_plugin.description = description
                db_plugin.author = author

        session.commit()

        # Ensure PluginBase table exists
        enabled_plugins = (
            list(
                session.exec(
                    select(MetadataPluginTable).where(
                        MetadataPluginTable.enabled == True
                    )
                ).all()
            )
            + list(
                session.exec(
                    select(IndexerPlugin).where(IndexerPlugin.enabled == True)
                ).all()
            )
            + list(
                session.exec(
                    select(DownloadClientPlugin).where(
                        DownloadClientPlugin.enabled == True
                    )
                ).all()
            )
            + list(
                session.exec(
                    select(GenericPlugin).where(GenericPlugin.enabled == True)
                ).all()
            )
        )

        for plugin in enabled_plugins:
            manifest_file = PLUGIN_DIR / plugin.name / "manifest.yaml"
            if manifest_file.exists():
                manifest = yaml.safe_load(manifest_file.open())
                plugin_manager.load_plugin_from_manifest(plugin.name, manifest)
                # try:
                #     plugin_manager.load_plugin_from_manifest(plugin.name, manifest)
                # except Exception as e:
                #     print(f"Failed to load plugin {plugin.name}: {e}")

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
        NotificationMessage(
            message="Backend server is restarting..."
        )
    )
    
    async def delayed_restart():
        await asyncio.sleep(1)
        restart_server()
    
    # Schedule restart as background task to allow response to be sent
    background_tasks.add_task(delayed_restart)
    
    return {
        "success": True,
        "message": "Backend server restart initiated"
    }

app.include_router(core.router, prefix="/api/v1", tags=["core"])
app.include_router(metadata.router, prefix="/api/v1", tags=["metadata"])
app.include_router(system.router, prefix="/api/v1", tags=["system"])
