from pathlib import Path
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.crud.chats import get_chat_by_id
from app.crud.contacts import get_contact_by_id
from app.crud.users import get_user_by_id
from app.database import get_db
from app.models import ChatFiles, ChatMessages
from app.routes.chat_websocket import manager
from app.schemas.chat_messages import serialize_chat_message


router = APIRouter(prefix="/chat_files", tags=["chat_files"])

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


@router.post("/send", status_code=201)
async def send_file_message(
    chat_id: int = Form(...),
    sender_id: int = Form(...),
    sender_type: str = Form(...),
    file: UploadFile = File(...),
    text: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    """Guarda una imagen o PDF y lo asocia a un nuevo mensaje del chat."""
    sender_type = sender_type.strip().lower()
    if sender_type not in {"user", "contact"}:
        raise HTTPException(400, "sender_type debe ser user o contact")

    if get_chat_by_id(db, chat_id) is None:
        raise HTTPException(404, "Chat no encontrado")

    sender = (
        get_contact_by_id(db, sender_id)
        if sender_type == "contact"
        else get_user_by_id(db, sender_id)
    )
    if sender is None:
        detail = "Contacto no encontrado" if sender_type == "contact" else "Usuario no encontrado"
        raise HTTPException(404, detail)

    original_name = Path(file.filename or "").name
    extension = Path(original_name).suffix.lower()
    if (
        not original_name
        or extension not in ALLOWED_EXTENSIONS
        or file.content_type not in ALLOWED_CONTENT_TYPES
    ):
        raise HTTPException(400, "Solo se permiten imágenes (JPG, PNG, GIF, WEBP) y archivos PDF")

    UPLOAD_DIRECTORY.mkdir(parents=True, exist_ok=True)
    relative_path = Path("uploads") / "chat_files" / f"{uuid4().hex}{extension}"
    stored_path = PROJECT_ROOT / relative_path
    try:
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
                    raise HTTPException(413, "El archivo excede el límite de 10 MB")
                destination.write(chunk)

        message = ChatMessages(
            chat_id=chat_id,
            sender_id=sender_id,
            sender_type=sender_type,
            text=(text or original_name).strip() or original_name,
        )
        db.add(message)
        db.flush()
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
        if stored_path.exists():
            stored_path.unlink()
        raise
    finally:
        await file.close()

    serialized_message = serialize_chat_message(
        message,
        sender if sender_type == "contact" else None,
        sender if sender_type == "user" else None,
    )
    await manager.broadcast(chat_id, {"type": "message", "data": serialized_message})

    return {
        "success": True,
        "message": "Archivo enviado",
        "data": serialized_message,
    }
