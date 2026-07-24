from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from app.models import Chats, ChatMembers, Contact
from app.utils.utils import decrypt_token


def create_chat(
    db: Session,
    name: str,
    user_id: int,
    quotation_id: int
) -> Chats:
    chat = Chats(
        name=name,
        user_id=user_id,
        quotation_id=quotation_id
    )
    db.add(chat)
    db.commit()
    db.refresh(chat)
    return chat


def update_chat(db: Session, chat_id: int, name: str) -> Optional[Chats]:
    chat = db.query(Chats).filter(Chats.id == chat_id).first()
    if chat is None:
        return None

    chat.name = name
    db.commit()
    db.refresh(chat)
    return chat


def get_chat_by_id(db: Session, chat_id: int) -> Optional[Chats]:
    return db.query(Chats).filter(Chats.id == chat_id).first()


def delete_chat(db: Session, chat_id: int) -> bool:
    chat = db.query(Chats).filter(Chats.id == chat_id).first()
    if chat is None:
        return False
    else:
        chat.status = 0;

    db.query(ChatMembers).filter(ChatMembers.chat_id == chat_id).delete(
        synchronize_session=False
    )

    chat_members = db.query(ChatMembers).filters(ChatMembers.chat_id == chat_id)
    for member in chat_members:
        member.status = 0
        db.commit()
        db.refresh(member)

    db.commit()
    db.refresh(chat)
    return True


def get_all_chats(db: Session) -> List[Chats]:
    return db.query(Chats).order_by(Chats.created_at.desc()).all()


def get_chat_with_members(db: Session, chat_id: int) -> Optional[Dict]:
    chat = db.query(Chats).filter(Chats.id == chat_id).first()
    if chat is None:
        return None

    rows = (
        db.query(ChatMembers, Contact)
        .outerjoin(Contact, ChatMembers.contact_id == Contact.id)
        .filter(ChatMembers.chat_id == chat_id)
        .order_by(ChatMembers.created_at.asc())
        .all()
    )

    members = [
        {
            "id": member.id,
            "chat_id": member.chat_id,
            "contact_id": member.contact_id,
            "token": decrypt_token(member.token),
            "access_code": member.access_code,
            "contact_name": contact.display_name if contact else None,
            "created_at": member.created_at.isoformat() if member.created_at else None,
            "contact": {
                "id": contact.id,
                "name": contact.name,
                "phone_number": contact.phone_number,
                "display_name": contact.display_name,
                "company": contact.company,
                "created_at": contact.created_at.isoformat() if contact.created_at else None,
            } if contact else None,
        }
        for member, contact in rows
    ]

    return {
        "id": chat.id,
        "name": chat.name,
        "created_at": chat.created_at.isoformat() if chat.created_at else None,
        "members": members,
    }
