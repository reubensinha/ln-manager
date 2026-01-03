"""API endpoints for plugin discovery and capabilities."""

from typing import Dict, List, Any
from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session

from backend.plugin_manager import plugin_manager
from backend.core.database.database import get_session
from backend.core.services import indexer_service


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


@router.get("/indexers/search")
async def search_all_indexers(
    query: str,
    session: Session = Depends(get_session)
) -> List[Dict[str, Any]]:
    """Search across all enabled indexers.
    
    Args:
        query: Search query string
        session: Database session
        
    Returns:
        Aggregated search results from all enabled indexers
    """
    results = await indexer_service.search_all_indexers(query, session)
    return results or []


@router.get("/indexers/search/{indexer_id}")
async def search_specific_indexer(
    indexer_id: str,
    query: str,
    session: Session = Depends(get_session)
) -> List[Dict[str, Any]]:
    """Search a specific indexer by ID.
    
    Args:
        indexer_id: UUID of the indexer
        query: Search query string
        session: Database session
        
    Returns:
        Search results from the specified indexer
    """
    results = await indexer_service.search_indexer(indexer_id, query, session)
    
    if results is None:
        raise HTTPException(status_code=404, detail="Indexer not found or disabled")
    
    return results


@router.get("/indexers/feed")
async def get_all_indexers_feed(
    session: Session = Depends(get_session)
) -> List[Dict[str, Any]]:
    """Get RSS/feed from all enabled indexers.
    
    Args:
        session: Database session
        
    Returns:
        Aggregated feed items from all enabled indexers
    """
    results = await indexer_service.get_all_feeds(session)
    return results or []


@router.get("/indexers/feed/{indexer_id}")
async def get_indexer_feed_by_id(
    indexer_id: str,
    session: Session = Depends(get_session)
) -> List[Dict[str, Any]]:
    """Get RSS/feed from a specific indexer by ID.
    
    Args:
        indexer_id: UUID of the indexer
        session: Database session
        
    Returns:
        Feed items from the specified indexer
    """
    results = await indexer_service.get_feed(indexer_id, session)
    
    if results is None:
        raise HTTPException(status_code=404, detail="Indexer not found or disabled")
    
    return results
