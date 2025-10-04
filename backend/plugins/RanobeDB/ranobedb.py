# TODO: Implement the actual logic for the RanobeDB plugin.
from backend.core.database.models import SeriesSearchResponse
from backend.core.plugins.metadata import MetadataPlugin, SeriesFetchModel
from .ranobedb_api import IMAGE_BASE_URL, get_series


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
    
    def start(self) -> None:
        print("RanobeDB plugin started")

    def stop(self) -> None:
        print("RanobeDB plugin stopped")


    async def search_series(self, query: str) -> list[SeriesSearchResponse]:
        results = await get_series(query)
        series_list = results.get("series", [])
        
        # search_results = []
        # for series in series_list:
        #     external_id = series.get("id")
        #     language = series.get("lang")
        #     orig_language = series.get("olang")
            
        #     title = self._determine_title(language, series)
        #     volumes = series.get("c_num_books") or series.get("volumes", {}).get("count")
        #     img_url = (
        #         series.get("book", {})
        #         .get("image", {})
        #         .get("filename")
        #     )
        #
        #     search_results.append(SeriesSearchResponse(
        #         external_id=external_id,
        #         title=title,
        #         language=language,
        #         orig_language=orig_language,
        #         volumes=volumes,
        #         img_url=img_url
        #     ))

        # return search_results

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

    async def fetch_series(self, external_id: str) -> SeriesFetchModel:
        raise NotImplementedError("RanobeDB fetch_series not yet implemented")