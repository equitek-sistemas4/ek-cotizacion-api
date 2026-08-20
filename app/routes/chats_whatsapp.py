from typing import Optional

from fastapi import APIRouter, Depends, Form, HTTPException
from sqlalchemy.orm import Session

from app.crud.chats_whatsapp import (
    create_chat_whatsapp as create_chat_whatsapp_db,
    delete_chat_whatsapp as delete_chat_whatsapp_db,
    get_all_chats_whatsapp as get_all_chats_whatsapp_db,
    get_chat_whatsapp_by_id,
    update_chat_whatsapp as update_chat_whatsapp_db,
)
from app.database import get_db, get_db_vmaps


router = APIRouter(prefix="/chats-whatsapp", tags=["chats-whatsapp"])


def serialize_chat_whatsapp(chat) -> dict:
    return {
        "id": chat.id,
        "user_id": chat.user_id,
        "contact_id": chat.contact_id,
        "status": chat.status,
        "created_at": chat.created_at.isoformat() if chat.created_at else None,
    }


@router.post("/create")
def create_chat_whatsapp_route(
    user_id: int = Form(...),
    contact_id: Optional[int] = Form(None),
    db: Session = Depends(get_db),
):
    chat = create_chat_whatsapp_db(db, user_id=user_id, contact_id=contact_id)
    return {
        "success": True,
        "message": "Chat de WhatsApp creado",
        "data": serialize_chat_whatsapp(chat),
    }


@router.get("/list")
def get_all_chats_whatsapp_route(
    db: Session = Depends(get_db),
    db_vmaps: Session = Depends(get_db_vmaps),
):
    chats = get_all_chats_whatsapp_db(db, db_vmaps)
    return {
        "success": True,
        "data": chats,
    }


@router.get("/{chat_whatsapp_id}")
def get_chat_whatsapp_route(
    chat_whatsapp_id: int,
    db: Session = Depends(get_db),
):
    chat = get_chat_whatsapp_by_id(db, chat_whatsapp_id)
    if chat is None:
        raise HTTPException(status_code=404, detail="Chat de WhatsApp no encontrado")

    return {"success": True, "data": serialize_chat_whatsapp(chat)}


@router.put("/{chat_whatsapp_id}")
def update_chat_whatsapp_route(
    chat_whatsapp_id: int,
    user_id: Optional[int] = Form(None),
    contact_id: Optional[int] = Form(None),
    status: Optional[int] = Form(None),
    db: Session = Depends(get_db),
):
    chat = update_chat_whatsapp_db(
        db,
        chat_whatsapp_id=chat_whatsapp_id,
        user_id=user_id,
        contact_id=contact_id,
        status=status,
    )
    if chat is None:
        raise HTTPException(status_code=404, detail="Chat de WhatsApp no encontrado")

    return {
        "success": True,
        "message": "Chat de WhatsApp actualizado",
        "data": serialize_chat_whatsapp(chat),
    }


@router.delete("/{chat_whatsapp_id}")
def delete_chat_whatsapp_route(
    chat_whatsapp_id: int,
    db: Session = Depends(get_db),
):
    if not delete_chat_whatsapp_db(db, chat_whatsapp_id):
        raise HTTPException(status_code=404, detail="Chat de WhatsApp no encontrado")

    return {"success": True, "message": "Chat de WhatsApp eliminado"}
