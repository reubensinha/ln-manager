from fastapi import WebSocket
from sqlmodel import Session

from backend.core.database.database import engine
from backend.core.database.models import (
    NotificationMessage,
    NotificationType,
    Notification,
)


class NotificationManager:
    def __init__(self) -> None:
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        self.active_connections.remove(websocket)

    async def broadcast(self, notification: NotificationMessage) -> None:
        print(f"Broadcasting notification: {notification.message}")
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
                print(f"Error sending message to {connection}: {e}")


notification_manager = NotificationManager()
