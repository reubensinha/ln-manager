from typing import Any
from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session, select
from uuid import UUID

from backend.core.database.models import DownloadClient
from backend.core.database.database import get_session
from backend.core.services.download_client_service import download_release

router = APIRouter()


@router.post("/download", response_model=dict[str, Any])
async def download_torrent(
    *, 
    session: Session = Depends(get_session),
    download_url: str | None = None,
    magnet: str | None = None,
    download_client_id: str | None = None
):
    """Download a release using the default or specified download client.
    
    Args:
        download_url: HTTP/HTTPS URL to download (e.g., .torrent file)
        magnet: Magnet link
        download_client_id: Optional UUID of specific download client to use
    
    Returns:
        Dictionary with success status, message, and download_client_id
    """
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info(f"Download request received: download_url={download_url}, magnet={magnet[:50] if magnet else None}..., client_id={download_client_id}")
    
    if not download_url and not magnet:
        raise HTTPException(status_code=400, detail="Either download_url or magnet must be provided")
    
    try:
        result = await download_release(
            session=session,
            download_url=download_url,
            magnet=magnet,
            download_client_id=download_client_id
        )
        logger.info(f"Download request successful: {result}")
        return result
    except ValueError as e:
        logger.error(f"ValueError in download: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Exception in download: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to download: {str(e)}")
