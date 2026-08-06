from typing import List, Optional

from sqlalchemy.orm import Session

from app.models import Notifications


def get_unread_notifications(db: Session, user_id: int) -> List[Notifications]:
    return db.query(Notifications).filter(Notifications.user_id == user_id, Notifications.status == 1).order_by(Notifications.created_at.desc()).all()


def create_notification(
    db: Session,
    user_id: int,
    section: str,
) -> Notifications:
    notification = Notifications(
        user_id=user_id,
        section=section
    )
    db.add(notification)
    db.commit()
    db.refresh(notification)
    return notification


def read_notifications(
    db: Session,
    user_id: int,
    section: str,
) -> List[Notifications]:
    notifications = (
        db.query(Notifications)
        .filter(Notifications.user_id == user_id, Notifications.section == section)
        .order_by(Notifications.created_at.desc())
        .all()
    )
    for notification in notifications:
        if notification.status:
            notification.status = False
    db.commit()
    return notifications
