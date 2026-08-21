from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from app.models import ChatMembers, Chats, Contact, QuotationEvent


def create_quotation_event(
    db: Session,
    quotation_id: int,
    contact_id: int,
    event_name: str,
    section_key: Optional[str] = None,
    element_key: Optional[str] = None,
) -> QuotationEvent:
    event = QuotationEvent(
        quotation_id=quotation_id,
        contact_id=contact_id,
        event_name=event_name,
        section_key=section_key,
        element_key=element_key,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def get_quotation_event_by_id(
    db: Session,
    event_id: int,
    include_inactive: bool = False,
) -> Optional[QuotationEvent]:
    query = db.query(QuotationEvent).filter(QuotationEvent.id == event_id)
    if not include_inactive:
        query = query.filter(QuotationEvent.status == 1)
    return query.first()


def get_quotation_events(
    db: Session,
    quotation_id: Optional[int] = None,
    contact_id: Optional[int] = None,
    include_inactive: bool = False,
) -> List[QuotationEvent]:
    query = db.query(QuotationEvent)
    if quotation_id is not None:
        query = query.filter(QuotationEvent.quotation_id == quotation_id)
    if contact_id is not None:
        query = query.filter(QuotationEvent.contact_id == contact_id)
    if not include_inactive:
        query = query.filter(QuotationEvent.status == 1)
    return query.order_by(QuotationEvent.created_at.desc()).all()


def get_contact_with_quotation_events(
    db: Session,
    quotation_id: int,
    include_inactive: bool = True,
) -> dict:
    """Obtiene contactos de los chats de una cotizacion y sus eventos."""
    rows = (
        db.query(Chats, Contact)
        .join(ChatMembers, ChatMembers.chat_id == Chats.id)
        .join(Contact, Contact.id == ChatMembers.contact_id)
        .filter(Chats.quotation_id == quotation_id)
        .all()
    )

    contacts_by_id: Dict[int, dict] = {}
    for chat, contact in rows:
        contact_data = contacts_by_id.setdefault(
            contact.id,
            {
                "id": contact.id,
                "name": contact.name,
                "display_name": contact.display_name,
                "phone_number": contact.phone_number,
                "company": contact.company,
                "position": contact.position,
                "status": contact.status,
                "created_at": (
                    contact.created_at.isoformat() if contact.created_at else None
                ),
                "chat_ids": [],
                "events": [],
            },
        )
        if chat.id not in contact_data["chat_ids"]:
            contact_data["chat_ids"].append(chat.id)

    contact_ids = list(contacts_by_id)
    if not contact_ids:
        return {"quotation_id": quotation_id, "contacts": []}

    events_query = db.query(QuotationEvent).filter(
        QuotationEvent.contact_id.in_(contact_ids),
        QuotationEvent.quotation_id == quotation_id,
    )
    if not include_inactive:
        events_query = events_query.filter(QuotationEvent.status == 1)

    for event in events_query.order_by(QuotationEvent.created_at.desc()).all():
        contacts_by_id[event.contact_id]["events"].append(
            {
                "id": event.id,
                "quotation_id": event.quotation_id,
                "event_name": event.event_name,
                "section_key": event.section_key,
                "element_key": event.element_key,
                "status": event.status,
                "created_at": (
                    event.created_at.isoformat() if event.created_at else None
                ),
            }
        )

    return {
        "quotation_id": quotation_id,
        "contacts": list(contacts_by_id.values()),
    }


def update_quotation_event(
    db: Session,
    event_id: int,
    event_name: Optional[str] = None,
    section_key: Optional[str] = None,
    element_key: Optional[str] = None,
    status: Optional[int] = None,
) -> Optional[QuotationEvent]:
    event = get_quotation_event_by_id(db, event_id, include_inactive=True)
    if event is None:
        return None

    if event_name is not None:
        event.event_name = event_name
    if section_key is not None:
        event.section_key = section_key
    if element_key is not None:
        event.element_key = element_key
    if status is not None:
        event.status = status

    db.commit()
    db.refresh(event)
    return event


def delete_quotation_event(db: Session, event_id: int) -> bool:
    """Baja lógica para conservar el historial de analítica."""
    event = get_quotation_event_by_id(db, event_id, include_inactive=True)
    if event is None:
        return False

    event.status = 0
    db.commit()
    return True
