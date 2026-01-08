from abc import abstractmethod
from .base import BasePlugin


class DownloadClientPlugin(BasePlugin):
    """Plugin that provides access to downloaders for downloading content."""

    # TODO: torrent_file? Would that be a path or raw data?
    @abstractmethod
    async def download(
        self,
        info_hash: str | None = None,
        magnet_link: str | None = None,
        torrent_file: str | None = None,
    ) -> bool:
        """Download content using the download client."""

        raise NotImplementedError

    @abstractmethod
    async def test_connection(self) -> dict:
        """Retrieve the current status of the download client."""

        raise NotImplementedError

    @abstractmethod
    async def get_all_downloads(self) -> list[dict]:
        """Retrieve a list of all current downloads with status from the download client."""

        raise NotImplementedError

    @abstractmethod
    async def remove_download(self, info_hash: str, delete_data: bool = False) -> bool:
        """Remove a download from the download client.

        Args:
            info_hash: Info hash of the download to remove
            delete_data: Whether to delete the downloaded data as well
        Returns:
            True if the download was successfully removed, False otherwise
        """

        raise NotImplementedError
