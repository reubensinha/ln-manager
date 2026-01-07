import logging
from fastapi import WebSocket
from sqlmodel import Session

from backend.core.database.database import engine
from backend.core.database.models import (
    NotificationMessage,
    NotificationType,
    Notification,
)
from backend.core.logging_config import get_logger


logger = get_logger(__name__)


class NotificationManager:
    def __init__(self) -> None:
        self.active_connections: list[WebSocket] = []
        logger.debug("NotificationManager initialized")

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket) -> None:
        self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")

    async def broadcast(self, notification: NotificationMessage) -> None:
        logger.info(f"Broadcasting notification [{notification.type}]: {notification.message}")
        
        with Session(engine) as session:
            notif = Notification(
                message=notification.message,
                type=notification.type,
            )
            session.add(notif)
            session.commit()
            session.refresh(notif)

        for connection in self.active_connections:
            try:
                await connection.send_json(
                    {"event": "notification", "payload": notification.model_dump_json()}
                )
            except Exception as e:
                logger.error(f"Error sending notification to WebSocket: {e}", exc_info=True)


notification_manager = NotificationManager()
