from fastapi import APIRouter, Depends, Form, Path
from sqlalchemy.orm import Session

from app.crud.notifications import (
    create_notification,
    get_unread_notifications,
    read_notifications,
)
from app.database import get_db


router = APIRouter(prefix="/notifications", tags=["notifications"])


def serialize_notification(notification) -> dict:
    return {
        "id": notification.id,
        "user_id": notification.user_id,
        "section": notification.section,
        "status": notification.status,
        "created_at": (
            notification.created_at.isoformat()
            if notification.created_at
            else None
        ),
    }


@router.post("/create")
async def create_notification_route(
    user_id: int = Form(..., ge=1),
    section: str = Form(..., min_length=1),
    db: Session = Depends(get_db),
):
    notification = create_notification(
        db,
        user_id=user_id,
        section=section,
    )

    return {
        "success": True,
        "message": "Notificacion creada",
        "data": serialize_notification(notification),
    }


@router.get("/unread/{user_id}")
async def get_unread_notifications_route(
    user_id: int = Path(..., ge=1),
    db: Session = Depends(get_db),
):
    notifications = get_unread_notifications(db, user_id=user_id)

    return {
        "success": True,
        "data": [
            serialize_notification(notification)
            for notification in notifications
        ],
    }


@router.post("/read")
async def read_notifications_route(
    user_id: int = Form(..., ge=1),
    section: str = Form(..., min_length=1),
    db: Session = Depends(get_db),
):
    notifications = read_notifications(
        db,
        user_id=user_id,
        section=section,
    )

    return {
        "success": True,
        "data": [
            serialize_notification(notification)
            for notification in notifications
        ],
    }
