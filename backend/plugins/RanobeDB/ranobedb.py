# TODO: Implement the actual logic for the RanobeDB plugin.
from datetime import date, datetime
from backend.core.database.models import ExternalLink, SeriesDetailsResponse, SeriesSearchResponse, StaffRole
from backend.core.plugins.metadata import MetadataPlugin, SeriesFetchModel
from .ranobedb_api import IMAGE_BASE_URL, get_series, get_series_by_id


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
            # For non-Japanese books: title > romaji > title_orig > romaji_orig > "Unknown Title"
            title = (
                response.get("title")
                or response.get("romaji")
                or response.get("title_orig")
                or response.get("romaji_orig")
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
                volumes=int(series.get("c_num_books") or series.get("volumes", {}).get("count")),
                img_url=(
                    f"{self._base_img_url}/{filename}"
                    if (filename := series.get("book", {}).get("image", {}).get("filename"))
                    else None
                ),
            )
            for series in series_list
        ]
    
    async def get_series_by_id(self, external_id: str) -> SeriesDetailsResponse | None:
        try:
            series = await get_series_by_id(int(external_id))
        except ValueError:
            raise ValueError("Invalid external_id format; must be an integer string")

        if not series:
            return None

        authors = [s.get("name") for s in series.get("staff", []) if s.get("role_type") == "author" and s.get("name")]
        artists = [s.get("name") for s in series.get("staff", []) if s.get("role_type") == "artist" and s.get("name")]
        other_staff = [
            StaffRole(name=s.get("name"), role=s.get("role"))
            for s in series.get("staff", [])
            if s.get("role_type") not in ["author", "artist"] and s.get("name") and s.get("role")
        ]
        
        genres = [t.get("name") for t in series.get("tags", []) if t.get("ttype") == "genre" and t.get("name")]
        tags = [t.get("name") for t in series.get("tags", []) if t.get("ttype") == "tag" and t.get("name")]
        demographics = [t.get("name") for t in series.get("tags", []) if t.get("ttype") == "demographic" and t.get("name")]
        content_tags = [t.get("name") for t in series.get("tags", []) if t.get("ttype") == "content" and t.get("name")]
        
        img_filename = None
        if books := series.get("books"):
            if books[0] and (image := books[0].get("image")):
                img_filename = image.get("filename")

        return SeriesDetailsResponse(
            external_id=str(series.get("id")),
            title=self._determine_title(series.get("lang") or "", series),
            romaji=series.get("romaji"),
            title_orig=series.get("title_orig"),
            aliases=series.get("aliases", "").split("\n") if series.get("aliases") else [],
            description=series.get("description"),
            volumes=len(series.get("books", [])),
            language=series.get("lang"),
            orig_language=series.get("olang"),
            img_url=f"{self._base_img_url}/{img_filename}" if img_filename else None,
            publishing_status=series.get("publication_status"),
            external_links=[
                ExternalLink(name=link.get("name"), url=link.get("url"))
                for link in series.get("urls", [])
            ],
            start_date=self._parse_date(series.get("start_date")),
            end_date=self._parse_date(series.get("end_date")),
            publishers=[p.get("name") for p in series.get("publishers", []) if p.get("name")],
            authors=authors,
            artists=artists,
            other_staff=other_staff,
            genres=genres,
            tags=tags,
            demographics=demographics,
            content_tags=content_tags,
        )

    async def fetch_series(self, external_id: str) -> SeriesFetchModel | None:
        raise NotImplementedError("RanobeDB fetch_series not yet implemented")