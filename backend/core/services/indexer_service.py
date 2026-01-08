from operator import call
from uuid import UUID
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
    # Convert string UUID to UUID object if needed
    if isinstance(indexer_id, str):
        indexer_id = UUID(indexer_id)
    
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
        
        results = await indexer_instance.get_feed()
        
        # Add indexer name to each result
        if results:
            for result in results:
                result['indexer_name'] = indexer.name
                
                # TODO: Move score and rejections addition to API call layer.
                # Add default score if not present
                if 'score' not in result:
                    result['score'] = 0
                # Add empty rejections list if not present
                if 'rejections' not in result:
                    result['rejections'] = []
        
        return results
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
    # Convert string UUID to UUID object if needed
    if isinstance(indexer_id, str):
        indexer_id = UUID(indexer_id)
    
    indexer = session.get(Indexer, indexer_id)
    
    if not indexer:
        return None
        
    if not indexer.enabled:
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
        
        results = await indexer_instance.search(query)
        
        # Add indexer name to each result
        if results:
            for result in results:
                result['indexer_name'] = indexer.name
                # Add default score if not present
                
                # TODO: Move score and rejections addition to API call layer.
                if 'score' not in result:
                    result['score'] = 0
                # Add empty rejections list if not present
                if 'rejections' not in result:
                    result['rejections'] = []
        
        return results
    finally:
        # Clean up if indexer has cleanup method
        if indexer_instance and hasattr(indexer_instance, 'stop'):
            indexer_instance.stop()
    
