# backend/core/plugins/metadata.py
from abc import abstractmethod

# from pydantic import BaseModel
from sqlmodel import SQLModel
from .base import BasePlugin

from backend.core.database.models import SeriesBase, BookBase, ChapterBase, ReleaseBase, SeriesSearchResponse, SeriesDetailsResponse

class BookFetchModel(BookBase):
    """
    Data model for a Book when fetched as part of a Series.

    Inherits all fields from BookBase.

    Fields:
        releases (list[ReleaseBase]): A list of all releases (e.g., digital, print editions) 
                                      associated with this specific book.
    """
    releases: list[ReleaseBase] = []

class ChapterFetchModel(ChapterBase):
    """
    Data model for a Chapter when fetched as part of a Series.

    Inherits all fields from ChapterBase.

    Fields:
        releases (list[ReleaseBase]): A list of all releases associated with this chapter
                                      (e.g., web novel chapters or translated chapters).
    """
    releases: list[ReleaseBase] = []

class SeriesFetchModel(SQLModel):
    """
    The complete data container model returned by MetadataPlugin.fetch_series().

    This aggregates all related data from an external source into a single structure.

    Fields:
        series (SeriesBase): The core series metadata (title, status, etc.).
        books (list[BookFetchModel]): A list of books belonging to this series, 
                                      each including its associated releases.
        chapters (list[ChapterFetchModel]): A list of chapters belonging to this series 
                                            (usually for Web Novels or digital-first content).
    """
    series: SeriesBase
    books: list[BookFetchModel] = []
    chapters: list[ChapterFetchModel] = []

class MetadataPlugin(BasePlugin):
    """Plugins that provide metadata (series search, details)."""

    @abstractmethod
    async def search_series(self, query: str) -> list[SeriesSearchResponse]:
        """
        Search for a series by name/keywords.

        Returns:
            List of Series objects with minimal info (id, title, etc.).
        """
        raise NotImplementedError
    
    @abstractmethod
    async def get_series_by_id(self, external_id: str) -> SeriesDetailsResponse | None:
        """
        Fetch basic metadata for a single series by its external ID.

        Args:
            external_id (str): The external ID of the series to fetch.
        Returns:
            SeriesBase: A model containing the basic series metadata.
        """
        raise NotImplementedError

    @abstractmethod
    async def fetch_series(self, external_id: str) -> SeriesFetchModel | None:
        """
        Fetch full metadata for a single series.

        Args:
            external_id (str): The external ID of the series to fetch.

        Returns:
            SeriesFetchModel: A model containing the series metadata, a list of books,
            a list of chapters, and a list of releases. If they exist.
        """
        raise NotImplementedError