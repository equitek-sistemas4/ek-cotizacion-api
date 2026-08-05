from datetime import timedelta
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from app.models import ChatMembers, Chats, Contact, Contact_requests
from app.utils.utils import create_access_token, encrypt_token, generate_alphanumeric_code


def clean_contact_phone_number(phone_number: str) -> str:
    return phone_number.replace("+", "").strip()


def create_contact(
    db: Session,
    name: str,
    phone_number: str,
    display_name: Optional[str] = None,
    company: Optional[str] = None,
    position: Optional[str] = None,
) -> Contact:
    contact = Contact(
        name=name,
        phone_number=clean_contact_phone_number(phone_number),
        display_name=display_name,
        company=company,
        position=position
    )
    db.add(contact)
    db.commit()
    db.refresh(contact)
    return contact


def create_contact_request(
    db: Session,
    chat_id: int,
    contact_name: str,
    contact_phone_number: str,
    contact_display_name: Optional[str] = None,
    contact_company: Optional[str] = None,
    contact_position: Optional[str] = None,
) -> Contact_requests:
    contact_request = Contact_requests(
        chat_id=chat_id,
        contact_name=contact_name,
        contact_phone_number=clean_contact_phone_number(contact_phone_number),
        contact_display_name=contact_display_name,
        contact_company=contact_company,
        contact_position=contact_position,
    )
    db.add(contact_request)
    db.commit()
    db.refresh(contact_request)
    return contact_request


def update_contact(
    db: Session,
    contact_id: int,
    name: Optional[str] = None,
    phone_number: Optional[str] = None,
    display_name: Optional[str] = None,
    company: Optional[str] = None,
    position: Optional[str] = None,
) -> Optional[Contact]:
    contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if contact is None:
        return None

    if name is not None:
        contact.name = name
    if phone_number is not None:
        contact.phone_number = clean_contact_phone_number(phone_number)
    if display_name is not None:
        contact.display_name = display_name
    if company is not None:
        contact.company = company

    db.commit()
    db.refresh(contact)
    return contact


def get_contact_by_id(db: Session, contact_id: int) -> Optional[Contact]:
    return db.query(Contact).filter(Contact.id == contact_id).first()


def delete_contact(db: Session, contact_id: int):
    contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if contact is None:
        return {"deleted": False, "reason": "not_found"}

    try:
        from app.models import ChatMembers

        referenced = (
            db.query(ChatMembers).filter(ChatMembers.contact_id == contact_id).count() > 0
        )
    except Exception:
        referenced = False

    if referenced:
        return {"deleted": False, "reason": "referenced"}

    db.delete(contact)
    db.commit()
    return {"deleted": True}


def get_all_contacts(db: Session) -> List[Contact]:
    return db.query(Contact).order_by(Contact.created_at.desc()).all()


def get_all_contact_requests(db: Session, status: str) -> List[Dict]:
    rows = (
        db.query(Contact_requests, Chats)
        .outerjoin(Chats, Contact_requests.chat_id == Chats.id)
        .order_by(Contact_requests.created_at.desc())
        .filter(Contact_requests.status == status)
        .all()
    )

    return [
        {
            "id": contact_request.id,
            "chat_id": contact_request.chat_id,
            "contact_name": contact_request.contact_name,
            "contact_phone_number": contact_request.contact_phone_number,
            "contact_display_name": contact_request.contact_display_name,
            "contact_company": contact_request.contact_company,
            "contact_position": contact_request.contact_position,
            "status": contact_request.status,
            "created_at": (
                contact_request.created_at.isoformat()
                if contact_request.created_at
                else None
            ),
            "chat": {
                "id": chat.id,
                "name": chat.name,
                "user_id": chat.user_id,
                "status": chat.status,
                "quotation_id": chat.quotation_id,
                "description": chat.description,
                "created_at": chat.created_at.isoformat() if chat.created_at else None,
            }
            if chat
            else None,
        }
        for contact_request, chat in rows
    ]


def approve_contact_request(db: Session, contact_request_id: int) -> Dict:
    contact_request = (
        db.query(Contact_requests)
        .filter(Contact_requests.id == contact_request_id)
        .first()
    )
    if contact_request is None:
        return {"approved": False, "reason": "not_found"}

    if contact_request.status != "pending":
        return {"approved": False, "reason": "invalid_status"}

    chat = db.query(Chats).filter(Chats.id == contact_request.chat_id).first()
    if chat is None:
        return {"approved": False, "reason": "chat_not_found"}

    try:
        contact = (
            db.query(Contact)
            .filter(Contact.phone_number == contact_request.contact_phone_number)
            .first()
        )
        if contact is None:
            contact = Contact(
                name=contact_request.contact_name,
                phone_number=contact_request.contact_phone_number,
                display_name=contact_request.contact_display_name,
                company=contact_request.contact_company,
                position=contact_request.contact_position,
            )
            db.add(contact)
            db.flush()

        chat_member = (
            db.query(ChatMembers)
            .filter(
                ChatMembers.chat_id == chat.id,
                ChatMembers.contact_id == contact.id,
            )
            .first()
        )
        if chat_member is None:
            access_token = create_access_token(
                {
                    "sub": f"chat:{chat.id}:contact:{contact.id}",
                    "chat_id": chat.id,
                    "contact_id": contact.id,
                    "token_use": "chat_contact",
                },
                expires_delta=timedelta(days=180),
            )
            chat_member = ChatMembers(
                chat_id=chat.id,
                contact_id=contact.id,
                token=encrypt_token(access_token) if access_token else None,
                access_code=generate_alphanumeric_code(),
            )
            db.add(chat_member)

        contact_request.status = "approved"
        db.commit()
        db.refresh(contact_request)
        db.refresh(contact)
        db.refresh(chat_member)
    except Exception:
        db.rollback()
        raise

    return {
        "approved": True,
        "contact_request": contact_request,
        "contact": contact,
        "chat_member": chat_member,
    }
