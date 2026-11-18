import asyncio
import logging
from typing import List, Set

from app.config import settings
from app.database import SessionLocal
from app.models import Chats_Whatsapp, Contact, Messages, UserAlertSettings
from app.services.whatsapp import WhatsAppService
from app.utils.utils import normalize_phone_number

logger = logging.getLogger(__name__)

PENDING_MESSAGE_TEMPLATE = "pending_message_whatsapp"
PENDING_MESSAGE_URL = "https://ek-ws.com.mx/chat-whatsapp"
PENDING_MESSAGE_DELAY_SECONDS = 120


_pending_alert_tasks: Set[asyncio.Task] = set()


def schedule_pending_whatsapp_alert(message_id: int) -> None:
    task = asyncio.ensure_future(_send_pending_whatsapp_alert(message_id))
    _pending_alert_tasks.add(task)
    task.add_done_callback(_pending_alert_tasks.discard)


async def _send_pending_whatsapp_alert(message_id: int) -> None:
    await asyncio.sleep(PENDING_MESSAGE_DELAY_SECONDS)

    db = SessionLocal()
    try:
        message = db.get(Messages, message_id)
        if message is None or message.direction != "incoming":
            return

        contact = (
            db.query(Contact)
            .filter(Contact.phone_number.in_(_phone_lookup_values(message.phone_number)))
            .first()
        )
        if contact is None:
            logger.info(
                "Alerta de WhatsApp omitida: no existe contacto para message_id=%s",
                message_id,
            )
            return

        chat = (
            db.query(Chats_Whatsapp)
            .filter(
                Chats_Whatsapp.contact_id == contact.id,
                Chats_Whatsapp.status == 1,
            )
            .order_by(Chats_Whatsapp.created_at.desc())
            .first()
        )
        if chat is None:
            logger.info(
                "Alerta de WhatsApp omitida: contacto_id=%s sin chat activo",
                contact.id,
            )
            return

        alert_settings = db.get(UserAlertSettings, chat.user_id)
        if (
            alert_settings is None
            or alert_settings.status != 1
            or not alert_settings.whatsapp_phone_number
        ):
            logger.warning(
                "Alerta de WhatsApp omitida: vendedor_id=%s sin teléfono de alerta activo",
                chat.user_id,
            )
            return

        contact_name = contact.display_name or contact.name or "Cliente"
        await WhatsAppService().send_template_message(
            to=alert_settings.whatsapp_phone_number,
            template=PENDING_MESSAGE_TEMPLATE,
            parameters=[contact_name, PENDING_MESSAGE_URL],
            language_code=settings.whatsapp_alert_template_language,
        )
        logger.info(
            "Alerta de WhatsApp enviada: message_id=%s contact_id=%s vendedor_id=%s",
            message_id,
            contact.id,
            chat.user_id,
        )
    except Exception:
        logger.exception(
            "No se pudo enviar alerta pendiente de WhatsApp para message_id=%s",
            message_id,
        )
    finally:
        db.close()


def _phone_lookup_values(phone_number: str) -> List[str]:
    clean_phone_number = phone_number.replace("+", "").strip()
    lookup_values = {clean_phone_number, normalize_phone_number(clean_phone_number)}

    if clean_phone_number.startswith("521"):
        lookup_values.add(f"52{clean_phone_number[3:]}")
    if clean_phone_number.startswith("52") and not clean_phone_number.startswith("521"):
        lookup_values.add(f"521{clean_phone_number[2:]}")

    return list(lookup_values)
