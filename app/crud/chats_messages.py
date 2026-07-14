from typing import List, Optional, Tuple

from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.models import ChatMessages, Contact, Users


def create_chat_message(
    db: Session,
    chat_id: int,
    sender_id: int,
    sender_type: str,
    text: str,
) -> ChatMessages:
    message = ChatMessages(
        chat_id=chat_id,
        sender_id=sender_id,
        sender_type=sender_type,
        text=text,
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    return message


def get_messages(
    db: Session,
    chat_id: int,
    limit: int = 100,
) -> List[Tuple[ChatMessages, Optional[Contact], Optional[Users]]]:
    return (
        db.query(ChatMessages, Contact, Users)
        .outerjoin(
            Contact,
            and_(
                ChatMessages.sender_type == "contact",
                ChatMessages.sender_id == Contact.id,
            ),
        )
        .outerjoin(
            Users,
            and_(
                ChatMessages.sender_type == "user",
                ChatMessages.sender_id == Users.id,
            ),
        )
        .filter(ChatMessages.chat_id == chat_id)
        .order_by(ChatMessages.created_at.asc())
        .limit(limit)
        .all()
    )


def serialize_chat_message(
    message: ChatMessages,
    contact: Optional[Contact] = None,
    user: Optional[Users] = None,
) -> dict:
    sender = contact if message.sender_type == "contact" else user

    return {
        "id": message.id,
        "chat_id": message.chat_id,
        "sender_id": message.sender_id,
        "sender_type": message.sender_type,
        "sender_name": (
            sender.display_name
            if message.sender_type == "contact" and sender
            else sender.name if sender else None
        ),
        "text": message.text,
        "created_at": message.created_at.isoformat() if message.created_at else None,
    }
