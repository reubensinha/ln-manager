# LN-Manager

A self-hosted web application for managing your light novel collection with automatic metadata fetching and release tracking.

## Features

- **Library Management** - Track your light novel collection with series and book information
- **Release Calendar** - View upcoming and past releases in calendar format
- **Automatic Metadata** - Fetches cover images, release dates, and series info from RanobeDB
- **Search** - Quick search for series to add to your library (`Ctrl+K` / `Cmd+K`)
- **Notifications** - Track metadata updates and changes

## Screenshots

- _Coming soon_

## Installation

### Docker (Recommended)

Create a `docker-compose.yml` file:

```yaml
services:
  ln-manager:
    image: ghcr.io/reubensinha/ln-manager:latest
    container_name: ln-manager
    restart: unless-stopped

    ports:
      - "9583:9583"

    volumes:
      # Database, plugins, and plugin data
      - ./config/backend:/app/backend/config/
      # Frontend plugins
      - ./config/frontend/plugins:/app/frontend/src/plugins/
```

Then run:

```bash
docker-compose up -d
```

Access the application at `http://localhost:9583`

**Volume Mounts:**

- `./config/backend` - Database (SQLite), installed plugins, and plugin data
- `./config/frontend/plugins` - Custom frontend plugin components

**Configuration:**

- Change port by modifying `9583:9583` to `YOUR_PORT:9583`
- All data persists in the mounted volumes

### Manual Installation (Development)

**Requirements**: Python 3.9+, Node.js 18+

1. Clone the repository:

   ```bash
   git clone https://github.com/reubensinha/ln-manager.git
   cd ln-auto-v2
   ```

2. Install and run backend:

   ```bash
   cd backend
   pip install -r requirements.txt
   fastapi dev  # Runs on http://localhost:8000
   ```

3. Install and run frontend (separate terminal):

   ```bash
   cd frontend
   npm install
   yarn dev  # Runs on http://localhost:5173
   ```

</details>

## Usage

1. Open `http://localhost:9583` in your browser
2. Press `Ctrl+K` (or `Cmd+K` on Mac) to open search
3. Search for a light novel series
4. Click a result and add it to your library
5. Navigate between Library, Calendar, and Settings pages

**Keyboard Shortcuts:**

- `Ctrl+K` / `Cmd+K` - Open search

## Architecture

### Backend (Python)

- **FastAPI** - REST API framework
- **SQLModel** - Database ORM (SQLite)
- **APScheduler** - Automatic metadata refresh
- **Plugin System** - Dynamic plugin loading

### Frontend (TypeScript)

- **React 18** - UI framework
- **Mantine** - Component library
- **Vite** - Build tool
- **Axios** - HTTP client

### Current Plugins

- **RanobeDB** (Metadata) - Fetches series info, covers, and release dates

## Plugin Development

See [backend/ReadMe.md](backend/ReadMe.md) for creating metadata providers, indexers, or download clients. The `backend/plugins/RanobeDB/` directory contains a complete example.

## Contributing

For development setup and contribution guidelines, see [backend/ReadMe.md](backend/ReadMe.md) and [frontend/ReadMe.md](frontend/ReadMe.md).

**Quick start for contributors:**

1. Fork and clone the repository
2. Follow manual installation steps above
3. Make changes and test
4. Submit a pull request

## Known Issues

- Restart backend endpoint may not work properly in production
- Search doesn't update existing series list until hard refresh (`Ctrl+Shift+R`)

See [TODOs.md](TODOs.md) for full list of planned features and known issues.

## Acknowledgments

- [RanobeDB](https://ranobedb.org/) - Light novel metadata
- [FastAPI](https://fastapi.tiangolo.com/) - Backend framework
- [Mantine](https://mantine.dev/) - UI components

---

**Status**: Active Development
