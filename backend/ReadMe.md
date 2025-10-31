# LN-Manager - Backend

FastAPI-based backend for LN-Auto v2. This guide is for contributors and plugin developers who want to understand the backend architecture or create plugins.

## Architecture Overview

The backend is built with FastAPI and follows a modular plugin architecture:

- **API Layer** (`api/v1/`) - REST endpoints for collections, series, books, metadata, and plugins
- **Core Logic** (`core/`) - Business logic, database models, plugin system, and scheduling
- **Plugin System** (`plugins/`) - Extensible plugin architecture for metadata sources, indexers, and download clients
- **Database** - SQLModel ORM with SQLite (default) or PostgreSQL/MySQL support

## 📁 Project Structure

```text
backend/
├── main.py                    # FastAPI app entry point, lifespan management
├── plugin_manager.py          # Plugin discovery and loading
├── requirements.txt           # Python dependencies
│
├── api/v1/                    # Versioned API routes
│   ├── core.py               # Collections, series, books, releases
│   ├── metadata.py           # Metadata search and fetch operations
│   ├── system.py             # Plugins, notifications, system endpoints
│   └── utils.py              # Shared API utilities
│
├── core/                      # Core business logic
│   ├── database/
│   │   ├── database.py       # DB connection and session management
│   │   └── models.py         # SQLModel data models (698 lines!)
│   │
│   ├── plugins/              # Plugin base classes (extend these!)
│   │   ├── base.py          # Base plugin interface
│   │   ├── metadata.py      # MetadataPlugin base class
│   │   ├── indexer.py       # IndexerPlugin base class
│   │   ├── download_client.py  # DownloadClientPlugin base
│   │   └── generic.py       # GenericPlugin base class
│   │
│   ├── services/
│   │   └── metadata_service.py  # Metadata operation logic
│   │
│   ├── scheduler.py          # APScheduler background tasks
│   ├── notifications.py      # WebSocket notification manager
│   └── orchestrator.py       # (TODO) Plugin orchestration
│
└── plugins/                   # Plugin implementations
    ├── RanobeDB/             # Example: RanobeDB metadata plugin
    ├── Jackett/              # (Planned) Indexer integration
    └── qBittorrent/          # (Planned) Download client
```

## Development Setup

### Running the Backend

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Run development server with auto-reload
fastapi dev

# Run with multiple workers (production)
fastapi run
```

### API Documentation

Once running, visit:

- **Swagger UI**: <http://localhost:8000/docs> - Interactive API testing
- **ReDoc**: <http://localhost:8000/redoc> - API reference documentation

## 🗄️ Database

### Models Overview

Key database models (in `core/database/models.py`):

- **Collection** - Top-level organization (e.g., "Light Novels")
- **SeriesGroup** - Groups related series (different editions, languages)
- **Series** - Individual series with metadata
- **Book** - Individual volumes with metadata
- **Release** - Release information (dates, formats, publishers)
- **NotificationMessage** - Notification history
- **PluginBase** - Base plugin configuration
- **MetadataPluginTable**, **IndexerPlugin**, **DownloadClientPlugin** - Plugin-specific tables

### Database Initialization

The database is automatically initialized on app startup:

### Migrations

Currently using SQLModel's built-in table creation. For production, consider setting up Alembic migrations (TODO).

## Background Tasks & Notifications

### Scheduler

The app uses APScheduler for background tasks:

```python
# In main.py
scheduler = AsyncIOScheduler()
scheduler.add_job(
    update_all_series_metadata,
    "interval",
    minutes=UPDATE_SERIES_INTERVAL_MINUTES,  # Default: 60
)
```

**Current scheduled tasks:**

- Metadata refresh for all series

### WebSocket Notifications

Real-time notifications via WebSocket (`/ws` endpoint):

```python
from backend.core.notifications import notification_manager

# Send notification
await notification_manager.send_notification(
    title="Update Complete",
    message="Series metadata refreshed",
    notification_type="success",  # success, info, warning, error
    persist=True  # Save to database
)
```

## 🔌 Plugin Development Guide

### Plugin Types

LN-Auto supports four plugin types:

1. **MetadataPlugin** - Fetch series/book metadata from external sources
2. **IndexerPlugin** - Search for content across indexers (planned)
3. **DownloadClientPlugin** - Interface with download clients (planned)
4. **GenericPlugin** - Custom functionality

### Creating a Metadata Plugin

#### Step 1: Plugin Structure

Create a directory in `backend/plugins/`:

```text
plugins/YourPlugin/
├── __init__.py              # Empty or package initialization
├── manifest.yaml            # Plugin metadata (required)
└── your_plugin.py           # Plugin implementation
```

#### Step 2: Write the Manifest

Create `manifest.yaml`:

```yaml
name: YourPlugin
version: 1.0.0
description: Brief description of your plugin
author: Your Name
type: metadata # metadata, indexer, download_client, or generic
entry_point: your_plugin:YourPluginClass
dependencies: # Python packages (installed via pip)
  - httpx
  - beautifulsoup4
```

#### Step 3: Implement the Plugin Class

Create `your_plugin.py`:

```text
See backend.plugins.RanobeDB.ranobedb.py for example
```

#### Step 4: Key Data Models

Important models to understand (from `core/database/models.py`):

**SeriesSearchResponse** - For search results:

```python
class SeriesSearchResponse(SQLModel):
    id: str                    # Your unique ID
    title: str                 # English/primary title
    title_orig: Optional[str]  # Original language title
    romaji: Optional[str]      # Romaji title (for Japanese)
    description: Optional[str]
    cover_url: Optional[str]
    lang: Optional[str]        # Language code (ja, en, etc.)
    # ... many more fields
```

**SeriesDetailsResponse** - For full series data:

- Includes all SeriesSearchResponse fields
- Plus: books, releases, publishers, etc.

**BookFetchModel** - For individual books:

- Title, description, cover
- Release dates, formats, ISBNs
- Publisher information

#### Step 5: Testing Your Plugin

1. Place your plugin with manifest in `backend/plugins/YourPlugin/`
2. Restart the backend server
3. The plugin will be auto-discovered and loaded
4. Test via API: `POST /api/v1/metadata/search`

### Plugin Best Practices

1. **Error Handling**: Always handle API errors gracefully

   ```python
   try:
       response = await client.get(url)
       response.raise_for_status()
   except httpx.HTTPError as e:
       # Log error and return empty/default data
       return []
   ```

2. **Rate Limiting**: Respect API rate limits

   ```python
   from pyrate_limiter import Duration, Limiter, RequestRate

   rate = RequestRate(10, Duration.SECOND)
   limiter = Limiter(rate)
   ```

3. **Image Handling**: Store images locally when possible

   ```python
   # See RanobeDB plugin for example
   async def download_image(url: str, save_path: Path):
       # Download and save cover images
       pass
   ```

4. **Async Operations**: Use async/await for all I/O

   ```python
   import httpx

   async with httpx.AsyncClient() as client:
       response = await client.get(url)
   ```

5. **Type Hints**: Always use type hints for better IDE support

6. **Documentation**: Add docstrings to all methods

### Example: RanobeDB Plugin

See `backend/plugins/RanobeDB/` for a complete, working example:

- `ranobedb.py` - Main plugin class
- `ranobedb_api.py` - API client implementation
- `rate_limiter.py` - Rate limiting wrapper
- `manifest.yaml` - Plugin manifest

### Plugin Lifecycle

1. **Discovery**: `plugin_manager` scans `plugins/` directory on startup
2. **Loading**: Reads `manifest.yaml`, installs dependencies (if listed)
3. **Instantiation**: Imports and creates plugin instance
4. **Registration**: Adds to database and makes available via API
5. **Usage**: Called by API endpoints and services

**Note on Dependencies**: The project currently does not have a proper dependency manager for plugins. While you can list dependencies in `manifest.yaml`, there is no isolation between plugin environments, and dependency conflicts may occur. Manual dependency management is required.

### Packaging Plugins (.lna files)

To distribute your plugin, package it as a `.lna` (LN-Auto) file:

1. **Structure your plugin package**:

   ```text
   YourPlugin/
   ├── manifest.yaml           # Required at root level
   ├── backend/                # Backend plugin code
   │   ├── __init__.py
   │   └── your_plugin.py
   └── frontend/               # Optional: Frontend components
       └── manifest.tsx
   ```

2. **Create the .lna archive**:

   ```bash
   # From the directory containing your plugin folder structure
   cd YourPlugin
   zip -r YourPlugin.lna manifest.yaml backend/ frontend/
   ```

   **Important structure requirements:**

   - `manifest.yaml` must be at the root of the archive
   - Backend code must be in a `backend/` directory
   - Frontend code (optional) must be in a `frontend/` directory with `manifest.tsx`

3. **Users can install** the `.lna` file via:
   - API: `POST /api/v1/plugins/install` with the `.lna` file upload
   - UI: Upload through the Plugins page (Settings → Plugins)

**Note**: The `.lna` file is just a `.zip` file with a specific internal structure. The installer extracts and places:

- `backend/` contents → `backend/plugins/YourPlugin/`
- `frontend/` contents → `frontend/src/plugins/YourPlugin/` (if present)
- Copies `manifest.yaml` into the backend plugin directory

### Debugging Plugins

Check the console output when the backend starts for plugin loading information. Look for:

- Plugin discovery messages
- Dependency installation output
- Any import or instantiation errors

Common issues:

- **Plugin not loading**: Check `manifest.yaml` syntax and `entry_point` format
- **Import errors**: Ensure all dependencies are listed in `manifest.yaml`
- **Runtime errors**: Check that all required methods are implemented

## Testing & Logging

### Testing

A formal test suite has not been implemented yet. I am welcome to anyone wanting to implement them.
