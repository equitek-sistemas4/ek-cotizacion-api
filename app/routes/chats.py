from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session

from app.crud.chats import (
    create_chat as create_chat_db,
    delete_chat as delete_chat_db,
    get_all_chats as get_all_chats_db,
    get_chat_by_id,
    get_chat_with_members as get_chat_with_members_db,
)
from app.crud.chats_messages import get_messages
from app.crud.chats_members import add_member_to_chat, update_token_member_chat
from app.crud.messages import (
    get_chat_messages as get_chat_messages_from_db,
    chat_send_and_save_text_message,
)
from app.crud.contacts import get_contact_by_id
from app.database import get_db, get_db_vmaps
from app.schemas.chat_messages import serialize_chat_message
from app.services.whatsapp import WhatsAppService
from app.utils.utils import create_access_token, serialize_message


router = APIRouter(prefix="/chats", tags=["chats"])
service = WhatsAppService()
DEFAULT_CHAT_MEMBER_CONTACT_ID = 1


@router.post("/create")
async def create_chat_route(
    name: str = Form(...),
    description: Optional[str] = Form(None),
    user_id: int = Form(...),
    db: Session = Depends(get_db),
):

    chat = create_chat_db(
        db,
        name,
        description,
        user_id,
    )

    return {
        "success": True,
        "message": "Chat creado",
        "data": {
            "id": chat.id,
            "name": chat.name,
            "description": chat.description,
        }
    }


@router.get("/list")
async def get_all_chats_route(
    search: Optional[str] = Query(None, min_length=1),
    limit: Optional[int] = Query(None, ge=1, le=1024),
    after: Optional[str] = Query(None),
    before: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    chats = get_all_chats_db(db, search=search)
    return {
        "success": True,
        "data": [
            {
                "id": chat.id,
                "name": chat.name,
                "description": chat.description,
                "quotation_id": chat.quotation_id,
                "status": chat.status,
                "created_at": chat.created_at.isoformat() if chat.created_at else None,
            }
            for chat in chats
        ],
    }


@router.get("/{chat_id}")
async def get_chat_with_members_route(chat_id: int, db: Session = Depends(get_db)):
    chat = get_chat_with_members_db(db, chat_id)
    if chat is None:
        return {
            "success": False,
            "message": "Chat no encontrado",
        }

    return {
        "success": True,
        "data": chat,
    }


@router.delete("/{chat_id}")
async def delete_chat_route(chat_id: int, db: Session = Depends(get_db)):
    deleted = delete_chat_db(db, chat_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Chat no encontrado")

    return {
        "success": True,
        "message": "Chat eliminado",
    }


@router.get("/{chat_id}/messages")
async def get_chat_messages_route(
    chat_id: int,
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    db_vmaps: Session = Depends(get_db_vmaps),
):
    chat = get_chat_by_id(db, chat_id)
    if chat is None:
        return {
            "success": False,
            "message": "Chat no encontrado",
        }

    messages = get_messages(db, db_vmaps, chat_id, limit)
    return {
        "success": True,
        "data": {
            "chat_id": chat.id,
            "chat_name": chat.name,
            "messages": [
                serialize_chat_message(message, contact, user)
                for message, contact, user in messages
            ],
        },
    }


@router.post("/{chat_id}/members")
async def add_chat_member(
    chat_id: int,
    contact_ids: List[int] = Form(...),
    db: Session = Depends(get_db),
):
    chat = get_chat_by_id(db, chat_id)
    if chat is None:
        return {
            "success": False,
            "message": "Chat no encontrado",
        }

    if not contact_ids:
        return {
            "success": False,
            "message": "Debes enviar al menos un contact_id",
        }

    created_members = []
    missing_contacts = []

    for contact_id in contact_ids:
        contact = get_contact_by_id(db, contact_id)
        if contact is None:
            missing_contacts.append(contact_id)
            continue

        members = add_member_to_chat(
            db,
            chat_id=chat_id,
            contact_ids=[contact_id],
        )
        created_members.extend(members)

    return {
        "success": True,
        "message": "Participantes agregados",
        "data": {
            "chat_id": chat_id,
            "added_members": [
                {
                    "id": member.id,
                    "chat_id": member.chat_id,
                    "contact_id": member.contact_id,
                }
                for member in created_members
            ],
            "missing_contacts": missing_contacts,
        }
    }


@router.post("/{chat_id}/send")
async def send_message_to_chat(
    chat_id: int,
    text: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
):
    if not text and file is None:
        raise HTTPException(
            status_code=400,
            detail="Debes enviar text o file",
        )

    chat = get_chat_with_members_db(db, chat_id)
    if chat is None:
        return {
            "success": False,
            "message": "Chat no encontrado",
        }

    file_bytes = await file.read() if file else None
    if file is not None and not file_bytes:
        raise HTTPException(
            status_code=400,
            detail="El archivo esta vacio",
        )

    result = await chat_send_and_save_text_message(
        db,
        service,
        chat_id,
        sender_id=1,
        text=text,
        file_bytes=file_bytes,
        filename=file.filename if file else None,
        content_type=file.content_type if file else None,
    )
    sent_messages = result["sent"]
    failed_messages = result["failed"]

    return {
        "success": len(failed_messages) == 0,
        "message": "Mensaje enviado al chat",
        "data": {
            "chat_id": chat["id"],
            "chat_name": chat["name"],
            "sent_count": len(sent_messages),
            "failed_count": len(failed_messages),
            "media": result.get("media"),
            "sent": sent_messages,
            "failed": failed_messages,
        },
    }
