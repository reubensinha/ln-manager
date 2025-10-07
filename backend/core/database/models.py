# from __future__ import annotations
from datetime import date
from sqlmodel import Field, SQLModel, Relationship
from typing import Literal
import uuid

# if TYPE_CHECKING:
#     from .plugins import MetadataPlugin, MetadataPluginPublic

LanguageCode = Literal[
    "ja",
    "en",
    "zh-Hans",
    "zh-Hant",
    "fr",
    "es",
    "ko",
    "ar",
    "bg",
    "ca",
    "cs",
    "ck",
    "da",
    "de",
    "el",
    "eo",
    "eu",
    "fa",
    "fi",
    "ga",
    "gd",
    "he",
    "hi",
    "hr",
    "hu",
    "id",
    "it",
    "iu",
    "mk",
    "ms",
    "la",
    "lt",
    "lv",
    "nl",
    "no",
    "pl",
    "pt-pt",
    "pt-br",
    "ro",
    "ru",
    "sk",
    "sl",
    "sr",
    "sv",
    "ta",
    "th",
    "tr",
    "uk",
    "ur",
    "vi",
]
# Create a reusable Literal type that includes None as a valid option


################################################################################
# Plugin Models
################################################################################

# TODO: Track plugin dependencies and versions


class Dependency(SQLModel, table=True):
    """
    Represents a dependency required by a plugin (e.g., a required Python package).

    Fields:
        name (str): The name of the dependency (Primary Key).
        version (str | None): The required version or version range.
    """

    name: str = Field(primary_key=True)
    version: str | None = None


class PluginBase(SQLModel):
    """
    Base class containing common descriptive fields for all plugin types.

    Fields:
        name (str): The display name of the plugin.
        version (str): The version string of the plugin.
        description (str | None): A brief explanation of what the plugin does.
        author (str | None): The creator of the plugin.
        enabled (bool): Whether the plugin is currently active and running.
    """

    name: str
    version: str
    description: str | None = None
    author: str | None = None
    enabled: bool = Field(default=True)


class GenericPlugin(PluginBase, table=True):
    """
    A concrete plugin model for plugins that don't fit into other, more specific categories.
    """

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)


class MetadataPluginTable(PluginBase, table=True):
    """
    Plugin that provides metadata for searching and fetching series details.

    Relationships:
        series (list["Series"]): All specific series entries sourced by this plugin.
    """

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)

    series: list["Series"] = Relationship(back_populates="plugin")


# class MetadataPluginPublic(PluginBase):
#     """
#     Public API representation of the MetadataPlugin.
#     """

#     id: uuid.UUID
#     series: list["SeriesPublic"] = []


class IndexerPlugin(PluginBase, table=True):
    """
    Plugin that provides access to indexers for searching and locating downloadable files.
    """

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)


class DownloadClientPlugin(PluginBase, table=True):
    """
    Plugin that provides access to download clients (e.g., torrent clients, web downloaders)
    for initiating and managing content downloads.
    """

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)


################################################################################
# Search Response Models
################################################################################


class SeriesSearchResponse(SQLModel):
    """
    Represents the response model for a series search query.

    Fields:
        id (uuid.UUID): The unique identifier for the series.
        title (str): The title of the series.
        author (str | None): The author of the series.
        description (str | None): A brief description of the series.
        img_url (str | None): The URL to the cover image of the series.
    """

    external_id: str
    title: str
    volumes: int | None = None
    chapters: int | None = None

    language: LanguageCode | None = None
    orig_language: LanguageCode | None = None
    img_url: str | None = None


PublishingStatus = Literal["unknown", "ongoing", "completed", "hiatus", "stalled", "cancelled"]

class ExternalLink(SQLModel):
    name: str
    url: str
    icon_url: str | None = None
    
class StaffRole(SQLModel):
    name: str
    role: str
    
class SeriesDetailsResponse(SQLModel):
    external_id: str
    title: str
    romaji: str | None = None
    title_orig: str | None = None
    aliases: list[str] | None = None
    description: str | None = None
    volumes: int | None = None
    chapters: int | None = None
    language: str | None = None
    orig_language: str | None = None
    img_url: str | None = None
    publishing_status: PublishingStatus | None = None
    external_links: list[ExternalLink] | None = None
    start_date: date | None = None
    end_date: date | None = None             ## TODO: Standardize date format
    publishers: list[str] | None = None     ## TODO: Standardize date format
    authors: list[str] | None = None
    artists: list[str] | None = None
    other_staff: list[StaffRole] | None = None
    genres: list[str] | None = None
    tags: list[str] | None = None
    demographics: list[str] | None = None
    content_tags: list[str] | None = None


################################################################################
# Database Models
################################################################################
# TODO: Add created_at, updated_at timestamps to all models
# TODO: Modify models


class CollectionSeriesGroupLink(SQLModel, table=True):
    """
    Link table for the many-to-many relationship between Collection and SeriesGroup.

    Fields:
        collection_id (uuid.UUID): Foreign key to the Collection.
        seriesgroup_id (uuid.UUID): Foreign key to the SeriesGroup.
    """

    collection_id: uuid.UUID = Field(foreign_key="collection.id", primary_key=True)
    seriesgroup_id: uuid.UUID = Field(foreign_key="seriesgroup.id", primary_key=True)


class CollectionBase(SQLModel):
    """
    Base class for a user-created list of series groups.

    Fields:
        name (str): The user-defined name of the collection.
    """

    name: str = Field(index=True)


class Collection(CollectionBase, table=True):
    """
    Represents a collection of series groups created by the user.

    Relationships:
        series_groups (list["SeriesGroup"]): The groups contained in this collection.
    """

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)

    series_groups: list["SeriesGroup"] = Relationship(
        back_populates="collections", link_model=CollectionSeriesGroupLink
    )


class CollectionPublic(CollectionBase):
    """
    Represents a publicly viewable collection of series groups.
    """

    id: uuid.UUID
    series_groups: list["SeriesGroupPublic"] = []


class SeriesGroupBase(SQLModel):
    """
    Base class for the canonical identifier of an intellectual property.
    This groups all variations of a series (from different plugins) into one concept.

    Fields:
        title (str): The main title for this group.
        description (str | None): A shared description for the group.
    """

    title: str = Field(index=True)
    description: str | None = None


class SeriesGroup(SeriesGroupBase, table=True):
    """
    A single object representing a single series from all metadata sources.

    Relationships:
        collections (list[Collection]): The collections this group belongs to.
        series (list["Series"]): All individual Series objects linked to this group.
    """

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)

    collections: list["Collection"] = Relationship(
        back_populates="series_groups", link_model=CollectionSeriesGroupLink
    )
    series: list["Series"] = Relationship(back_populates="group")


class SeriesGroupPublic(SeriesGroupBase):
    """
    Public API representation of the canonical SeriesGroup.
    """

    id: uuid.UUID
    collections: list["CollectionPublic"] = []
    series: list["SeriesPublic"] = []


class SeriesBase(SQLModel):
    """
    Base class for a single series entry, sourced from one specific plugin.

    Fields:
        title (str): The title as provided by the external source.
        author (str | None): The author as provided by the external source.
        description (str | None): The description as provided by the external source.
        source_id (uuid.UUID | None): Foreign key to the MetadataPluginTable that provided this series.
        group_id (uuid.UUID | None): Foreign key to the SeriesGroup that this Series belongs to.
    """

    title: str = Field(index=True)
    romaji: str | None = Field(default=None, index=True)
    title_orig: str | None = Field(default=None, index=True)
    author: str | None = Field(default=None, index=True)
    description: str | None = None
    external_id: str | None = Field(
        default=None, index=True
    )  # ID from the external source, if available

    source_id: uuid.UUID | None = Field(
        foreign_key="metadataplugintable.id", ondelete="SET NULL"
    )  # TODO: Decide what to do on delete
    group_id: uuid.UUID | None = Field(
        foreign_key="seriesgroup.id", ondelete="SET NULL"
    )


class Series(SeriesBase, table=True):
    """
    A single series from a single metadata source.

    Relationships:
        plugin (MetadataPluginTable): The plugin that sourced this series.
        group (SeriesGroup): The canonical group this series belongs to.
        books (list["Book"]): All books belonging to this specific series.
        chapters (list["Chapter"]): All chapters belonging to this specific series.
    """

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)

    plugin: MetadataPluginTable | None = Relationship(back_populates="series")
    group: SeriesGroup | None = Relationship(back_populates="series")

    books: list["Book"] = Relationship(back_populates="series", cascade_delete=True)
    chapters: list["Chapter"] = Relationship(back_populates="series", cascade_delete=True)


class SeriesPublic(SeriesBase):
    """
    Public API representation of a single Series entry.
    """

    id: uuid.UUID
    source: MetadataPluginTable | None = None
    group: SeriesGroupPublic | None = None
    books: list["BookPublic"] = []
    chapters: list["ChapterPublic"] = []


# TODO: Make volume field decimal
class BookBase(SQLModel):
    """
    Base class for a major volume or collection within a Series.

    Fields:
        title (str): The title of the book.
        author (str | None): The author of the book.
        description (str | None): A description of the book.
        volume (int | None): The volume number (e.g., 1, 2, 3).
        series_id (uuid.UUID): Foreign key to the parent Series.
    """

    title: str = Field(index=True)
    author: str | None = Field(default=None, index=True)
    description: str | None = None
    volume: int | None = Field(default=None, index=True)

    series_id: uuid.UUID = Field(foreign_key="series.id", ondelete="CASCADE")


class Book(BookBase, table=True):
    """
    A specific book contained within a series.

    Relationships:
        series (Series): The parent series this book belongs to.
        releases (list["Release"]): All file releases associated with this book.
    """

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)

    series: "Series" = Relationship(back_populates="books")
    releases: list["Release"] = Relationship(back_populates="book", cascade_delete=True)


class BookPublic(BookBase):
    """
    Public API representation of a Book.
    """

    id: uuid.UUID
    series: "SeriesPublic"

    releases: list["ReleasePublic"] = []


# TODO: Make number and volume field decimal
class ChapterBase(SQLModel):
    """
    Base class for a single chapter or segment of content within a Series.

    Fields:
        title (str): The title of the chapter.
        author (str | None): The author of the chapter.
        number (int | None): The chapter number.
        volume (int | None): The volume number (if part of a larger volume structure).
        description (str | None): A description of the chapter content.
        series_id (uuid.UUID): Foreign key to the parent Series.
    """

    title: str = Field(index=True)
    author: str | None = Field(default=None, index=True)
    number: int | None = Field(default=None, index=True)
    volume: int | None = Field(default=None, index=True)
    description: str | None = None

    series_id: uuid.UUID = Field(foreign_key="series.id", ondelete="CASCADE")


class Chapter(ChapterBase, table=True):
    """
    A specific chapter contained within a series.

    Relationships:
        series (Series): The parent series this chapter belongs to.
        releases (list["Release"]): All file releases associated with this chapter.
    """

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)

    series: "Series" = Relationship(back_populates="chapters")
    releases: list["Release"] = Relationship(
        back_populates="chapter", cascade_delete=True
    )


class ChapterPublic(ChapterBase):
    """
    Public API representation of a Chapter.
    """

    id: uuid.UUID
    series: SeriesPublic

    releases: list["ReleasePublic"] = []


class ReleaseBase(SQLModel):
    """
    Base class for a single release related to a book or chapter.
    NOTE: A Release must be linked to EITHER a chapter_id OR a book_id, but not both.

    Fields:
        url (str): The source URL for the release file.
        format (str | None): The format (e.g., 'EPUB', 'PDF', 'Web').
        release_date (str | None): The date the release was made available (ISO 8601 string).
        chapter_id (uuid.UUID | None): Foreign key to the parent Chapter.
        book_id (uuid.UUID | None): Foreign key to the parent Book.
    """

    url: str = Field(index=True)
    format: str | None = None
    release_date: str | None = (
        None  # ISO 8601 date string # TODO: Check if date type is more appropriate
    )

    chapter_id: uuid.UUID | None = Field(
        default=None, foreign_key="chapter.id", ondelete="CASCADE"
    )
    book_id: uuid.UUID | None = Field(
        default=None, foreign_key="book.id", ondelete="SET NULL"
    )


class Release(ReleaseBase, table=True):
    """
    A specific release record stored in the database.

    Relationships:
        chapter (Chapter | None): The chapter this release is for.
        book (Book | None): The book this release is for.
    """

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)

    chapter: Chapter | None = Relationship(back_populates="releases")
    book: Book | None = Relationship(back_populates="releases")


class ReleasePublic(ReleaseBase):
    """
    Public API representation of a Release.
    """

    id: uuid.UUID
    chapter: ChapterPublic | None = None
    book: BookPublic | None = None
