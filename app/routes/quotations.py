from datetime import timedelta

from fastapi import APIRouter, Depends, Form
from sqlalchemy.orm import Session

from app.database import get_db
from app.crud.chats import create_chat, get_chat_by_id
from app.crud.chats_members import add_member_to_chat, get_chat_member, update_token_member_chat
from app.crud.contacts import get_contact_by_id
from app.utils.utils import create_access_token, decrypt_token


router = APIRouter(prefix="/quotations", tags=["quotations"])


@router.post("/create-link")
async def create_link_quotation(
    name: str = Form(...),
    user_id: int = Form(...),
    contact_id: int = Form(...),
    db: Session = Depends(get_db),
):
    chat = create_chat(
        db,
        name,
        user_id
    )

    contact = get_contact_by_id(db, contact_id)
    if contact is None:
        return {
            "success": False,
            "message": "Contacto no encontrado",
        }

    member = add_member_to_chat(db, chat.id, contact_id)
    if member is None:
        return {
            "success": False,
            "message": "El contacto no pertenece al chat",
        }
    
    """ access_token = create_access_token({
        "sub": f"chat:{chat.id}:contact:{contact_id}",
        "chat_id": chat.id,
        "contact_id": contact_id,
        "token_use": "chat_contact",
    }, expires_delta=timedelta(days=180))

    chat_member = update_token_member_chat(db, chat.id, contact_id, access_token)
    if chat_member is None:
        return {
            "success": False,
            "message": "No se pudo actualizar el token del miembro",
        } """

    return {
        "success": True,
        "message": "Token generado",
        "data": {
            "access_token": member.token,
            "access_code": member.access_code,
            "token_type": "bearer",
            "chat_id": chat.id,
            "contact_id": contact_id,
        },
    }

    
