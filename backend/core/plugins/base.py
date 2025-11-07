from abc import ABC, abstractmethod
from pathlib import Path
import os
from typing import Any

class BasePlugin(ABC):
    """Base interface for all plugins."""

    name: str
    version: str
    description: str = ""

    def __init__(self, **kwargs: Any):
        # Allow plugins to receive config from DB or user settings
        for k, v in kwargs.items():
            setattr(self, k, v)
        
        # Set up plugin data directory
        self._setup_data_directory()
    
    def _setup_data_directory(self) -> None:
        """
        Automatically set up a persistent data directory for this plugin.
        
        The data directory is:
        - In Docker: /app/backend/config/plugin-data/{plugin_name}/
        - Locally: backend/config/plugin-data/{plugin_name}/
        
        This directory persists across container rebuilds when properly volume-mounted.
        """
        # Get the base plugin-data directory
        base_data_dir = os.environ.get("PLUGIN_DATA_DIR")
        
        if base_data_dir:
            # Docker or custom environment
            data_dir = Path(base_data_dir) / self.name
        else:
            # Local development - use config/plugin-data at backend root
            # Navigate from this file (core/plugins/base.py) up to backend/
            backend_dir = Path(__file__).parent.parent.parent
            data_dir = backend_dir / "config" / "plugin-data" / self.name
        
        # Create the directory if it doesn't exist
        data_dir.mkdir(parents=True, exist_ok=True)
        
        # Make it available to the plugin
        self.data_dir = data_dir

    @abstractmethod
    def start(self) -> None:
        """Called when the plugin is loaded and ready."""
        ...

    @abstractmethod
    def stop(self) -> None:
        """Called when the plugin is unloaded or disabled."""
        ...
