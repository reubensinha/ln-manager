from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from sqlmodel import Session, select
import yaml

from backend.core.database.database import init_db, engine
from backend.core.database.models import PluginBase, MetadataPluginTable, IndexerPlugin, DownloadClientPlugin, GenericPlugin
from backend.plugin_manager import PluginManager, PLUGIN_DIR, plugin_manager

from .api.v1 import core, metadata


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
                    enabled=True
                )
                session.add(db_plugin)
            else:
                db_plugin.version = version
                db_plugin.description = description
                db_plugin.author = author
            
        session.commit()
        
        # Ensure PluginBase table exists
        enabled_plugins = list(
            session.exec(select(MetadataPluginTable).where(MetadataPluginTable.enabled == True)).all()
        ) + list(
            session.exec(select(IndexerPlugin).where(IndexerPlugin.enabled == True)).all()
        ) + list(
            session.exec(select(DownloadClientPlugin).where(DownloadClientPlugin.enabled == True)).all()
        ) + list(
            session.exec(select(GenericPlugin).where(GenericPlugin.enabled == True)).all()
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

    yield
    # Perform shutdown tasks

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
    "http://127.0.0.1:5173"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def read_root():
    return {"Hello": "World"}

@app.get("/health")
async def health_check():
    return {"status": "ok"}


app.include_router(core.router, prefix="/api/v1", tags=["core"])
app.include_router(metadata.router, prefix="/api/v1", tags=["metadata"])