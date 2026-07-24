from datetime import timedelta
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from app.models import ChatMembers, Chats, Contact
from app.utils.utils import create_access_token, encrypt_token, generate_alphanumeric_code


def add_member_to_chat(
    db: Session,
    chat_id: int,
    contact_id: int,
) -> ChatMembers:
    existing_member = db.query(ChatMembers).filter(
        ChatMembers.chat_id == chat_id,
        ChatMembers.contact_id == contact_id,
    ).first()
    if existing_member is not None:
        return existing_member
    
    access_token = create_access_token({
        "sub": f"chat:{chat_id}:contact:{contact_id}",
        "chat_id": chat_id,
        "contact_id": contact_id,
        "token_use": "chat_contact",
    }, expires_delta=timedelta(days=180))

    access_code = generate_alphanumeric_code()

    member = ChatMembers(
        chat_id=chat_id,
        contact_id=contact_id,
        token=encrypt_token(access_token) if access_token else None,
        access_code=access_code,
    )
    db.add(member)
    db.commit()
    db.refresh(member)
    return member


def get_chat_member(
    db: Session,
    chat_id: int,
    contact_id: int,
) -> Optional[ChatMembers]:
    return db.query(ChatMembers).filter(
        ChatMembers.chat_id == chat_id,
        ChatMembers.contact_id == contact_id,
    ).first()


def get_chat_member_by_code(db: Session, access_code: str) -> Optional[ChatMembers]:
    result = (
        db.query(ChatMembers, Chats.quotation_id)
        .join(Chats, ChatMembers.chat_id == Chats.id)
        .filter(ChatMembers.access_code == access_code)
        .first()
    )
    if result is None:
        return None

    chat_member, quotation_id = result
    chat_member.quotation_id = quotation_id
    return chat_member


def get_members_availables_of_chat(db: Session, chat_id: int) -> List[Dict]:
    chat_contact_ids = (
        db.query(ChatMembers.contact_id)
        .filter(
            ChatMembers.chat_id == chat_id,
            ChatMembers.contact_id.isnot(None),
        )
    )

    contacts = (
        db.query(Contact)
        .filter(~Contact.id.in_(chat_contact_ids))
        .order_by(Contact.created_at.desc())
        .all()
    )

    return [
        {
            "id": contact.id,
            "name": contact.name,
            "phone_number": contact.phone_number,
            "display_name": contact.display_name,
            "company": contact.company,
            "created_at": contact.created_at.isoformat() if contact.created_at else None,
        }
        for contact in contacts
    ]


def update_token_member_chat(
    db: Session,
    chat_id: int,
    contact_id: int,
    token: str,
) -> Optional[ChatMembers]:
    existing_member = db.query(ChatMembers).filter(
        ChatMembers.chat_id == chat_id,
        ChatMembers.contact_id == contact_id,
    ).first()
    if existing_member is None:
        return None

    existing_member.token = encrypt_token(token)
    db.commit()
    db.refresh(existing_member)
    return existing_member



def remove_member_from_chat(db: Session, chat_id: int, contact_id: int) -> bool:
    member = db.query(ChatMembers).filter(
        ChatMembers.chat_id == chat_id,
        ChatMembers.contact_id == contact_id,
    ).first()
    if member is None:
        return False

    db.delete(member)
    db.commit()
    return True
