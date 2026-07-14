from typing import List, Optional

from sqlalchemy.orm import Session

from app.models import Contact


def clean_contact_phone_number(phone_number: str) -> str:
    return phone_number.replace("+", "").strip()


def create_contact(
    db: Session,
    name: str,
    phone_number: str,
    display_name: Optional[str] = None,
    company: Optional[str] = None,
) -> Contact:
    contact = Contact(
        name=name,
        phone_number=clean_contact_phone_number(phone_number),
        display_name=display_name,
        company=company,
    )
    db.add(contact)
    db.commit()
    db.refresh(contact)
    return contact


def update_contact(
    db: Session,
    contact_id: int,
    name: Optional[str] = None,
    phone_number: Optional[str] = None,
    display_name: Optional[str] = None,
    company: Optional[str] = None,
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


def delete_contact(db: Session, contact_id: int) -> bool:
    contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if contact is None:
        return False

    db.delete(contact)
    db.commit()
    return True


def get_all_contacts(db: Session) -> List[Contact]:
    return db.query(Contact).order_by(Contact.created_at.desc()).all()
