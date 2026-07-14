import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Form
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from app.schemas.whatsapp import WhatsAppTemplateRequestSimple, WhatsAppTemplateRequest
from app.services.whatsapp import WhatsAppService
from app.database import get_db
from app.crud.messages import (
    forward_incoming_message_to_chat_members,
    getAllMessages,
    get_received_messages as get_received_messages_from_db,
    send_and_save_text_message,
    send_and_save_template_message,
)
from app.utils.utils import (
    build_incoming_message,
    serialize_message,
)


router = APIRouter(prefix="/whatsapp", tags=["whatsapp"])
service = WhatsAppService()
logger = logging.getLogger(__name__)


# Para que funcione desde estar activa la casilla de messages en el webhook de Meta
@router.post("/send")
async def send_whatsapp_message(
    to: str = Form(...),
    text: str = Form(...),
    db: Session = Depends(get_db),
):
    result, message = await send_and_save_text_message(db, service, to, text)

    return {
        "success": True,
        "message": "Mensaje enviado",
        "saved_message_id": message.id,
        "data": result,
    }


# Para poder usar este endpoint debemos registrar la plantilla en el sistema de Meta
# https://business.facebook.com/latest/whatsapp_manager/message_templates
@router.post("/send-template")
async def send_whatsapp_template(
    payload: WhatsAppTemplateRequestSimple,
    db: Session = Depends(get_db),
):
    result, message = await send_and_save_template_message(
        db,
        service,
        to=payload.to,
        template=payload.template_name,
        parameters=payload.parameters,
        language_code=payload.language_code,
    )

    return {
        "success": True,
        "message": "Plantilla enviada",
        "saved_message_id": message.id,
        "data": result,
    }


# Para poder usar este endpoint debemos registrar la plantilla en el sistema de Meta (ruta comentada arriba)
@router.post("/send-template-meta")
async def send_whatsapp_template_meta(
    payload: WhatsAppTemplateRequest,
    db: Session = Depends(get_db),
):
    result, message = await send_and_save_template_message(
        db,
        service,
        to=payload.to,
        template=payload.template.name,
        components=payload.template.components,
        language_code=payload.template.language.code,
    )

    return {
        "success": True,
        "message": "Plantilla enviada",
        "saved_message_id": message.id,
        "data": result,
    }


@router.get("/webhook")
async def verify_webhook(
    mode: str = Query(..., alias="hub.mode"),
    token: str = Query(..., alias="hub.verify_token"),
    challenge: str = Query(..., alias="hub.challenge"),
):
    try:
        logger.warning("Verificacion webhook recibida: mode=%s token=%s", mode, token)
        verified = service.verify_webhook(mode, token, challenge)
        return PlainTextResponse(content=verified)
    except RuntimeError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


#Para el funcionamiento correcto se debe de activar en los campos de webhook el evento de "messages"
@router.post("/webhook")
async def receive_webhook(
    request: Request,
    db: Session = Depends(get_db),
):
    payload = await request.json()
    saved_messages = 0
    saved_message_ids = []
    received_messages = 0
    received_statuses = 0
    forwarded_messages = 0
    forwarded_results = []
    failed_forwards = 0

    try:
        for entry in payload.get("entry", []):
            for change in entry.get("changes", []):
                value = change.get("value", {})
                received_messages += len(value.get("messages", []))
                received_statuses += len(value.get("statuses", []))

                for msg in value.get("messages", []):
                    incoming_message = build_incoming_message(msg)
                    if incoming_message is None:
                        logger.warning("Mensaje entrante de WhatsApp sin telefono: %s", msg)
                        continue

                    db.add(incoming_message)
                    db.flush()
                    saved_message_ids.append(incoming_message.id)
                    saved_messages += 1

                    forward_result = await forward_incoming_message_to_chat_members(
                        db,
                        service,
                        incoming_message.phone_number,
                        incoming_message.text,
                    )
                    forwarded_messages += len(forward_result["sent"])
                    failed_forwards += len(forward_result["failed"])
                    forwarded_results.append({
                        "incoming_message_id": incoming_message.id,
                        "sender": forward_result["sender"],
                        "chats": forward_result["chats"],
                        "message": forward_result.get("message"),
                        "forwarded_text": forward_result.get("forwarded_text"),
                        "sent_count": len(forward_result["sent"]),
                        "failed_count": len(forward_result["failed"]),
                        "sent": forward_result["sent"],
                        "failed": forward_result["failed"],
                    })

        db.commit()

        logger.warning(
            "Webhook WhatsApp POST recibido: entries=%s messages=%s statuses=%s saved=%s ids=%s forwarded=%s failed_forwards=%s",
            len(payload.get("entry", [])),
            received_messages,
            received_statuses,
            saved_messages,
            saved_message_ids,
            forwarded_messages,
            failed_forwards,
        )

        response = service.process_webhook(payload)
        response["received_messages"] = received_messages
        response["received_statuses"] = received_statuses
        response["saved_messages"] = saved_messages
        response["saved_message_ids"] = saved_message_ids
        response["forwarded_messages"] = forwarded_messages
        response["failed_forwards"] = failed_forwards
        response["forwarded_results"] = forwarded_results

        return response
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/messages/received")
async def get_received_messages(
    phone_number: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    messages = get_received_messages_from_db(db, phone_number, limit)
    return {
        "success": True,
        "data": [serialize_message(message) for message in messages],
    }


@router.get("/messages")
async def get_all_messages(
    db: Session = Depends(get_db),
):
    messages = getAllMessages(db)

    return  {
        "success": True,
        "data": [serialize_message(message) for message in messages],
    }
