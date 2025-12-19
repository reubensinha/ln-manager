# TODO: Handle plugin name collisions.
import subprocess
import importlib
import sys
from pathlib import Path
from typing import Dict, Type

from backend.core.plugins.base import BasePlugin

# Bundled plugins (part of the image)
BUNDLED_PLUGIN_DIR = Path(__file__).parent / "plugins"
# User-installed plugins (in backend/config/plugins/)
backend_dir = Path(__file__).parent
USER_PLUGIN_DIR = backend_dir / "config" / "plugins"

# Combined plugin directories to search
PLUGIN_DIRS = [BUNDLED_PLUGIN_DIR, USER_PLUGIN_DIR]


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
        
        # Ensure user plugin directory exists
        USER_PLUGIN_DIR.mkdir(parents=True, exist_ok=True)

    def install_dependencies(self, dependencies: list[str]):
        ## TODO: Manage dependencies somehow.
        for dep in dependencies:
            subprocess.check_call([sys.executable, "-m", "pip", "install", dep])

    def find_plugin_path(self, folder_name: str) -> Path | None:
        """Find the plugin directory, checking bundled first, then user plugins."""
        for plugin_dir in self.plugin_dirs:
            plugin_path = plugin_dir / folder_name
            if plugin_path.exists() and plugin_path.is_dir():
                return plugin_path
        return None
    
    def load_plugin_from_manifest(self, folder_name: str, manifest: dict):
        """Load and instantiate a plugin from its manifest.
        
        The plugin instance is kept running for the lifetime of the application.
        """
        entry_point = manifest.get("entry_point")
        if not entry_point:
            raise ValueError("Manifest missing 'entry_point' field")
        
        dependencies = manifest.get("dependencies", [])
        if dependencies:
            self.install_dependencies(dependencies)

        module_name, class_name = entry_point.split(":")
        
        # Check if this is a bundled plugin or user plugin
        plugin_path = self.find_plugin_path(folder_name)
        if not plugin_path:
            raise ValueError(f"Plugin folder '{folder_name}' not found")
        
        # Use bundled module path for bundled plugins
        if plugin_path.parent == BUNDLED_PLUGIN_DIR:
            module_path = f"backend.plugins.{folder_name}.{module_name}"
        else:
            # For user plugins, we need to add the directory to sys.path and import dynamically
            if str(USER_PLUGIN_DIR) not in sys.path:
                sys.path.insert(0, str(USER_PLUGIN_DIR))
            module_path = f"{folder_name}.{module_name}"
        
        module = importlib.import_module(module_path)
        cls: Type[BasePlugin] = getattr(module, class_name)
        
        # Instantiate the plugin
        plugin_name = manifest["name"]
        instance = cls()
        self.plugins[plugin_name] = instance
        
        # Call start() to initialize the plugin
        instance.start()
        
        return instance

    def unload_plugin(self, name: str) -> bool:
        """Unload a plugin by name, calling its stop() method for cleanup.
        
        Returns:
            bool: True if plugin was unloaded, False if not found
        """
        if name in self.plugins:
            plugin = self.plugins[name]
            plugin.stop()
            del self.plugins[name]
            return True
        return False
    
    def shutdown_all_plugins(self) -> None:
        """Call stop() on all loaded plugins for cleanup during application shutdown."""
        ## TODO: call unload_plugin() instead?
        for name, plugin in list(self.plugins.items()):
            try:
                plugin.stop()
            except Exception as e:
                # Log but don't stop shutdown process
                print(f"Error stopping plugin '{name}': {e}")
    
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

plugin_manager = PluginManager()