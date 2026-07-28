from app.crud.chats_members import get_members_availables_of_chat
from typing import Optional

from fastapi import APIRouter, Depends, Form
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.crud.contacts import create_contact, delete_contact, get_all_contacts, update_contact
from app.database import get_db


router = APIRouter(prefix="/contacts", tags=["contacts"])


def serialize_contact(contact) -> dict:
    return {
        "id": contact.id,
        "name": contact.name,
        "phone_number": contact.phone_number,
        "display_name": contact.display_name,
        "company": contact.company,
        "created_at": contact.created_at.isoformat() if contact.created_at else None,
    }


@router.get("/list")
async def get_all_contacts_route(db: Session = Depends(get_db)):
    contacts = get_all_contacts(db)
    return {
        "success": True,
        "data": [serialize_contact(contact) for contact in contacts],
    }


@router.get("/availables/chat/{chat_id}")
async def get_contacts_by_chat_route(chat_id: int, db: Session = Depends(get_db)):
    contacts = get_members_availables_of_chat(db, chat_id=chat_id)
    return {
        "success": True,
        "data": contacts,
    }


@router.post("/create")
async def create_contact_route(
    name: str = Form(...),
    phone_number: str = Form(...),
    display_name: Optional[str] = Form(None),
    company: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    contact = create_contact(
        db,
        name=name,
        phone_number=phone_number,
        display_name=display_name,
        company=company,
    )

    return {
        "success": True,
        "message": "Contacto creado",
        "data": serialize_contact(contact),
    }


@router.put("/update/{contact_id}")
async def update_contact_route(
    contact_id: int,
    name: Optional[str] = Form(None),
    phone_number: Optional[str] = Form(None),
    display_name: Optional[str] = Form(None),
    company: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    contact = update_contact(
        db,
        contact_id=contact_id,
        name=name,
        phone_number=phone_number,
        display_name=display_name,
        company=company,
    )

    if contact is None:
        return {
            "success": False,
            "message": "Contacto no encontrado",
        }

    return {
        "success": True,
        "message": "Contacto actualizado",
        "data": serialize_contact(contact),
    }



@router.delete("/delete/{contact_id}")
async def delete_contact_route(contact_id: int, db: Session = Depends(get_db)):
    result = delete_contact(db, contact_id)
    if not result.get("deleted"):
        reason = result.get("reason")
        if reason == "not_found":
            return JSONResponse(
                status_code=404, content={"success": False, "message": "Contacto no encontrado"}
            )
        if reason == "referenced":
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "message": "No se puede eliminar: el contacto está asociado a uno o más miembros de chat",
                },
            )
        return JSONResponse(
            status_code=400, content={"success": False, "message": "No se pudo eliminar el contacto"}
        )

    return JSONResponse(status_code=200, content={"success": True, "message": "Contacto eliminado"})
