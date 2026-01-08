"""API endpoints for indexer search and feed operations."""

from typing import Dict, List, Any
from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session

from backend.core.database.database import get_session
from backend.core.services import indexer_service


router = APIRouter(prefix="/indexers", tags=["indexers"])


@router.get("/search")
async def search_all_indexers(
    query: str,
    session: Session = Depends(get_session)
) -> List[Dict[str, Any]]:
    """Search across all enabled indexers.
    
    Args:
        query: Search query string
        session: Database session
        
    Returns:
        Aggregated search results from all enabled indexers
    """
    results = await indexer_service.search_all_indexers(query, session)
    return results or []


@router.get("/search/{indexer_id}")
async def search_specific_indexer(
    indexer_id: str,
    query: str,
    session: Session = Depends(get_session)
) -> List[Dict[str, Any]]:
    """Search a specific indexer by ID.
    
    Args:
        indexer_id: UUID of the indexer
        query: Search query string
        session: Database session
        
    Returns:
        Search results from the specified indexer
    """
    results = await indexer_service.search_indexer(indexer_id, query, session)
    
    if results is None:
        raise HTTPException(status_code=404, detail="Indexer not found or disabled")
    
    return results


@router.get("/feed")
async def get_all_indexers_feed(
    session: Session = Depends(get_session)
) -> List[Dict[str, Any]]:
    """Get RSS/feed from all enabled indexers.
    
    Args:
        session: Database session
        
    Returns:
        Aggregated feed items from all enabled indexers
    """
    results = await indexer_service.get_all_feeds(session)
    return results or []


@router.get("/feed/{indexer_id}")
async def get_indexer_feed_by_id(
    indexer_id: str,
    session: Session = Depends(get_session)
) -> List[Dict[str, Any]]:
    """Get RSS/feed from a specific indexer by ID.
    
    Args:
        indexer_id: UUID of the indexer
        session: Database session
        
    Returns:
        Feed items from the specified indexer
    """
    results = await indexer_service.get_feed(indexer_id, session)
    
    if results is None:
        raise HTTPException(status_code=404, detail="Indexer not found or disabled")
    
    return results


@router.post("/automatic-search")
async def automatic_search(
    book_id: str | None = None,
    series_id: str | None = None,
    session: Session = Depends(get_session)
) -> Dict[str, Any]:
    """Perform automatic search and download for a book or series.
    
    This endpoint will:
    - For books: Search for the specific book/volume and auto-download best match
    - For series: Search for all missing/undownloaded books in the series
    - Apply quality profiles and filters
    - Automatically download the best matching releases if criteria are met
    
    Args:
        book_id: UUID of a specific book to search for
        series_id: UUID of a series (searches all books in series)
        session: Database session
        
    Returns:
        Dictionary with search results and download status
        
    Raises:
        HTTPException: If neither or both book_id and series_id are provided
    """
    if not book_id and not series_id:
        raise HTTPException(
            status_code=400, 
            detail="Either book_id or series_id must be provided"
        )
    
    if book_id and series_id:
        raise HTTPException(
            status_code=400, 
            detail="Cannot specify both book_id and series_id"
        )
    
    # TODO: Implement automatic search logic
    # For book_id:
    # - Get book details from database
    # - Build search query from book metadata (title, volume, series, etc.)
    # - Search all enabled indexers
    # - Score and filter results based on quality profiles
    # - Automatically trigger download for best match
    # - Return download status and matched result
    #
    # For series_id:
    # - Get series details and all books from database
    # - Filter to only undownloaded/missing books
    # - For each book, perform search across all enabled indexers
    # - Score and filter results based on quality profiles
    # - Automatically trigger downloads for best matches
    # - Return summary of downloads initiated (count, which books, etc.)
    raise HTTPException(status_code=501, detail="Automatic search not yet implemented")


@router.post("/smart-search")
async def smart_search(
    query: str,
    book_id: str | None = None,
    series_id: str | None = None,
    session: Session = Depends(get_session)
) -> List[Dict[str, Any]]:
    """Perform smart search with enhanced scoring and filtering.
    
    Smart search will:
    - Parse the query to extract metadata (title, volume, language, etc.)
    - Search across all enabled indexers
    - Apply intelligent scoring based on:
      * Title similarity
      * Metadata matching (volume number, language, format)
      * Seeders/peers ratio
      * File size reasonableness
      * Release group reputation
    - Filter out low-quality or mismatched results
    - Return scored and ranked results
    
    Args:
        query: Search query string (can be book title, series name, etc.)
        book_id: Optional UUID of the book for enhanced matching
        series_id: Optional UUID of the series for enhanced matching
        session: Database session
        
    Returns:
        Scored and filtered search results from all enabled indexers
    """
    # TODO: Implement smart search logic
    # - If book_id or series_id provided, get metadata from database
    # - Parse query to extract metadata
    # - Search all enabled indexers
    # - Apply scoring algorithm to results
    # - Filter and rank results
    # - Return enhanced results with scores and rejection reasons
    raise HTTPException(status_code=501, detail="Smart search not yet implemented")
