"""API endpoints for plugin discovery and capabilities."""

from typing import Dict, List, Any
from fastapi import APIRouter, HTTPException

from backend.plugin_manager import plugin_manager


router = APIRouter(prefix="/plugins", tags=["plugins"])


@router.get("/")
async def get_all_plugins() -> Dict[str, Any]:
    """Get all loaded plugins with their basic information.
    
    Returns:
        Dictionary mapping plugin names to their basic info
    """
    plugins = plugin_manager.get_all_plugins()
    
    return {
        name: {
            "name": plugin.name,
            "version": plugin.version,
            "description": plugin.description,
            "enabled": plugin.enabled
        }
        for name, plugin in plugins.items()
    }


@router.get("/{plugin_name}/sources")
async def get_available_sources(plugin_name: str) -> List[Dict[str, Any]]:
    """Get available metadata sources from a plugin.
    
    Args:
        plugin_name: Name of the plugin
        
    Returns:
        List of available source configurations
    """
    plugin = plugin_manager.get_plugin(plugin_name)
    if not plugin:
        raise HTTPException(status_code=404, detail=f"Plugin '{plugin_name}' not found")
    
    try:
        sources = plugin.get_available_sources()
        return sources
    except NotImplementedError:
        return []


@router.get("/{plugin_name}/indexers")
async def get_available_indexers(plugin_name: str) -> List[Dict[str, Any]]:
    """Get available indexers from a plugin.
    
    Args:
        plugin_name: Name of the plugin
        
    Returns:
        List of available indexer configurations
    """
    plugin = plugin_manager.get_plugin(plugin_name)
    if not plugin:
        raise HTTPException(status_code=404, detail=f"Plugin '{plugin_name}' not found")
    
    try:
        indexers = plugin.get_available_indexers()
        return indexers
    except NotImplementedError:
        return []


@router.get("/{plugin_name}/clients")
async def get_available_clients(plugin_name: str) -> List[Dict[str, Any]]:
    """Get available download clients from a plugin.
    
    Args:
        plugin_name: Name of the plugin
        
    Returns:
        List of available client configurations
    """
    plugin = plugin_manager.get_plugin(plugin_name)
    if not plugin:
        raise HTTPException(status_code=404, detail=f"Plugin '{plugin_name}' not found")
    
    try:
        clients = plugin.get_available_clients()
        return clients
    except NotImplementedError:
        return []

