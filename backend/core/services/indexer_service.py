from fastapi import Depends
from sqlmodel import Session, select
from backend.core.database.database import get_session, engine
from backend.core.database.models import Indexer
from backend.plugin_manager import plugin_manager
from backend.core.plugins.indexer import IndexerPlugin


async def get_all_feeds(session: Session = Depends(get_session)):
    """Get all indexer feeds from all enabled indexer instances.
    
    Args:
        session: Database session
    """
    all_feeds = []
    
    # Query all enabled indexers
    indexers = session.exec(
        select(Indexer).where(Indexer.enabled == True)
    ).all()
    
    for indexer in indexers:
        feed = await get_feed(indexer.id, session)
        if feed:
            all_feeds.extend(feed)
    
    return all_feeds


async def get_feed(indexer_id, session: Session = Depends(get_session)):
    """Get indexer feed from a specific indexer instance.
    
    Args:
        indexer_id: UUID of the Indexer
        session: Database session
    """
    indexer = session.get(Indexer, indexer_id)
        
    if not indexer or not indexer.enabled:
        return None
    
    if not indexer.plugin:
        return None
    
    # Get the plugin instance
    plugin = plugin_manager.get_plugin(indexer.plugin.name)
    if not plugin:
        return None
    
    indexer_instance = None
    try:
        # Use plugin's factory method to create configured indexer
        indexer_instance = plugin.create_indexer(indexer.config or {})
        if not isinstance(indexer_instance, IndexerPlugin):
            return None
        
        return await indexer_instance.get_feed()
    finally:
        # Clean up if indexer has cleanup method
        if indexer_instance and hasattr(indexer_instance, 'stop'):
            indexer_instance.stop()


async def search_all_indexers(query, session: Session = Depends(get_session)):
    """Search all enabled indexer instances.
    
    Args:
        query: Search query
        session: Database session
    """
    all_results = []
    
    # Query all enabled indexers
    indexers = session.exec(
        select(Indexer).where(Indexer.enabled == True)
    ).all()
    
    for indexer in indexers:
        results = await search_indexer(indexer.id, query, session)
        if results:
            all_results.extend(results)
    
    return all_results


async def search_indexer(indexer_id, query, session: Session = Depends(get_session)):
    """Search a specific indexer instance.
    
    Args:
        indexer_id: UUID of the Indexer
        query: Search query
        session: Database session
    """
    indexer = session.get(Indexer, indexer_id)
    
    print(f"[DEBUG] search_indexer called with indexer_id={indexer_id}, query={query}")
    
    if not indexer:
        print(f"[DEBUG] Indexer not found: {indexer_id}")
        return None
        
    if not indexer.enabled:
        print(f"[DEBUG] Indexer '{indexer.name}' is disabled")
        return None
    
    if not indexer.plugin:
        print(f"[DEBUG] Indexer '{indexer.name}' has no plugin")
        return None
    
    # Get the plugin instance
    plugin = plugin_manager.get_plugin(indexer.plugin.name)
    if not plugin:
        print(f"[DEBUG] Plugin '{indexer.plugin.name}' not found in plugin_manager")
        return None
    
    indexer_instance = None
    try:
        # Use plugin's factory method to create configured indexer
        indexer_instance = plugin.create_indexer(indexer.config or {})
        if not isinstance(indexer_instance, IndexerPlugin):
            print(f"[DEBUG] Created instance is not an IndexerPlugin: {type(indexer_instance)}")
            return None
        
        return await indexer_instance.search(query)
    finally:
        # Clean up if indexer has cleanup method
        if indexer_instance and hasattr(indexer_instance, 'stop'):
            indexer_instance.stop()
    
