from abc import abstractmethod
from .base import BasePlugin

class DownloadClientPlugin(BasePlugin):
    """Plugin that provides access to downloaders for downloading content."""

    @abstractmethod
    async def download(self, content_id) -> bool:
        """Download content using the download client."""
        ...