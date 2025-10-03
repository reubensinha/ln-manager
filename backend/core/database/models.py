from typing import TYPE_CHECKING
from sqlmodel import Field, SQLModel, Relationship
import uuid

# if TYPE_CHECKING:
#     from .plugins import MetadataPlugin, MetadataPluginPublic

################################################################################
# Plugin Models
################################################################################

# TODO: Track plugin dependencies and versions

class Dependency(SQLModel, table=True):
    """Represents a dependency required by a plugin."""
    name: str = Field(primary_key=True)
    version: str | None = None

class PluginBase(SQLModel):
    """Base class for plugins to allow for future extensions."""
    name: str
    version: str
    description: str | None = None
    author: str | None = None
    enabled: bool = Field(default=True)

class GenericPlugin(PluginBase, table=True):
    """A generic plugin that doesn't fit into other categories."""
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)


class MetadataPluginTable(PluginBase, table=True):
    """Plugin that provides metadata for searching series"""
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    
    series: list["Series"] = Relationship(back_populates="plugin")

class MetadataPluginPublic(PluginBase):
    """Public representation of the MetadataPlugin."""
    id: uuid.UUID
    series: list["SeriesPublic"] = []

class IndexerPlugin(PluginBase, table=True):
    """Plugin that provides access to indexers for searching/downloading."""
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)


class DownloadClientPlugin(PluginBase, table=True):
    """Plugin that provides access to downloaders for downloading content."""
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)


################################################################################
# Database Models
################################################################################
# TODO: Add created_at, updated_at timestamps to all models
# TODO: Modify models 

class CollectionSeriesGroupLink(SQLModel, table=True):
    """Link table for many-to-many relationship between Collection and SeriesGroup."""
    collection_id: uuid.UUID = Field(foreign_key="collection.id", primary_key=True)
    seriesgroup_id: uuid.UUID = Field(foreign_key="seriesgroup.id", primary_key=True)
    

class CollectionBase(SQLModel):
    """Base class for Collection to allow for future extensions."""
    name: str = Field(index=True)

class Collection(CollectionBase, table=True):
    """Represents a collection of series created by the user."""
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    
    series_groups: list["SeriesGroup"] = Relationship(back_populates="collections", link_model=CollectionSeriesGroupLink)

class CollectionPublic(CollectionBase):
    """Represents a publicly viewable collection of series."""
    id: uuid.UUID
    series_groups: list["SeriesGroupPublic"] = []
    

class SeriesGroupBase(SQLModel):
    """Base class for SeriesGroup to allow for future extensions."""
    title: str = Field(index=True)
    description: str | None = None

class SeriesGroup(SeriesGroupBase, table=True):
    """A single object representing a single series from all metadata sources."""
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    
    collections: list[Collection] = Relationship(back_populates="seriesgroups", link_model=CollectionSeriesGroupLink)
    series: list["Series"] = Relationship(back_populates="seriesgroup")

class SeriesGroupPublic(SeriesGroupBase):
    """A single object representing a single series from all metadata sources."""
    id: uuid.UUID
    collections: list[CollectionPublic] = []
    series: list["SeriesPublic"] = []


class SeriesBase(SQLModel):
    title: str = Field(index=True)
    author: str | None = Field(default=None, index=True)
    description: str | None = None

    source_id: uuid.UUID | None = Field(foreign_key="metadataplugin.id", ondelete="SET NULL")       # TODO: Decide what to do on delete
    group_id: uuid.UUID | None = Field(foreign_key="seriesgroup.id", ondelete="SET NULL")

class Series(SeriesBase, table=True):
    """A single series from a single metadata source."""
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    
    plugin: "MetadataPluginTable" = Relationship(back_populates="series")
    group: SeriesGroup = Relationship(back_populates="series")
    
    books: list["Book"] = Relationship(back_populates="series", cascade_delete=True)
    chapters: list["Chapter"] = Relationship(back_populates="series", cascade_delete=True)

class SeriesPublic(SeriesBase):
    """A single series from a single metadata source."""
    id: uuid.UUID
    plugin: "MetadataPluginPublic"
    group: SeriesGroupPublic
    books: list["BookPublic"] = []
    chapters: list["ChapterPublic"] = []

# TODO: Make volume field decimal
class BookBase(SQLModel):
    title: str = Field(index=True)
    author: str | None = Field(default=None, index=True)
    description: str | None = None
    volume: int | None = Field(default=None, index=True)

    series_id: uuid.UUID = Field(foreign_key="series.id", ondelete="CASCADE")

class Book(BookBase, table=True):
    """Book contained in a series."""
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    
    series: Series = Relationship(back_populates="book")
    releases: list["Release"] = Relationship(back_populates="book", cascade_delete=True)    

class BookPublic(BookBase):
    """Book contained in a series."""
    id: uuid.UUID
    series: SeriesPublic
    
    releases: list["ReleasePublic"] = []

# TODO: Make number and volume field decimal
class ChapterBase(SQLModel):
    title: str = Field(index=True)
    author: str | None = Field(default=None, index=True)
    number: int | None = Field(default=None, index=True)
    volume: int | None = Field(default=None, index=True)
    description: str | None = None
    
    series_id: uuid.UUID = Field(foreign_key="series.id", ondelete="CASCADE")

class Chapter(ChapterBase, table=True):
    """Chapter contained in a book."""
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)

    series: "Series" = Relationship(back_populates="chapters")
    releases: list["Release"] = Relationship(back_populates="chapter", cascade_delete=True)

class ChapterPublic(ChapterBase):
    """Chapter contained in a book."""
    id: uuid.UUID
    series: SeriesPublic
    
    releases: list["ReleasePublic"] = []

## Releases are expected to be linked to either a chapter or book but not both.
class ReleaseBase(SQLModel):
    url: str = Field(index=True)
    format: str | None = None
    release_date: str | None = None  # ISO 8601 date string # TODO: Check if date type is more appropriate

    chapter_id: uuid.UUID | None = Field(default=None, foreign_key="chapter.id", ondelete="CASCADE")
    book_id: uuid.UUID | None = Field(default=None, foreign_key="book.id", ondelete="SET NULL")

class Release(ReleaseBase, table=True):
    """A release (downloadable file) for a chapter."""
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)

    chapter: Chapter | None = Relationship(back_populates="releases")
    book: Book | None = Relationship(back_populates="releases")


class ReleasePublic(ReleaseBase):
    """A release (downloadable file) for a chapter."""
    id: uuid.UUID
    chapter: ChapterPublic | None = None
    book: BookPublic | None = None