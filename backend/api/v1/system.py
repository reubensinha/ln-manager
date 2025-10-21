import asyncio

from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session, select
from uuid import UUID

from backend.core.database.models import Notification
from backend.core.database.database import get_session

router = APIRouter()

@router.get("/system/notifications", response_model=list[Notification])
async def read_notifications(*, session: Session = Depends(get_session)):
    notifications = session.exec(select(Notification)).all()
    return notifications
