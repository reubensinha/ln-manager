from abc import abstractmethod
from .base import BasePlugin


class IndexerPlugin(BasePlugin):
    """Plugin that provides access to indexers for searching/downloading."""
    
    @abstractmethod
    async def search(self, query: str) -> list[dict]:
        """Search for content using the indexer."""
        ...
        
    @abstractmethod
    async def get_feed(self) -> list[dict]:
        """Get the latest feed items from the indexer."""
        ...
