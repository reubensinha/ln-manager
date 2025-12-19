from sqlmodel import Session, select
from backend.core.database.database import engine
from backend.core.database.models import DownloadClient
from backend.plugin_manager import plugin_manager
from backend.core.plugins.download_client import DownloadClientPlugin
# TODO: Use session dependency injection where possible

def get_torrent_status(download_client_id: str | None = None):
    """Get torrent percent complete and status from download client(s).
    
    Args:
        download_client_id: Optional UUID of specific DownloadClient, otherwise uses first enabled
    """
    # TODO: Implement torrent status retrieval
    ...

def send_to_download_client(item: dict, download_client_id: str | None = None):
    """Send item to download client(s).
    
    Args:
        item: Item to send to download client
        download_client_id: Optional UUID of specific DownloadClient, otherwise uses first enabled
    """
    with Session(engine) as session:
        if download_client_id:
            # Send to specific download client
            download_client = session.get(DownloadClient, download_client_id)
            if not download_client or not download_client.enabled:
                return False
            clients = [download_client]
        else:
            # Send to first enabled download client
            clients = session.exec(
                select(DownloadClient).where(DownloadClient.enabled == True)
            ).all()
            if not clients:
                return False
            ## TODO: Send to default constant. Not First one.
            clients = [clients[0]]  # Use first one
        
        for client in clients:
            if not client.plugin:
                continue
            
            # Get the plugin instance
            plugin = plugin_manager.get_plugin(client.plugin.name)
            if not plugin:
                continue
            
            client_instance = None
            try:
                # Use plugin's factory method to create configured download client
                client_instance = plugin.create_download_client(client.config or {})
                if not isinstance(client_instance, DownloadClientPlugin):
                    continue
                
                # Send to download client
                result = client_instance.download(item)
                if result:
                    return True
            except Exception as e:
                print(f"Error sending to download client {client.name}: {e}")
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
