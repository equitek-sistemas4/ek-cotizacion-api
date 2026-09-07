from typing import List, Optional

from sqlalchemy.orm import Session

from app.models import Notifications


def get_unread_notifications(db: Session, user_id: int) -> List[Notifications]:
    return db.query(Notifications).filter(Notifications.user_id == user_id, Notifications.status == 1).order_by(Notifications.created_at.desc()).all()


def create_notification(
    db: Session,
    user_id: int,
    section: str,
    chat_id: Optional[int] = None,
) -> Notifications:
    notification = Notifications(
        user_id=user_id,
        section=section,
        chat_id=chat_id
    )
    db.add(notification)
    db.commit()
    db.refresh(notification)
    return notification


def read_notifications(
    db: Session,
    user_id: int,
    section: str,
    chat_id: Optional[int] = None,
) -> List[Notifications]:
    query = db.query(Notifications).filter(
        Notifications.user_id == user_id,
        Notifications.section == section,
    )
    if chat_id is not None:
        query = query.filter(Notifications.chat_id == chat_id)

    notifications = query.order_by(Notifications.created_at.desc()).all()
    for notification in notifications:
        if notification.status:
            notification.status = False
    db.commit()
    return notifications
