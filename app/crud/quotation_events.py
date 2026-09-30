import re
import unicodedata
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from app.models import ChatMembers, Chats, Contact, QuotationEvent, ncrm_coti


SECTION_OPENED_EVENT = "section_opened"

# Estas claves son el contrato entre el frontend que registra la apertura y el
# cálculo del ranking. No se cuentan otros tipos de eventos de analítica.
SECTION_VALUES = {
    "inicio": {"name": "Inicio", "value": 0},
    "alcances": {"name": "Alcances", "value": 2},
    "equipos": {"name": "Equipos", "value": 4},
    "precios": {"name": "Precios", "value": 8},
    "analisis_financiero": {"name": "Análisis financiero", "value": 4},
    "ligas": {"name": "Ligas", "value": 3},
}


def _normalize_text(value: Optional[str]) -> str:
    """Normaliza puestos y claves para compararlos sin acentos ni formato."""
    normalized = unicodedata.normalize("NFKD", value or "")
    normalized = "".join(
        character for character in normalized if not unicodedata.combining(character)
    )
    return " ".join(re.sub(r"[^a-z0-9]+", " ", normalized.lower()).split())


def normalize_section_key(section_key: Optional[str]) -> Optional[str]:
    """Devuelve la clave canónica de una sección o ``None`` si no es válida."""
    normalized = _normalize_text(section_key)
    aliases = {
        "inicio": "inicio",
        "home": "inicio",
        "alcances": "alcances",
        "products": "alcances",
        "equipos": "equipos",
        "equipment": "equipos",
        "precios": "precios",
        "prices": "precios",
        "analisis financiero": "analisis_financiero",
        "financial": "analisis_financiero",
        "ligas": "ligas",
        "links": "ligas",
    }
    return aliases.get(normalized)


def get_role_score(position: Optional[str]) -> int:
    """Obtiene el puntaje del puesto; vacío o desconocido vale un punto."""
    normalized = _normalize_text(position)

    if any(term in normalized for term in ("dueno", "director general", "directivo")):
        return 5
    if any(term in normalized for term in ("compras", "financier")):
        return 4
    if any(term in normalized for term in ("project manager", "champion")):
        return 3
    if "mantenimiento" in normalized:
        return 2
    return 1


def get_quotation_final_total(quotation_id: int, db_quote: Session) -> Decimal:
    """Obtiene el total cotizado final almacenado en ``ncrm_coti.costo``."""
    total = (
        db_quote.query(ncrm_coti.costo)
        .filter(ncrm_coti.idcoti == quotation_id)
        .scalar()
    )
    return Decimal(str(total)) if total is not None else Decimal("0")


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


def contact_belongs_to_quotation(
    db: Session,
    quotation_id: int,
    contact_id: int,
) -> bool:
    """Comprueba que el contacto tenga acceso a la cotización indicada."""
    return (
        db.query(ChatMembers.id)
        .join(Chats, Chats.id == ChatMembers.chat_id)
        .filter(
            Chats.quotation_id == quotation_id,
            Chats.status == 1,
            ChatMembers.contact_id == contact_id,
            ChatMembers.status == 1,
        )
        .first()
        is not None
    )


def register_section_opened(
    db: Session,
    quotation_id: int,
    contact_id: int,
    section_key: str,
) -> Optional[QuotationEvent]:
    """Registra una apertura válida únicamente para un contacto autorizado."""
    canonical_section_key = normalize_section_key(section_key)
    if canonical_section_key is None:
        return None
    if not contact_belongs_to_quotation(db, quotation_id, contact_id):
        return None

    return create_quotation_event(
        db=db,
        quotation_id=quotation_id,
        contact_id=contact_id,
        event_name=SECTION_OPENED_EVENT,
        section_key=canonical_section_key,
    )


def get_quotation_ranking(
    db: Session,
    db_quote: Session,
    quotation_id: int,
) -> dict:
    sections = []
    sections_by_key = {}
    for section_key, metadata in SECTION_VALUES.items():
        section = {
            "section_key": section_key,
            "section_name": metadata["name"],
            "section_value": metadata["value"],
            "total_openings": 0,
            "weighted_total": 0,
            "contacts": [],
        }
        sections.append(section)
        sections_by_key[section_key] = section

    rows = (
        db.query(QuotationEvent, Contact)
        .join(Contact, Contact.id == QuotationEvent.contact_id)
        .filter(
            QuotationEvent.quotation_id == quotation_id,
            QuotationEvent.status == 1,
            QuotationEvent.event_name == SECTION_OPENED_EVENT,
        )
        .all()
    )

    openings_by_contact_and_section: Dict[tuple, dict] = {}
    for event, contact in rows:
        section_key = normalize_section_key(event.section_key)
        if section_key is None:
            continue

        key = (contact.id, section_key)
        detail = openings_by_contact_and_section.setdefault(
            key,
            {
                "contact_id": contact.id,
                "contact_name": contact.display_name or contact.name,
                "position": contact.position,
                "role_score": get_role_score(contact.position),
                "section_key": section_key,
                "openings": 0,
            },
        )
        detail["openings"] += 1

    weighted_openings_total = 0
    total_openings = 0
    for detail in openings_by_contact_and_section.values():
        section = sections_by_key[detail["section_key"]]
        detail["weighted_openings"] = (
            (section["section_value"] + detail["role_score"])
            * detail["openings"]
        )
        section["contacts"].append(detail)
        section["total_openings"] += detail["openings"]
        section["weighted_total"] += detail["weighted_openings"]
        total_openings += detail["openings"]
        weighted_openings_total += detail["weighted_openings"]

    for section in sections:
        section["contacts"].sort(key=lambda contact: contact["contact_name"] or "")

    quotation_total = get_quotation_final_total(quotation_id, db_quote)
    ranking = (Decimal(weighted_openings_total) * quotation_total) / Decimal("1000000")

    return {
        "quotation_id": quotation_id,
        "sections": sections,
        "total_openings": total_openings,
        "weighted_openings_total": weighted_openings_total,
        "quotation_final_total": float(quotation_total),
        "ranking": float(ranking),
        "ranking_rounded": int(
            ranking.quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        ),
    }


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
