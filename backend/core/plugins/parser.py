from typing import TypedDict
from uuid import UUID
from abc import abstractmethod

from backend.core.database.models import Chapter
from .base import BasePlugin

class ParserPlugin(BasePlugin):
    """Plugin that provides access to parsers and matching data to content."""
    
    class ParserResponseModel(TypedDict):
        series: list[UUID]
        book: list[UUID]
        chapters: list[UUID]

    @abstractmethod
    async def parse(self, title: str | None = None, infohash: str | None = None) -> ParserResponseModel:
        """Parse content using the parser."""
        ...