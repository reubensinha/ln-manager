from sqlmodel import Session, select
from backend.core.database.database import engine
from backend.core.database.models import DownloadClient
from backend.plugin_manager import plugin_manager
from backend.core.plugins.download_client import DownloadClientPlugin
from typing import Any
from uuid import UUID
# TODO: Use session dependency injection where possible

def get_torrent_status(download_client_id: str | None = None):
    """Get torrent percent complete and status from download client(s).
    
    Args:
        download_client_id: Optional UUID of specific DownloadClient, otherwise uses first enabled
    """
    # TODO: Implement torrent status retrieval
    ...

async def download_release(
    session: Session,
    download_url: str | None = None,
    magnet: str | None = None,
    download_client_id: str | UUID | None = None
) -> dict[str, Any]:
    """Download a release using the default or specified download client.
    
    Args:
        session: Database session
        download_url: HTTP/HTTPS URL to download (e.g., .torrent file)
        magnet: Magnet link
        download_client_id: Optional UUID of specific download client to use
    
    Returns:
        Dictionary with success status, message, and download_client_id
    
    Raises:
        ValueError: If no download URL or magnet is provided, or if no enabled client is found
    """
    from backend.core.logging_config import get_logger
    logger = get_logger(__name__)
    
    logger.info(f"download_release called: url={download_url}, magnet={magnet[:50] if magnet else None}..., client_id={download_client_id}")
    
    if not download_url and not magnet:
        raise ValueError("Either download_url or magnet must be provided")
    
    # Get the default client if no specific client was requested
    if not download_client_id:
        default_client = session.exec(
            select(DownloadClient)
            .where(DownloadClient.enabled == True)
            .where(DownloadClient.is_default == True)
        ).first()
        
        if default_client:
            download_client_id = default_client.id  # Keep as UUID
            logger.info(f"Using default download client: {default_client.name} ({download_client_id})")
        else:
            logger.warning("No default download client found")
    
    # Send to download client - pass only the URL or magnet that was provided
    logger.info(f"Calling send_to_download_client...")
    success = await send_to_download_client(
        torrent_url=download_url,
        magnet_link=magnet,
        download_client_id=download_client_id
    )
    
    logger.info(f"send_to_download_client returned: {success}")
    
    if not success:
        raise ValueError("Failed to send download to client. Make sure a download client is enabled.")
    
    return {
        "success": True,
        "message": "Download sent to client successfully",
        "download_client_id": str(download_client_id)  # Convert to string only for response
    }

async def send_to_download_client(
    torrent_url: str | None = None,
    magnet_link: str | None = None,
    download_client_id: str | UUID | None = None
) -> bool:
    """Send item to download client(s).
    
    Args:
        torrent_url: HTTP/HTTPS URL to a .torrent file
        magnet_link: Magnet link
        download_client_id: Optional UUID of specific DownloadClient, otherwise uses default
    
    Returns:
        True if download was successfully sent, False otherwise
    """
    from backend.core.logging_config import get_logger
    logger = get_logger(__name__)
    
    with Session(engine) as session:
        if download_client_id:
            # Send to specific download client
            download_client = session.get(DownloadClient, download_client_id)
            if not download_client or not download_client.enabled:
                logger.error(f"Download client not found or not enabled: {download_client_id}")
                return False
            clients = [download_client]
        else:
            # Get the default download client
            default_client = session.exec(
                select(DownloadClient)
                .where(DownloadClient.enabled == True)
                .where(DownloadClient.is_default == True)
            ).first()
            
            if default_client:
                clients = [default_client]
            else:
                # Fall back to first enabled client
                clients = session.exec(
                    select(DownloadClient).where(DownloadClient.enabled == True)
                ).all()
                if not clients:
                    logger.error("No enabled download clients found")
                    return False
                clients = [clients[0]]
        
        for client in clients:
            if not client.plugin:
                logger.warning(f"Client {client.name} has no plugin configured")
                continue
            
            # Get the plugin instance
            plugin = plugin_manager.get_plugin(client.plugin.name)
            if not plugin:
                logger.error(f"Plugin not found: {client.plugin.name}")
                continue
            
            client_instance = None
            try:
                # Use plugin's factory method to create configured download client
                logger.info(f"Creating download client instance for {client.name}")
                client_instance = plugin.create_download_client(client.config or {})
                if not isinstance(client_instance, DownloadClientPlugin):
                    logger.error(f"Client instance is not a DownloadClientPlugin")
                    continue
                
                # Send to download client with the appropriate parameter
                logger.info(f"Sending download to {client.name}: torrent_url={torrent_url}, magnet_link={magnet_link[:50] if magnet_link else None}...")
                result = await client_instance.download(
                    torrent_file=torrent_url,
                    magnet_link=magnet_link
                )
                logger.info(f"Download result: {result}")
                if result:
                    return True
            except Exception as e:
                logger.error(f"Error sending to download client {client.name}: {e}", exc_info=True)
            finally:
                # Clean up if client has cleanup method
                if client_instance and hasattr(client_instance, 'stop'):
                    client_instance.stop()
    
    return False
    
def get_metadata(torrent_hash: str, download_client_id: str | None = None):
    """Get metadata from torrent hash.
    
    Args:
        torrent_hash: Hash of the torrent
        download_client_id: Optional UUID of specific DownloadClient
    """
    # TODO: Implement metadata retrieval from torrent
    ...
