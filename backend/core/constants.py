from pathlib import Path

STATIC_DIR = Path(__file__).parent / "static"

# Directory inside Docker container for persistent config and plugin data
# __file__ is in backend/core/constants.py, so parent.parent gets us to backend/
BACKEND_DIR = Path(__file__).parent.parent
MOUNT_DIR = BACKEND_DIR / "config"

# Bundled plugins (part of the image)
BUNDLED_PLUGIN_DIR = BACKEND_DIR / "plugins"
# User-installed plugins (in backend/config/plugins/)
USER_PLUGIN_DIR = MOUNT_DIR / "plugins"

# Combined plugin directories to search
PLUGIN_DIRS = [BUNDLED_PLUGIN_DIR, USER_PLUGIN_DIR]

# Directory for storing logs
LOG_DIR = MOUNT_DIR / "logs"

# Log file paths
MAIN_LOG_FILE = LOG_DIR / "main.log"
PLUGIN_LOG_FILE = LOG_DIR / "plugins.log"
