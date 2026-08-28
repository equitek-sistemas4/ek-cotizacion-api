from typing import Dict, List, Optional

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models import Chats, ChatMembers, Contact
from app.utils.utils import decrypt_token


def create_chat(
    db: Session,
    name: str,
    description: Optional[str],
    user_id: int,
    quotation_id: int
) -> Chats:
    chat = Chats(
        name=name,
        description=description,
        user_id=user_id,
        quotation_id=quotation_id
    )
    db.add(chat)
    db.commit()
    db.refresh(chat)
    return chat


def update_chat(db: Session, chat_id: int, name: str, description: Optional[str] = None) -> Optional[Chats]:
    chat = db.query(Chats).filter(Chats.id == chat_id).first()
    if chat is None:
        return None

    chat.name = name
    chat.description = description
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

    db.query(ChatMembers).filter(ChatMembers.chat_id == chat_id).update(
        {ChatMembers.status: 0},
        synchronize_session=False,
    )

    db.commit()
    db.refresh(chat)
    return True


def get_all_chats(db: Session, user_id: Optional[int] = None, search: Optional[str] = None) -> List[Chats]:
    query = db.query(Chats).filter(Chats.status == 1, Chats.user_id == user_id)

    if search and search.strip():
        search_term = f"%{search.strip()}%"
        query = query.filter(
            or_(
                Chats.name.ilike(search_term),
                Chats.description.ilike(search_term),
            )
        )

    return query.order_by(Chats.created_at.desc()).all()


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
                "position": contact.position,
                "idempresa_contacto": contact.idempresa_contacto,
                "fk_idempresa": contact.fk_idempresa,
                "created_at": contact.created_at.isoformat() if contact.created_at else None,
            } if contact else None,
        }
        for member, contact in rows
    ]

    return {
        "id": chat.id,
        "name": chat.name,
        "description": chat.description,
        "quotation_id": chat.quotation_id,
        "created_at": chat.created_at.isoformat() if chat.created_at else None,
        "members": members,
    }
