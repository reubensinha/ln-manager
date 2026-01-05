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
)


from .api.v1 import core, metadata, system, plugins, indexers

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

            ## TODO: Add unavailable field to source/indexer/client, and set/unset based on whether it exists.
            if manifest_file and manifest_file.exists():
                manifest = yaml.safe_load(manifest_file.open())
                plugin_instance = plugin_manager.load_plugin_from_manifest(plugin.name, manifest)
                
                # Register plugin's metadata sources in database
                try:
                    available_sources = plugin_instance.get_available_sources()
                    advertised_names = {s["name"] for s in available_sources}
                    
                    # Get all existing sources for this plugin
                    existing_sources = session.exec(
                        select(MetadataSource).where(MetadataSource.plugin_id == plugin.id)
                    ).all()
                    
                    # Disable sources that are no longer advertised
                    for existing in existing_sources:
                        if existing.name not in advertised_names:
                            existing.enabled = False
                            print(f"Disabled metadata source '{existing.name}' (no longer advertised by {plugin.name})")
                    
                    # Add new advertised sources (don't auto re-enable disabled ones)
                    for source_info in available_sources:
                        existing = session.exec(
                            select(MetadataSource)
                            .where(MetadataSource.name == source_info["name"])
                            .where(MetadataSource.plugin_id == plugin.id)
                        ).first()
                        
                        if not existing:
                            # Create new source
                            metadata_source = MetadataSource(
                                name=source_info["name"],
                                version=plugin.version,
                                author=plugin.author,
                                description=source_info.get("description"),
                                config={},  # Default empty config
                                enabled=True,
                                plugin_id=plugin.id
                            )
                            session.add(metadata_source)
                            print(f"Registered new metadata source '{source_info['name']}' from {plugin.name}")
                except NotImplementedError:
                    pass  # Plugin doesn't support metadata sources
                
                # Register plugin's indexers in database
                try:
                    available_indexers = plugin_instance.get_available_indexers()
                    
                    # Only auto-register indexers that are NOT user-configurable
                    auto_register_indexers = [
                        i for i in available_indexers 
                        if not i.get("user_configurable", False)
                    ]
                    advertised_names = {i["name"] for i in auto_register_indexers}
                    
                    # Get all existing indexers for this plugin
                    existing_indexers = session.exec(
                        select(Indexer).where(Indexer.plugin_id == plugin.id)
                    ).all()
                    
                    # Only disable auto-registered indexers that are no longer advertised
                    # Don't touch user-configured indexers (those with custom names/configs)
                    for existing in existing_indexers:
                        # Check if this looks like an auto-registered indexer
                        # Auto-registered indexers have empty config dicts
                        if (existing.config is None or existing.config == {}) and existing.name not in advertised_names:
                            existing.enabled = False
                            print(f"Disabled indexer '{existing.name}' (no longer advertised by {plugin.name})")
                    
                    # Add new advertised indexers (don't auto re-enable disabled ones)
                    for indexer_info in auto_register_indexers:
                        existing = session.exec(
                            select(Indexer)
                            .where(Indexer.name == indexer_info["name"])
                            .where(Indexer.plugin_id == plugin.id)
                        ).first()
                        
                        if not existing:
                            indexer = Indexer(
                                name=indexer_info["name"],
                                version=plugin.version,
                                author=plugin.author,
                                description=indexer_info.get("description"),
                                config={},
                                enabled=True,
                                plugin_id=plugin.id
                            )
                            session.add(indexer)
                            print(f"Registered new indexer '{indexer_info['name']}' from {plugin.name}")
                except NotImplementedError:
                    pass  # Plugin doesn't support indexers
                
                # Register plugin's download clients in database
                try:
                    available_clients = plugin_instance.get_available_clients()
                    advertised_names = {c["name"] for c in available_clients}
                    
                    # Get all existing clients for this plugin
                    existing_clients = session.exec(
                        select(DownloadClient).where(DownloadClient.plugin_id == plugin.id)
                    ).all()
                    
                    # Disable clients that are no longer advertised
                    for existing in existing_clients:
                        if existing.name not in advertised_names:
                            existing.enabled = False
                            print(f"Disabled download client '{existing.name}' (no longer advertised by {plugin.name})")
                    
                    # Add new advertised clients (don't auto re-enable disabled ones)
                    for client_info in available_clients:
                        existing = session.exec(
                            select(DownloadClient)
                            .where(DownloadClient.name == client_info["name"])
                            .where(DownloadClient.plugin_id == plugin.id)
                        ).first()
                        
                        if not existing:
                            download_client = DownloadClient(
                                name=client_info["name"],
                                version=plugin.version,
                                author=plugin.author,
                                description=client_info.get("description"),
                                config={},
                                enabled=True,
                                plugin_id=plugin.id
                            )
                            session.add(download_client)
                            print(f"Registered new download client '{client_info['name']}' from {plugin.name}")
                except NotImplementedError:
                    pass  # Plugin doesn't support download clients
        
        session.commit()

        # Register scheduled jobs from all enabled plugins
        # Plugins decide their own scheduling logic and requirements
        for plugin_name, plugin_instance in plugin_manager.plugins.items():
            try:
                jobs = plugin_instance.get_scheduler_jobs()
                
                for job_config in jobs:
                    scheduler.add_job(**job_config)
                    print(f"Scheduled job '{job_config.get('id', 'unnamed')}' from {plugin_name} plugin")
                        
            except Exception as e:
                print(f"Error registering scheduled jobs for {plugin_name}: {e}")

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
app.include_router(plugins.router, prefix="/api/v1", tags=["plugins"])
app.include_router(indexers.router, prefix="/api/v1", tags=["indexers"])

# Include plugin-registered API routers
for plugin_name, router in plugin_manager.get_plugin_routers().items():
    app.include_router(
        router,
        prefix=f"/api/v1/plugins/{plugin_name}",
        tags=[f"plugin:{plugin_name}"]
    )


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
