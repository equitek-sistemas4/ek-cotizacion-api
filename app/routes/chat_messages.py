from pathlib import Path
from typing import Optional
from uuid import uuid4

from app.database import get_db
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.crud.chats import get_chat_by_id
from app.crud.chats_messages import get_messages
from app.crud.contacts import get_contact_by_id
from app.crud.users import get_user_by_id
from app.models import ChatFiles, ChatMessages
from app.routes.chat_websocket import manager
from app.schemas.chat_messages import serialize_chat_message


router = APIRouter(prefix="/chat_messages", tags=["chat_messages"])

PROJECT_ROOT = Path(__file__).resolve().parents[2]
UPLOAD_DIRECTORY = PROJECT_ROOT / "uploads" / "chat_files"
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "image/gif",
    "image/jpeg",
    "image/png",
    "image/webp",
}
ALLOWED_EXTENSIONS = {".gif", ".jpeg", ".jpg", ".pdf", ".png", ".webp"}


@router.post("/send")
async def create_chat_message_route(
    chat_id: int = Form(...),
    sender_id: int = Form(...),
    sender_type: str = Form(...),
    text: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
):
    sender_type = sender_type.strip().lower()
    if sender_type not in ("user", "contact"):
        raise HTTPException(400, "sender_type debe ser user o contact")

    text = text.strip() if text else None
    if not text and file is None:
        raise HTTPException(400, "Debes enviar text o file")

    chat = get_chat_by_id(db, chat_id)
    if chat is None:
        return {
            "success": False,
            "message": "Chat no encontrado",
        }

    contact = None
    user = None
    if sender_type == "contact":
        contact = get_contact_by_id(db, sender_id)
        if contact is None:
            return {
                "success": False,
                "message": "Contacto no encontrado",
            }
    else:
        user = get_user_by_id(db, sender_id)
        if user is None:
            return {
                "success": False,
                "message": "Usuario no encontrado",
            }

    stored_path = None
    try:
        message_text = text
        if file is not None:
            original_name = Path(file.filename or "").name
            extension = Path(original_name).suffix.lower()
            if (
                not original_name
                or extension not in ALLOWED_EXTENSIONS
                or file.content_type not in ALLOWED_CONTENT_TYPES
            ):
                raise HTTPException(400, "Solo se permiten imagenes (JPG, PNG, GIF, WEBP) y archivos PDF")

            UPLOAD_DIRECTORY.mkdir(parents=True, exist_ok=True)
            relative_path = Path("uploads") / "chat_files" / f"{uuid4().hex}{extension}"
            stored_path = PROJECT_ROOT / relative_path
            total_size = 0
            with stored_path.open("wb") as destination:
                while True:
                    chunk = await file.read(1024 * 1024)
                    if not chunk:
                        break
                    total_size += len(chunk)
                    if total_size > MAX_FILE_SIZE:
                        destination.close()
                        if stored_path.exists():
                            stored_path.unlink()
                        raise HTTPException(413, "El archivo excede el limite de 10 MB")
                    destination.write(chunk)
            if total_size == 0:
                raise HTTPException(400, "El archivo esta vacio")
            message_text = text or original_name

        message = ChatMessages(
            chat_id=chat_id,
            sender_id=sender_id,
            sender_type=sender_type,
            text=message_text,
        )
        db.add(message)
        db.flush()

        if file is not None:
            db.add(
                ChatFiles(
                    chat_message_id=message.id,
                    file_name=original_name,
                    file_path=relative_path.as_posix(),
                )
            )

        db.commit()
        db.refresh(message)
    except Exception:
        db.rollback()
        if stored_path is not None:
            if stored_path.exists():
                stored_path.unlink()
        raise
    finally:
        if file is not None:
            await file.close()

    serialized_message = serialize_chat_message(message, contact, user)

    await manager.broadcast(chat_id, {
        "type": "message",
        "data": serialized_message,
    })

    return {
        "success": True,
        "message": "Mensaje creado",
        "data": serialized_message,
    }


@router.get("/{chat_id}/messages")
async def get_chat_messages_route(
    chat_id: int,
    db: Session = Depends(get_db),
):
    chats = get_messages(db, chat_id)
    return {
        "success": True,
        "data": [
            serialize_chat_message(message, contact, user)
            for message, contact, user in chats
        ]
    }
