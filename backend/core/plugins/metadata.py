# backend/core/plugins/metadata.py
from abc import abstractmethod
from typing import Any

from pydantic import BaseModel
from sqlmodel import Session
from .base import BasePlugin

from backend.core.database.models import SeriesBase, BookBase, ChapterBase, ReleaseBase

class BookFetchModel(BookBase):
    releases: list[ReleaseBase] = []

class ChapterFetchModel(ChapterBase):
    releases: list[ReleaseBase] = []

class SeriesFetchModel(BaseModel):
    series: SeriesBase
    books: list[BookFetchModel] = []
    chapters: list[ChapterFetchModel] = []

class MetadataPlugin(BasePlugin):
    """Plugins that provide metadata (series search, details)."""

    @abstractmethod
    async def search_series(self, query: str) -> list[SeriesBase]:
        """
        Search for a series by name/keywords.

        Returns:
            List of Series objects with minimal info (id, title, etc.).
        """
        ...

    @abstractmethod
    async def fetch_series(self, external_id: str) -> SeriesFetchModel:
        """
        Fetch full metadata for a single series.

        Args:
            external_id (str): The external ID of the series to fetch.

        Returns:
            SeriesFetchModel: A model containing the series metadata, a list of books,
            a list of chapters, and a list of releases. If they exist.
        """
        ...