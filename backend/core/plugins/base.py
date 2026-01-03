from abc import ABC, abstractmethod
from pathlib import Path
import os

## TODO: Try Avoid using Any
from typing import Any, Optional
from fastapi import APIRouter

class BasePlugin(ABC):
    """Base interface for all plugins."""

    name: str
    version: str
    description: str = ""
    enabled: bool = True  # Default to enabled

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
    
    # Optional methods for service-type plugins (metadata, indexer, download client)
    
    # TODO: Consider raising NotImplementedError in these methods instead of returning [].
    def get_available_sources(self) -> list[dict[str, Any]]:
        """Return metadata sources this plugin can provide.
        
        Returns:
            List of source definitions with name, description, and config schema
            
        Example:
            [
                {
                    "name": "RanobeDB Main",
                    "description": "Primary RanobeDB instance",
                    "config_schema": {
                        "api_key": {"type": "string", "required": False},
                        "base_url": {"type": "string", "default": "https://ranobedb.org"}
                    }
                }
            ]
        """
        return []
    
    def get_available_indexers(self) -> list[dict[str, Any]]:
        """Return indexers this plugin can provide.
        
        Returns:
            List of indexer definitions with name, description, and config schema
        """
        return []
    
    def get_available_clients(self) -> list[dict[str, Any]]:
        """Return download clients this plugin can provide.
        
        Returns:
            List of client definitions with name, description, and config schema
        """
        return []
    
    def get_api_router(self) -> Optional[APIRouter]:
        """Return an APIRouter for this plugin's custom endpoints.
        
        Plugins can override this method to register custom API routes.
        The router will be automatically included in the FastAPI app at
        /api/v1/plugins/{plugin_name}/
        
        Returns:
            fastapi.APIRouter instance or None
            
        Example:
            from fastapi import APIRouter
            
            def get_api_router(self):
                router = APIRouter()
                
                @router.get("/status")
                async def get_status():
                    return {"status": "running"}
                
                return router
        """
        return None
    
    def create_metadata_source(self, config: dict[str, Any]):
        """Factory method to create a configured metadata source instance.
        
        Args:
            config: Configuration dictionary for this source
            
        Returns:
            Configured metadata source object (should inherit from MetadataPlugin interface)
        """
        raise NotImplementedError(f"{self.name} does not provide metadata sources")
    
    def create_indexer(self, config: dict[str, Any]):
        """Factory method to create a configured indexer instance.
        
        Args:
            config: Configuration dictionary for this indexer
            
        Returns:
            Configured indexer object (should inherit from IndexerPlugin interface)
        """
        raise NotImplementedError(f"{self.name} does not provide indexers")
    
    def create_download_client(self, config: dict[str, Any]):
        """Factory method to create a configured download client instance.
        
        Args:
            config: Configuration dictionary for this client
            
        Returns:
            Configured download client object (should inherit from DownloadClientPlugin interface)
        """
        raise NotImplementedError(f"{self.name} does not provide download clients")
    
    def get_scheduler_jobs(self) -> list[dict[str, Any]]:
        """Return scheduled jobs this plugin wants to register.
        
        Each job dict should contain:
            - 'func': Callable to execute
            - 'trigger': Trigger type (e.g. 'interval', 'cron')
            - Additional trigger parameters

        Returns:
            List of job definitions
        """
        return []