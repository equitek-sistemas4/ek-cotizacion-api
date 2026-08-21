from typing import Optional

from fastapi import APIRouter, Depends, Form, HTTPException, Query
from sqlalchemy.orm import Session

from app.crud.quotation_events import (
    create_quotation_event,
    delete_quotation_event,
    get_contact_with_quotation_events,
    get_quotation_event_by_id,
    get_quotation_events,
    update_quotation_event,
)
from app.database import get_db


router = APIRouter(prefix="/quotation-events", tags=["quotation-events"])


def serialize_quotation_event(event) -> dict:
    return {
        "id": event.id,
        "quotation_id": event.quotation_id,
        "contact_id": event.contact_id,
        "event_name": event.event_name,
        "section_key": event.section_key,
        "element_key": event.element_key,
        "status": event.status,
        "created_at": event.created_at.isoformat() if event.created_at else None,
    }


@router.post("/create", status_code=201)
def create_quotation_event_route(
    quotation_id: int = Form(...),
    contact_id: int = Form(...),
    event_name: str = Form(...),
    section_key: Optional[str] = Form(None),
    element_key: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    event = create_quotation_event(
        db=db,
        quotation_id=quotation_id,
        contact_id=contact_id,
        event_name=event_name,
        section_key=section_key,
        element_key=element_key,
    )
    return {"success": True, "data": serialize_quotation_event(event)}


@router.get("/list")
def get_quotation_events_route(
    quotation_id: Optional[int] = Query(None),
    contact_id: Optional[int] = Query(None),
    include_inactive: bool = Query(False),
    db: Session = Depends(get_db),
):
    events = get_quotation_events(
        db=db,
        quotation_id=quotation_id,
        contact_id=contact_id,
        include_inactive=include_inactive,
    )
    return {"success": True, "data": [serialize_quotation_event(event) for event in events]}


@router.get("/contacts-events/{quotation_id}")
def get_quotation_contacts_events_route(
    quotation_id: int,
    include_inactive: bool = Query(True),
    db: Session = Depends(get_db),
):
    result = get_contact_with_quotation_events(
        db=db,
        quotation_id=quotation_id,
        include_inactive=include_inactive,
    )
    return {"success": True, "data": result}


@router.get("/{event_id}")
def get_quotation_event_route(event_id: int, db: Session = Depends(get_db)):
    event = get_quotation_event_by_id(db, event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="Evento de cotizacion no encontrado")
    return {"success": True, "data": serialize_quotation_event(event)}


@router.put("/{event_id}")
def update_quotation_event_route(
    event_id: int,
    event_name: Optional[str] = Form(None),
    section_key: Optional[str] = Form(None),
    element_key: Optional[str] = Form(None),
    status: Optional[int] = Form(None),
    db: Session = Depends(get_db),
):
    event = update_quotation_event(
        db=db,
        event_id=event_id,
        event_name=event_name,
        section_key=section_key,
        element_key=element_key,
        status=status,
    )
    if event is None:
        raise HTTPException(status_code=404, detail="Evento de cotizacion no encontrado")
    return {"success": True, "data": serialize_quotation_event(event)}


@router.delete("/{event_id}")
def delete_quotation_event_route(event_id: int, db: Session = Depends(get_db)):
    if not delete_quotation_event(db, event_id):
        raise HTTPException(status_code=404, detail="Evento de cotizacion no encontrado")
    return {"success": True, "message": "Evento de cotizacion eliminado"}
