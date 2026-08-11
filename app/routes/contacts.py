from app.crud.chats_members import get_members_availables_of_chat
from typing import Optional

from fastapi import APIRouter, Depends, Form, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.crud.contacts import (
    create_contact,
    create_contact_request,
    delete_contact,
    approve_contact_request,
    contact_exists_by_empresa_contacto_id,
    reject_contact_request,
    get_all_contact_requests,
    get_all_contacts,
    update_contact,
)
from app.database import get_db


router = APIRouter(prefix="/contacts", tags=["contacts"])


def serialize_contact(contact) -> dict:
    return {
        "id": contact.id,
        "name": contact.name,
        "phone_number": contact.phone_number,
        "display_name": contact.display_name,
        "company": contact.company,
        "status": contact.status,
        "position": contact.position,
        "idempresa_contacto": contact.idempresa_contacto,
        "created_at": contact.created_at.isoformat() if contact.created_at else None,
    }


@router.get("/list")
async def get_all_contacts_route(db: Session = Depends(get_db)):
    contacts = get_all_contacts(db)
    return {
        "success": True,
        "data": [serialize_contact(contact) for contact in contacts],
    }


@router.get("/exists/company-contact/{idempresa_contacto}")
async def contact_exists_by_empresa_contacto_id_route(
    idempresa_contacto: int,
    db: Session = Depends(get_db),
):
    contact = contact_exists_by_empresa_contacto_id(db, idempresa_contacto)
    return {
        "success": True,
        "exists": contact is not None,
        "data": serialize_contact(contact) if contact else None,
    }


@router.get("/list-requests/{status}")
async def get_all_contact_requests_route(status: Optional[str] = None, db: Session = Depends(get_db)):
    contact_requests = get_all_contact_requests(db, status=status)
    return {
        "success": True,
        "data": contact_requests,
    }


@router.post("/requests/{contact_request_id}/approve")
async def approve_contact_request_route(
    contact_request_id: int,
    db: Session = Depends(get_db),
):
    result = approve_contact_request(db, contact_request_id)
    if not result["approved"]:
        reason = result["reason"]
        if reason == "not_found":
            raise HTTPException(status_code=404, detail="Solicitud de contacto no encontrada")
        if reason == "chat_not_found":
            raise HTTPException(status_code=404, detail="Chat de la solicitud no encontrado")
        raise HTTPException(
            status_code=409,
            detail="La solicitud ya fue procesada y no puede aprobarse",
        )

    contact_request = result["contact_request"]
    contact = result["contact"]
    chat_member = result["chat_member"]
    return {
        "success": True,
        "message": "Solicitud de contacto aprobada",
        "data": {
            "contact_request": {
                "id": contact_request.id,
                "chat_id": contact_request.chat_id,
                "status": contact_request.status,
            },
            "contact": serialize_contact(contact),
            "chat_member": {
                "id": chat_member.id,
                "chat_id": chat_member.chat_id,
                "contact_id": chat_member.contact_id,
                "access_code": chat_member.access_code,
                "created_at": (
                    chat_member.created_at.isoformat()
                    if chat_member.created_at
                    else None
                ),
            },
        },
    }


@router.post("/requests/{contact_request_id}/reject")
async def reject_contact_request_route(
    contact_request_id: int,
    db: Session = Depends(get_db),
):
    result = reject_contact_request(db, contact_request_id)
    if not result["rejected"]:
        if result["reason"] == "not_found":
            raise HTTPException(status_code=404, detail="Solicitud de contacto no encontrada")
        raise HTTPException(
            status_code=409,
            detail="La solicitud ya fue procesada y no puede rechazarse",
        )

    contact_request = result["contact_request"]
    return {
        "success": True,
        "message": "Solicitud de contacto rechazada",
        "data": {
            "id": contact_request.id,
            "chat_id": contact_request.chat_id,
            "status": contact_request.status,
        },
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
    idempresa_contacto: Optional[int] = Form(None),
    fk_idempresa: Optional[int] = Form(None),
    db: Session = Depends(get_db),
):
    contact = create_contact(
        db,
        name=name,
        phone_number=phone_number,
        display_name=display_name,
        company=company,
        idempresa_contacto=idempresa_contacto,
        fk_idempresa=fk_idempresa
    )

    return {
        "success": True,
        "message": "Contacto creado",
        "data": serialize_contact(contact),
    }


@router.post("/create-request")
async def create_contact_request_route(
    chat_id: int = Form(...),
    contact_name: str = Form(...),
    contact_phone_number: str = Form(...),
    contact_display_name: Optional[str] = Form(None),
    contact_company: Optional[str] = Form(None),
    contact_position: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    contact_request = create_contact_request(
        db,
        chat_id=chat_id,
        contact_name=contact_name,
        contact_phone_number=contact_phone_number,
        contact_display_name=contact_display_name,
        contact_company=contact_company,
        contact_position=contact_position
    )

    return {
        "success": True,
        "message": "Solicitud de contacto creada",
        "data": {
            "id": contact_request.id,
            "chat_id": contact_request.chat_id,
            "contact_name": contact_request.contact_name,
            "contact_phone_number": contact_request.contact_phone_number,
            "contact_display_name": contact_request.contact_display_name,
            "contact_company": contact_request.contact_company,
            "created_at": contact_request.created_at.isoformat() if contact_request.created_at else None,
        },
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
