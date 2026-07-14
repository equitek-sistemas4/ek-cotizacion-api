from typing import List, Optional, Tuple

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.config import settings
from app.models import ChatMembers, ChatMessages, Chats, Messages, Contact
from app.services.whatsapp import WhatsAppService
from app.utils.utils import get_whatsapp_message_id, normalize_phone_number


def raise_message_http_exception(db: Session, exc: Exception) -> None:
    db.rollback()
    raise HTTPException(status_code=500, detail=str(exc)) from exc


def get_sender_phone_number() -> Optional[str]:
    phone_number = settings.whatsapp_phone_number or settings.whatsapp_phone_number_id
    if not phone_number:
        return None
    return phone_number.replace("+", "").strip()


def get_phone_number_lookup_values(phone_number: str) -> List[str]:
    clean_phone_number = phone_number.replace("+", "").strip()
    lookup_values = {
        clean_phone_number,
        normalize_phone_number(clean_phone_number),
    }

    if clean_phone_number.startswith("521"):
        lookup_values.add(f"52{clean_phone_number[3:]}")
    if clean_phone_number.startswith("52") and not clean_phone_number.startswith("521"):
        lookup_values.add(f"521{clean_phone_number[2:]}")

    return list(lookup_values)


def get_media_message_type(content_type: Optional[str]) -> str:
    if not content_type:
        return "document"
    if content_type.startswith("image/"):
        return "image"
    if content_type.startswith("video/"):
        return "video"
    if content_type.startswith("audio/"):
        return "audio"
    return "document"


def create_outgoing_whatsapp_message(
    db: Session,
    phone_number: str,
    message_type: str,
    text: str,
    result: dict,
) -> Messages:
    try:
        message = Messages(
            phone_number=normalize_phone_number(phone_number),
            direction="outgoing",
            message_type=message_type,
            text=text,
            whatsapp_message_id=get_whatsapp_message_id(result),
        )
        db.add(message)
        db.commit()
        db.refresh(message)
        return message
    except Exception as exc:
        raise_message_http_exception(db, exc)


async def send_and_save_text_message(
    db: Session,
    service: WhatsAppService,
    to: str,
    text: str,
) -> Tuple[dict, Messages]:
    try:
        result = await service.send_text_message(to, text)
        message = create_outgoing_whatsapp_message(
            db,
            phone_number=to,
            message_type="text",
            text=text,
            result=result,
        )
        return result, message
    except HTTPException:
        raise
    except Exception as exc:
        raise_message_http_exception(db, exc)


async def forward_incoming_message_to_chat_members(
    db: Session,
    service: WhatsAppService,
    sender_phone_number: str,
    text: Optional[str],
) -> dict:
    if not text:
        return {
            "sender": None,
            "sent": [],
            "failed": [],
            "chats": [],
            "message": "Mensaje sin texto para reenviar",
        }

    sender = (
        db.query(Contact)
        .filter(Contact.phone_number.in_(get_phone_number_lookup_values(sender_phone_number)))
        .first()
    )
    if sender is None:
        return {
            "sender": None,
            "sent": [],
            "failed": [],
            "chats": [],
            "message": "No se encontro contacto para el telefono emisor",
        }

    sender_memberships = (
        db.query(ChatMembers, Chats)
        .join(Chats, ChatMembers.chat_id == Chats.id)
        .filter(ChatMembers.contact_id == sender.id)
        .all()
    )

    if not sender_memberships:
        return {
            "sender": {
                "id": sender.id,
                "name": sender.name,
                "phone_number": sender.phone_number,
            },
            "sent": [],
            "failed": [],
            "chats": [],
            "message": "El usuario emisor no pertenece a ningun chat",
        }

    if len(sender_memberships) > 1:
        return {
            "sender": {
                "id": sender.id,
                "name": sender.name,
                "phone_number": sender.phone_number,
            },
            "sent": [],
            "failed": [],
            "chats": [
                {
                    "id": chat.id,
                    "name": chat.name,
                }
                for _, chat in sender_memberships
            ],
            "message": "El usuario pertenece a mas de un chat, no se puede identificar a cual reenviar",
        }

    forwarded_text = f"Envia {sender.name}: {text}"
    sent_messages = []
    failed_messages = []
    chats = []

    for sender_member, chat in sender_memberships:
        chat_message = ChatMessages(
            chat_id=sender_member.chat_id,
            contact_id=sender.id,
            text=text,
        )
        db.add(chat_message)
        db.commit()
        db.refresh(chat_message)

        chats.append({
            "id": chat.id,
            "name": chat.name,
            "chat_message_id": chat_message.id,
        })

        recipients = (
            db.query(ChatMembers, Contact)
            .join(Contact, ChatMembers.contact_id == Contact.id)
            .filter(
                ChatMembers.chat_id == sender_member.chat_id,
                ChatMembers.contact_id != sender.id,
            )
            .all()
        )

        for recipient_member, recipient in recipients:
            if not recipient.phone_number:
                failed_messages.append({
                    "chat_id": sender_member.chat_id,
                    "contact_id": recipient_member.contact_id,
                    "error": "Usuario sin telefono",
                })
                continue

            try:
                result = await service.send_text_message(recipient.phone_number, forwarded_text)
                message = create_outgoing_whatsapp_message(
                    db,
                    phone_number=recipient.phone_number,
                    message_type="text",
                    text=forwarded_text,
                    result=result,
                )
                sent_messages.append({
                    "chat_id": sender_member.chat_id,
                    "contact_id": recipient.id,
                    "phone_number": recipient.phone_number,
                    "saved_message_id": message.id,
                    "whatsapp_message_id": message.whatsapp_message_id,
                    "data": result,
                })
            except Exception as exc:
                db.rollback()
                failed_messages.append({
                    "chat_id": sender_member.chat_id,
                    "contact_id": recipient.id,
                    "phone_number": recipient.phone_number,
                    "error": str(exc),
                })

    return {
        "sender": {
            "id": sender.id,
            "name": sender.name,
            "phone_number": sender.phone_number,
        },
        "sent": sent_messages,
        "failed": failed_messages,
        "chats": chats,
        "forwarded_text": forwarded_text,
    }


async def chat_send_and_save_text_message(
    db: Session,
    service: WhatsAppService,
    chat_id: int,
    sender_id: int,
    text: Optional[str] = None,
    file_bytes: Optional[bytes] = None,
    filename: Optional[str] = None,
    content_type: Optional[str] = None,
) -> dict:
    try:
        members = db.query(ChatMembers).filter(ChatMembers.chat_id == chat_id).all()
        sent_messages = []
        failed_messages = []
        media_id = None
        media_type = None
        upload_result = None

        if file_bytes:
            media_type = get_media_message_type(content_type)
            upload_result = await service.upload_media(
                file_bytes=file_bytes,
                filename=filename or "archivo",
                content_type=content_type or "application/octet-stream",
            )
            media_id = upload_result.get("id")
            if not media_id:
                raise RuntimeError(f"WhatsApp no regreso media id: {upload_result}")

        # Crear un solo ChatMessages con el user_id del remitente
        saved_text = text or filename or media_type or ""
        chat_message = ChatMessages(
            chat_id=chat_id,
            sender_id=sender_id,
            sender_type="user",
            text=saved_text,
        )
        db.add(chat_message)
        db.commit()
        db.refresh(chat_message)

        for member in members:
            contact = db.query(Contact).filter(Contact.id == member.contact_id).first()
            if not contact or not contact.phone_number:
                failed_messages.append({
                    "contact_id": member.contact_id,
                    "error": "Contacto sin telefono",
                })
                continue

            try:
                if media_id and media_type:
                    result = await service.send_media_message(
                        to=contact.phone_number,
                        media_type=media_type,
                        media_id=media_id,
                        caption=text,
                        filename=filename,
                    )
                    message_type = media_type
                else:
                    result = await service.send_text_message(contact.phone_number, text or "")
                    message_type = "text"

                message = create_outgoing_whatsapp_message(
                    db,
                    phone_number=contact.phone_number,
                    message_type=message_type,
                    text=saved_text,
                    result=result,
                )

                sent_messages.append({
                    "contact_id": contact.id,
                    "phone_number": contact.phone_number,
                    "saved_message_id": message.id,
                    "whatsapp_message_id": message.whatsapp_message_id,
                    "chat_message_id": chat_message.id,
                    "message_type": message_type,
                    "filename": filename,
                    "data": result,
                })
            except Exception as exc:
                db.rollback()
                failed_messages.append({
                    "contact_id": contact.id,
                    "phone_number": contact.phone_number,
                    "error": str(exc),
                })

        return {
            "sent": sent_messages,
            "failed": failed_messages,
            "media": {
                "id": media_id,
                "type": media_type,
                "filename": filename,
                "content_type": content_type,
                "upload_response": upload_result,
            } if media_id else None,
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise_message_http_exception(db, exc)
        


async def send_and_save_template_message(
    db: Session,
    service: WhatsAppService,
    to: str,
    template: str,
    parameters: Optional[List] = None,
    language_code: str = "en_US",
    components: Optional[List] = None,
) -> Tuple[dict, Messages]:
    try:
        result = await service.send_template_message(
            to=to,
            template=template,
            parameters=parameters,
            language_code=language_code,
            components=components,
        )
        message = create_outgoing_whatsapp_message(
            db,
            phone_number=to,
            message_type="template",
            text=template,
            result=result,
        )
        return result, message
    except HTTPException:
        raise
    except Exception as exc:
        raise_message_http_exception(db, exc)


def get_received_messages(
    db: Session,
    phone_number: Optional[str] = None,
    limit: int = 100,
) -> List[Messages]:
    query = db.query(Messages).filter(Messages.direction == "incoming")

    if phone_number:
        query = query.filter(
            Messages.phone_number == normalize_phone_number(phone_number)
        )

    return (
        query
        .order_by(Messages.created_at.desc())
        .limit(limit)
        .all()
    )


def get_chat_messages(
    db: Session,
    phone_number: str,
    limit: int = 100,
) -> List[Messages]:
    return (
        db.query(Messages)
        .filter(Messages.phone_number == normalize_phone_number(phone_number))
        .order_by(Messages.created_at.asc())
        .limit(limit)
        .all()
    )


def getAllMessages(db: Session) -> List[Messages]:
    return db.query(Messages).order_by(Messages.created_at.desc()).all()
