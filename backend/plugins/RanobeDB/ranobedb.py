# TODO: Implement the actual logic for the RanobeDB plugin.
from datetime import date, datetime
from uuid import UUID, uuid4
from backend.core.database.models import (
    ReleaseBase,
    SeriesBase,
    BookBase,
    SeriesDetailsResponse,
    SeriesSearchResponse,
)
from backend.core.plugins.metadata import (
    BookFetchModel,
    MetadataPlugin,
    SeriesFetchModel,
)
from .ranobedb_api import IMAGE_BASE_URL, get_series, get_series_by_id, get_book_by_id


class RanobeDBPlugin(MetadataPlugin):
    """RanobeDB metadata plugin implementation."""

    name = "RanobeDB"
    version = "1.0.0"
    description = "Metadata plugin for RanobeDB"
    enabled = True
    _base_img_url = IMAGE_BASE_URL

    @staticmethod
    def _determine_title(lang: str, response: dict) -> str:
        """
        Determine the appropriate title based on language preference.
        """
        if lang == "ja":
            # For Japanese books: romaji > romaji_orig > title > title_orig > "Unknown Title"
            title = (
                response.get("romaji")
                or response.get("romaji_orig")
                or response.get("title")
                or response.get("title_orig")
                or "Unknown Title"
            )
        else:
            # For non-Japanese books: romaji > romaji_orig > title > title_orig > "Unknown Title"
            title = (
                response.get("romaji")
                or response.get("romaji_orig")
                or response.get("title")
                or response.get("title_orig")
                or "Unknown Title"
            )

        return title

    @staticmethod
    def _parse_date(date_int: int | None) -> date | None:
        """
        Parse a date integer from the API into a date object.
        Handles YYYYMMDD format.
        """
        if not date_int:
            return None
        try:
            return datetime.strptime(str(date_int), "%Y%m%d").date()
        except (ValueError, TypeError):
            return None

    def start(self) -> None:
        print("RanobeDB plugin started")

    def stop(self) -> None:
        print("RanobeDB plugin stopped")

    async def search_series(self, query: str) -> list[SeriesSearchResponse]:
        results = await get_series(query)
        series_list = results.get("series", [])

        return [
            SeriesSearchResponse(
                external_id=str(series.get("id")),
                title=self._determine_title(series.get("lang"), series),
                language=series.get("lang"),
                orig_language=series.get("olang"),
                volumes=int(
                    series.get("c_num_books") or series.get("volumes", {}).get("count")
                ),
                img_url=(
                    f"{self._base_img_url}/{filename}"
                    if (
                        filename := series.get("book", {})
                        .get("image", {})
                        .get("filename")
                    )
                    else None
                ),
                nsfw_img=series.get("book", {}).get("image", {}).get("nsfw", False),
            )
            for series in series_list
        ]

    async def get_series_by_id(self, external_id: str) -> SeriesDetailsResponse | None:
        try:
            response = await get_series_by_id(int(external_id))
        except ValueError:
            raise ValueError("Invalid external_id format; must be an integer string")

        if not response:
            return None

        series = response.get("series")

        if not series:
            return None

        authors = [
            s.get("name")
            for s in series.get("staff", [])
            if s.get("role_type") == "author" and s.get("name")
        ]
        artists = [
            s.get("name")
            for s in series.get("staff", [])
            if s.get("role_type") == "artist" and s.get("name")
        ]
        other_staff = [
            {"name": s.get("name"), "role": s.get("role")}
            for s in series.get("staff", [])
            if s.get("role_type") not in ["author", "artist"]
            and s.get("name")
            and s.get("role")
        ]

        genres = [
            t.get("name")
            for t in series.get("tags", [])
            if t.get("ttype") == "genre" and t.get("name")
        ]
        tags = [
            t.get("name")
            for t in series.get("tags", [])
            if t.get("ttype") == "tag" and t.get("name")
        ]
        demographics = [
            t.get("name")
            for t in series.get("tags", [])
            if t.get("ttype") == "demographic" and t.get("name")
        ]
        content_tags = [
            t.get("name")
            for t in series.get("tags", [])
            if t.get("ttype") == "content" and t.get("name")
        ]

        img_filename = None
        nsfw_img = False
        if books := series.get("books"):
            if books[0] and (image := books[0].get("image")):
                img_filename = image.get("filename")
                nsfw_img = image.get("nsfw", False)

        potential_links = []
        if url := series.get("web_novel"):
            potential_links.append({"name": "Web Novel", "url": url})
        if website := series.get("website"):
            potential_links.append({"name": "Official Website", "url": website})
        if wid := series.get("wikidata_id"):
            potential_links.append(
                {"name": "Wikidata", "url": f"https://www.wikidata.org/wiki/Q{wid}"}
            )
        if aid := series.get("anidb_id"):
            potential_links.append(
                {"name": "AniDB", "url": f"https://anidb.net/anime/{aid}"}
            )
        if bid := series.get("bookwalker_id"):
            potential_links.append(
                {"name": "BookWalker", "url": f"https://bookwalker.jp/series/{bid}"}
            )
        if anilist_id := series.get("anilist_id"):
            potential_links.append(
                {"name": "AniList", "url": f"https://anilist.co/manga/{anilist_id}"}
            )
        if mal_id := series.get("mal_id"):
            potential_links.append(
                {
                    "name": "MyAnimeList",
                    "url": f"https://myanimelist.net/manga/{mal_id}",
                }
            )

        return SeriesDetailsResponse(
            external_id=str(series.get("id")),
            title=self._determine_title(series.get("lang") or "", series),
            romaji=series.get("romaji") or series.get("romaji_orig"),
            title_orig=series.get("title_orig"),
            aliases=(
                series.get("aliases", "").split("\n") if series.get("aliases") else []
            ),
            description=series.get("description")
            or series.get("book_description", {}).get("description")
            or series.get("book_description", {}).get("description_ja"),
            volumes=len(series.get("books", [])),
            language=series.get("lang"),
            orig_language=series.get("olang"),
            img_url=f"{self._base_img_url}/{img_filename}" if img_filename else None,
            publishing_status=series.get("publication_status"),
            external_links=potential_links,
            start_date=self._parse_date(series.get("start_date")),
            end_date=self._parse_date(series.get("end_date")),
            publishers=[
                p.get("name") for p in series.get("publishers", []) if p.get("name")
            ],
            authors=authors,
            artists=artists,
            other_staff=other_staff,
            genres=genres,
            tags=tags,
            demographics=demographics,
            content_tags=content_tags,
            source_url=f"https://ranobedb.org/series/{external_id}",
            nsfw_img=nsfw_img,
        )

    async def fetch_series(self, external_id: str) -> SeriesFetchModel | None:

        ## Get Series Details
        response = await get_series_by_id(int(external_id))

        if not response:
            return None

        series_details = response.get("series")
        if not series_details:
            return None

        ## TODO: Save image locally and set img_url accordingly
        authors = [
            s.get("name")
            for s in series_details.get("staff", [])
            if s.get("role_type") == "author" and s.get("name")
        ]
        artists = [
            s.get("name")
            for s in series_details.get("staff", [])
            if s.get("role_type") == "artist" and s.get("name")
        ]
        other_staff = [
            {"name": s.get("name"), "role": s.get("role")}
            for s in series_details.get("staff", [])
            if s.get("role_type") not in ["author", "artist"]
            and s.get("name")
            and s.get("role")
        ]

        genres = [
            t.get("name")
            for t in series_details.get("tags", [])
            if t.get("ttype") == "genre" and t.get("name")
        ]
        tags = [
            t.get("name")
            for t in series_details.get("tags", [])
            if t.get("ttype") == "tag" and t.get("name")
        ]
        demographics = [
            t.get("name")
            for t in series_details.get("tags", [])
            if t.get("ttype") == "demographic" and t.get("name")
        ]
        content_tags = [
            t.get("name")
            for t in series_details.get("tags", [])
            if t.get("ttype") == "content" and t.get("name")
        ]

        img_filename = None
        nsfw_img = False
        if books := series_details.get("books"):
            if books[0] and (image := books[0].get("image")):
                img_filename = image.get("filename")
                nsfw_img = image.get("nsfw", False)

        potential_links = []
        if url := series_details.get("web_novel"):
            potential_links.append({"name": "Web Novel", "url": url})
        if website := series_details.get("website"):
            potential_links.append({"name": "Official Website", "url": website})
        if wid := series_details.get("wikidata_id"):
            potential_links.append(
                {"name": "Wikidata", "url": f"https://www.wikidata.org/wiki/Q{wid}"}
            )
        if aid := series_details.get("anidb_id"):
            potential_links.append(
                {"name": "AniDB", "url": f"https://anidb.net/anime/{aid}"}
            )
        if bid := series_details.get("bookwalker_id"):
            potential_links.append(
                {"name": "BookWalker", "url": f"https://bookwalker.jp/series/{bid}"}
            )
        if anilist_id := series_details.get("anilist_id"):
            potential_links.append(
                {"name": "AniList", "url": f"https://anilist.co/manga/{anilist_id}"}
            )
        if mal_id := series_details.get("mal_id"):
            potential_links.append(
                {
                    "name": "MyAnimeList",
                    "url": f"https://myanimelist.net/manga/{mal_id}",
                }
            )

        series = SeriesBase(
            external_id=str(series_details.get("id")),
            title=self._determine_title(
                series_details.get("lang") or "", series_details
            ),
            romaji=series_details.get("romaji") or series_details.get("romaji_orig"),
            title_orig=series_details.get("title_orig"),
            aliases=(
                series_details.get("aliases", "").split("\n")
                if series_details.get("aliases")
                else []
            ),
            description=series_details.get("description")
            or series_details.get("book_description", {}).get("description")
            or series_details.get("book_description", {}).get("description_ja"),
            language=series_details.get("lang"),
            orig_language=series_details.get("olang"),
            publishing_status=series_details.get("publication_status"),
            external_links=potential_links,
            start_date=self._parse_date(series_details.get("start_date")),
            end_date=self._parse_date(series_details.get("end_date")),
            publishers=[
                p.get("name")
                for p in series_details.get("publishers", [])
                if p.get("name")
            ],
            authors=authors,
            artists=artists,
            other_staff=other_staff,
            genres=genres,
            tags=tags,
            demographics=demographics,
            content_tags=content_tags,
            img_url=f"{self._base_img_url}/{img_filename}" if img_filename else None,
            source_url=f"https://ranobedb.org/series/{external_id}",
            nsfw_img=nsfw_img,
            source_id=None,  # Will be set by the caller
            group_id=None,  # Will be set by the caller
        )

        ## Get Book Details
        books_from_series = series_details.get("books", [])

        books = []
        for book_in_series in books_from_series:
            book_id = book_in_series.get("id")
            if not book_id:
                continue

            book_response = await get_book_by_id(book_id)

            if not book_response:
                continue

            book_detail = book_response.get("book")

            if not book_detail:
                continue

            editions = book_detail.get("editions")
            staff_list = (
                editions[0].get("staff", [])
                if editions and len(editions) > 0 and editions[0]
                else []
            )
            authors = [
                s.get("name")
                for s in staff_list
                if s.get("role_type") == "author" and s.get("name")
            ]
            artists = [
                s.get("name")
                for s in staff_list
                if s.get("role_type") == "artist" and s.get("name")
            ]
            other_staff = [
                {"name": s.get("name"), "role": s.get("role")}
                for s in staff_list
                if s.get("role_type") not in ["author", "artist"]
                and s.get("name")
                and s.get("role")
            ]

            img_filename = book_detail.get("image", {}).get("filename")
            nsfw_img = (
                book_detail.get("image", {}).get("nsfw", False)
                if book_detail.get("image")
                else False
            )

            # Assemble Data into BookFetchModel
            book_base = BookBase(
                external_id=str(book_detail.get("id")),
                title=self._determine_title(
                    series_details.get("lang") or "", book_detail
                ),
                romaji=book_detail.get("romaji") or book_detail.get("romaji_orig"),
                title_orig=book_detail.get("title_orig"),
                description=book_detail.get("description")
                or series_details.get("description_ja"),
                img_url=(
                    f"{self._base_img_url}/{img_filename}" if img_filename else None
                ),
                authors=authors,
                artists=artists,
                other_staff=other_staff,
                language=book_detail.get("lang"),
                orig_language=book_detail.get("olang"),
                release_date=self._parse_date(book_detail.get("c_release_date")),
                sort_order=book_in_series.get("sort_order"),
                source_url=f"https://ranobedb.org/book/{book_detail.get('id')}",
                nsfw_img=nsfw_img,
                series_id=uuid4(),  # Will be ignored and set by the caller
            )

            release_details = []
            for release in book_detail.get("releases", []):

                links = [
                    ("Official Website", release.get("website")),
                    ("Amazon", release.get("amazon")),
                    ("BookWalker", release.get("bookwalker")),
                    ("Rakuten", release.get("rakuten")),
                ]

                release_obj = ReleaseBase(
                    external_id=str(release.get("id")),
                    title=release.get("title"),
                    romaji=release.get("romaji"),
                    description=release.get("description"),
                    format=release.get("format"),
                    language=release.get("lang"),
                    release_date=self._parse_date(release.get("release_date")),
                    isbn=release.get("isbn13"),
                    links=[{"name": name, "url": url} for name, url in links if url],
                    source_url=f"https://ranobedb.org/release/{release.get('id')}",
                    book_id=uuid4(),  # Will be ignored and set by the caller
                )
                release_details.append(release_obj)

            book = BookFetchModel(book=book_base, releases=release_details)

            books.append(book)
            # Assemble Data into ReleaseBase

        chapters = []  # RanobeDB does not have chapters

        ## Assemble Data into SeriesFetchModel
        series_fetch = SeriesFetchModel(series=series, books=books, chapters=chapters)
        return series_fetch
