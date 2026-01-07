# TODO: Handle plugin name collisions.
import subprocess
import importlib
import sys
import logging
from pathlib import Path
from typing import Dict, Type, Any

from backend.core.plugins.base import BasePlugin
from backend.core.constants import BUNDLED_PLUGIN_DIR, USER_PLUGIN_DIR, PLUGIN_DIRS
from backend.core.logging_config import get_logger


logger = get_logger(__name__)


class PluginManager:
    """Manages the loading and lifecycle of plugins.
    
    Plugins are instantiated at startup and kept running. They can:
    - Provide multiple configured sources/indexers/clients (factory pattern)
    - Run continuously for generic functionality (event listeners, background tasks)
    - Register their capabilities and configuration requirements
    """
    
    def __init__(self, plugin_dirs: list[Path] | None = None):
        self.plugin_dirs = plugin_dirs if plugin_dirs is not None else PLUGIN_DIRS
        self.plugins: Dict[str, BasePlugin] = {}  # name -> running instance
        self.plugin_routers: Dict[str, Any] = {}  # name -> APIRouter instance
        
        # Ensure user plugin directory exists
        USER_PLUGIN_DIR.mkdir(parents=True, exist_ok=True)
        logger.debug(f"PluginManager initialized with directories: {self.plugin_dirs}")

    def install_dependencies(self, dependencies: list[str]):
        ## TODO: Manage dependencies somehow.
        logger.info(f"Installing dependencies: {dependencies}")
        for dep in dependencies:
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", dep])
                logger.info(f"Successfully installed dependency: {dep}")
            except Exception as e:
                logger.error(f"Failed to install dependency '{dep}': {e}", exc_info=True)
                raise

    def find_plugin_path(self, folder_name: str) -> Path | None:
        """Find the plugin directory, checking bundled first, then user plugins."""
        for plugin_dir in self.plugin_dirs:
            plugin_path = plugin_dir / folder_name
            if plugin_path.exists() and plugin_path.is_dir():
                logger.debug(f"Found plugin '{folder_name}' at {plugin_path}")
                return plugin_path
        logger.warning(f"Plugin folder '{folder_name}' not found in any plugin directory")
        return None
    
    def load_plugin_from_manifest(self, folder_name: str, manifest: dict):
        """Load and instantiate a plugin from its manifest.
        
        The plugin instance is kept running for the lifetime of the application.
        """
        plugin_name = manifest.get("name", folder_name)
        logger.info(f"Loading plugin: {plugin_name}")
        
        entry_point = manifest.get("entry_point")
        if not entry_point:
            logger.error(f"Plugin '{plugin_name}' manifest missing 'entry_point' field")
            raise ValueError("Manifest missing 'entry_point' field")
        
        dependencies = manifest.get("dependencies", [])
        if dependencies:
            logger.debug(f"Plugin '{plugin_name}' has dependencies: {dependencies}")
            self.install_dependencies(dependencies)

        module_name, class_name = entry_point.split(":")
        logger.debug(f"Plugin '{plugin_name}' entry point: {module_name}:{class_name}")
        
        # Check if this is a bundled plugin or user plugin
        plugin_path = self.find_plugin_path(folder_name)
        if not plugin_path:
            logger.error(f"Plugin folder '{folder_name}' not found")
            raise ValueError(f"Plugin folder '{folder_name}' not found")
        
        # Use bundled module path for bundled plugins
        if plugin_path.parent == BUNDLED_PLUGIN_DIR:
            module_path = f"backend.plugins.{folder_name}.{module_name}"
            logger.debug(f"Loading bundled plugin from: {module_path}")
        else:
            # For user plugins, we need to add the directory to sys.path and import dynamically
            if str(USER_PLUGIN_DIR) not in sys.path:
                sys.path.insert(0, str(USER_PLUGIN_DIR))
                logger.debug(f"Added user plugin directory to sys.path: {USER_PLUGIN_DIR}")
            module_path = f"{folder_name}.{module_name}"
            logger.debug(f"Loading user plugin from: {module_path}")
        
        try:
            module = importlib.import_module(module_path)
            cls: Type[BasePlugin] = getattr(module, class_name)
            
            # Instantiate the plugin
            instance = cls()
            self.plugins[plugin_name] = instance
            logger.info(f"Plugin '{plugin_name}' instantiated successfully")
            
            # Call start() to initialize the plugin
            instance.start()
            logger.info(f"Plugin '{plugin_name}' started successfully")
            
            # Register API router if the plugin provides one
            try:
                router = instance.get_api_router()
                if router is not None:
                    self.plugin_routers[plugin_name] = router
                    logger.info(f"Registered API router for plugin '{plugin_name}'")
            except Exception as e:
                logger.error(f"Error registering API router for '{plugin_name}': {e}", exc_info=True)
            
            return instance
            
        except Exception as e:
            logger.error(f"Failed to load plugin '{plugin_name}': {e}", exc_info=True)
            raise

    def unload_plugin(self, name: str) -> bool:
        """Unload a plugin by name, calling its stop() method for cleanup.
        
        Returns:
            bool: True if plugin was found (unloaded or attempted to unload),
            False if not found.
        """
        if name in self.plugins:
            logger.info(f"Unloading plugin: {name}")
            plugin = self.plugins[name]
            try:
                plugin.stop()
                logger.info(f"Plugin '{name}' stopped successfully")
            except Exception as e:
                # Log but don't prevent further shutdown/unload operations
                logger.error(f"Error stopping plugin '{name}': {e}", exc_info=True)
            else:
                del self.plugins[name]
                # Also remove the router if it exists
                if name in self.plugin_routers:
                    del self.plugin_routers[name]
                    logger.debug(f"Removed API router for plugin '{name}'")
            return True
        logger.warning(f"Attempted to unload non-existent plugin: {name}")
        return False
    
    def shutdown_all_plugins(self) -> None:
        """Call unload_plugin() on all loaded plugins for cleanup during application shutdown."""
        logger.info(f"Shutting down all plugins ({len(self.plugins)} loaded)...")
        for name in list(self.plugins.keys()):
            self.unload_plugin(name)
        logger.info("All plugins shut down")
    
    def get_plugin(self, name: str) -> BasePlugin | None:
        """Get a running plugin instance by name.
        
        Args:
            name: Plugin name
            
        Returns:
            Plugin instance or None if not found
        """
        return self.plugins.get(name)
    
    def get_all_plugins(self) -> Dict[str, BasePlugin]:
        """Get all loaded plugin instances.
        
        Returns:
            Dictionary of plugin_name -> plugin_instance
        """
        return self.plugins
    
    def get_plugin_routers(self) -> Dict[str, Any]:
        """Get all registered plugin API routers.
        
        Returns:
            Dictionary of plugin_name -> APIRouter instance
        """
        return self.plugin_routers

plugin_manager = PluginManager()