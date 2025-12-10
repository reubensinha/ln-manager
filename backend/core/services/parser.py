def _match_result_title_to_series(result_title: str) -> str | None:
    """Attempt to match a result title to an existing series in the database.

    Args:
        result_title (str): The title from the search result.
    Returns:
        str | None: The matched series group name, or None if no match found.
    """
    # TODO:
    ...

def _match_result_title_to_book(result_title: str, series_group: str) -> str | None:
    """Attempt to match a result title to an existing book in the database.

    Args:
        result_title (str): The title from the search result.
        series_group (str): The series group name to filter books by.
    Returns:
        str | None: The matched book title, or None if no match found.
    """
    # TODO:
    ...
    
def parse_titles(result_titles: list[str]) -> dict:
    """Parse a result title into its components (series, book, volume, etc).

    Args:
        result_titles (list[str]): The titles from the search results.
    Returns:
        dict: Parsed components of the titles.
    """
    # TODO:
    ...
