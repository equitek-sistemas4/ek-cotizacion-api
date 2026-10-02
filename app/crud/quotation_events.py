import re
import unicodedata
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Iterable, List, Optional

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
    normalized = unicodedata.normalize("NFKD", value or "")
    normalized = "".join(
        character for character in normalized if not unicodedata.combining(character)
    )
    return " ".join(re.sub(r"[^a-z0-9]+", " ", normalized.lower()).split())


def normalize_section_key(section_key: Optional[str]) -> Optional[str]:
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
    return get_quotation_rankings(db, db_quote, [quotation_id])[quotation_id]


def _empty_quotation_ranking(quotation_id: int) -> dict:
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

    return {
        "quotation_id": quotation_id,
        "sections": sections,
        "sections_by_key": sections_by_key,
        "total_openings": 0,
        "weighted_openings_total": 0,
    }


def get_quotation_rankings(
    db: Session,
    db_quote: Session,
    quotation_ids: Iterable[int],
    include_sections: bool = True,
) -> Dict[int, dict]:
    unique_quotation_ids = list(dict.fromkeys(quotation_ids))
    if not unique_quotation_ids:
        return {}

    rankings = {
        quotation_id: _empty_quotation_ranking(quotation_id)
        for quotation_id in unique_quotation_ids
    }

    rows = (
        db.query(QuotationEvent, Contact)
        .join(Contact, Contact.id == QuotationEvent.contact_id)
        .filter(
            QuotationEvent.quotation_id.in_(unique_quotation_ids),
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

        key = (event.quotation_id, contact.id, section_key)
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

    for (quotation_id, _contact_id, _section_key), detail in (
        openings_by_contact_and_section.items()
    ):
        ranking = rankings[quotation_id]
        section = ranking["sections_by_key"][detail["section_key"]]
        detail["weighted_openings"] = (
            (section["section_value"] + detail["role_score"])
            * detail["openings"]
        )
        section["contacts"].append(detail)
        section["total_openings"] += detail["openings"]
        section["weighted_total"] += detail["weighted_openings"]
        ranking["total_openings"] += detail["openings"]
        ranking["weighted_openings_total"] += detail["weighted_openings"]

    quotation_totals = dict(
        db_quote.query(ncrm_coti.idcoti, ncrm_coti.costo)
        .filter(ncrm_coti.idcoti.in_(unique_quotation_ids))
        .all()
    )

    for quotation_id, ranking_data in rankings.items():
        for section in ranking_data["sections"]:
            section["contacts"].sort(
                key=lambda contact: contact["contact_name"] or ""
            )

        quotation_total = Decimal(str(quotation_totals.get(quotation_id) or 0))
        ranking = (
            Decimal(ranking_data["weighted_openings_total"]) * quotation_total
        ) / Decimal("1000000")
        ranking_data.update(
            {
                "quotation_final_total": float(quotation_total),
                "ranking": float(ranking),
                "ranking_rounded": int(
                    ranking.quantize(Decimal("1"), rounding=ROUND_HALF_UP)
                ),
            }
        )
        ranking_data.pop("sections_by_key")
        if not include_sections:
            ranking_data.pop("sections")

    return rankings


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
    event = get_quotation_event_by_id(db, event_id, include_inactive=True)
    if event is None:
        return False

    event.status = 0
    db.commit()
    return True
