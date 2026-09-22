"""Procesamiento backend para el SLA de conversaciones sin respuesta."""

import logging
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, Iterable, List, Optional, Tuple

from sqlalchemy.orm import Session

from app.config import settings
from app.models import (
    ChatMembers,
    ChatMessages,
    Chats,
    ClientWaitingAlertLog,
    Contact,
    UserAlertSettings,
    Users,
)
from app.services.whatsapp import WhatsAppService

logger = logging.getLogger(__name__)

ALERT_TEMPLATE = "alert_message_pending"


def register_chat_message_for_sla(db: Session, message: ChatMessages) -> None:
    chat = db.get(Chats, message.chat_id)
    if chat is None:
        return

    timestamp = message.created_at or datetime.now()
    if message.sender_type == "contact":
        chat.hora_ultimo_mensaje_entrante = timestamp
        # Un mensaje nuevo abre o actualiza el mismo caso; no rearma alertas.
        return

    if message.sender_type == "user" and message.sender_id == chat.user_id:
        # Un log individual puede haber sido dirigido al vendedor o a su
        # supervisor. chat_id es el vínculo inequívoco para limpiar ambos.
        db.query(ClientWaitingAlertLog).filter(
            ClientWaitingAlertLog.chat_id == chat.id
        ).delete(synchronize_session=False)
        chat.hora_ultima_respuesta_vendedor = timestamp
        chat.ultima_alerta_enviada = None
        chat.etapa_escalamiento = 0


def _is_waiting(chat: Chats) -> bool:
    return bool(
        chat.hora_ultimo_mensaje_entrante
        and (
            chat.hora_ultima_respuesta_vendedor is None
            or chat.hora_ultima_respuesta_vendedor < chat.hora_ultimo_mensaje_entrante
        )
    )


class ClientWaitingAlertService:
    def __init__(self, whatsapp: Optional[WhatsAppService] = None):
        self.whatsapp = whatsapp or WhatsAppService()

    async def process_due_alerts(self, db: Session) -> int:
        """Envía alertas vencidas. El bloqueo SQL evita duplicados entre workers."""
        now = datetime.now()
        due_chats = (
            db.query(Chats)
            .filter(Chats.status == 1, Chats.hora_ultimo_mensaje_entrante.isnot(None))
            # No se usa SKIP LOCKED para mantener compatibilidad con MySQL 5.7.
            # Un segundo worker espera el commit y después observa el nuevo estado.
            .with_for_update()
            .all()
        )
        pending_by_recipient: Dict[int, List[Tuple[Chats, str]]] = defaultdict(list)

        for chat in due_chats:
            if not _is_waiting(chat):
                continue
            alert_type = self._due_alert_type(chat, now)
            if alert_type is None:
                continue
            recipient_id = self._recipient_for(chat, alert_type, db)
            if recipient_id is None:
                logger.warning(
                    "Alerta de cliente esperando sin destinatario: chat_id=%s etapa=%s",
                    chat.id,
                    chat.etapa_escalamiento,
                )
                continue
            pending_by_recipient[recipient_id].append((chat, alert_type))

        sent = 0
        for recipient_id, entries in pending_by_recipient.items():
            phone_number = self._phone_for(recipient_id, db)
            if not phone_number:
                logger.warning("Usuario %s sin teléfono configurado para alertas", recipient_id)
                continue

            delivered_last_hour = (
                db.query(ClientWaitingAlertLog)
                .filter(
                    ClientWaitingAlertLog.recipient_user_id == recipient_id,
                    ClientWaitingAlertLog.alert_type.in_(("individual", "escalation")),
                    ClientWaitingAlertLog.created_at >= now - timedelta(hours=1),
                )
                .count()
            )
            available = max(settings.client_waiting_max_alerts_per_hour - delivered_last_hour, 0)
            individual, summarized = entries[:available], entries[available:]

            for chat, alert_type in individual:
                if await self._send_individual(db, chat, recipient_id, phone_number, alert_type, now):
                    sent += 1

            # Un único resumen por destinatario y corrida; los chats incluidos se
            # consideran alertados para respetar "una alerta por conversación".
            if summarized and await self._send_summary(
                db, recipient_id, phone_number, summarized, now
            ):
                sent += 1

        db.commit()
        return sent

    def _due_alert_type(self, chat: Chats, now: datetime) -> Optional[str]:
        if chat.etapa_escalamiento == 0:
            due_at = chat.hora_ultimo_mensaje_entrante + timedelta(
                minutes=settings.client_waiting_alert_minutes
            )
            return "individual" if now >= due_at else None
        if chat.etapa_escalamiento == 1 and chat.ultima_alerta_enviada:
            due_at = chat.ultima_alerta_enviada + timedelta(
                minutes=settings.client_waiting_escalation_minutes
            )
            return "escalation" if now >= due_at else None
        return None

    def _recipient_for(self, chat: Chats, alert_type: str, db: Session) -> Optional[int]:
        if alert_type == "individual":
            return chat.user_id
        seller = db.get(UserAlertSettings, chat.user_id)
        if seller and seller.status == 1 and seller.supervisor_user_id:
            return seller.supervisor_user_id
        logger.warning(
            "No se escala el chat %s: el vendedor %s no tiene responsable directo configurado",
            chat.id,
            chat.user_id,
        )
        return None

    @staticmethod
    def _phone_for(user_id: int, db: Session) -> Optional[str]:
        setting = db.get(UserAlertSettings, user_id)
        if setting and setting.status == 1:
            return setting.whatsapp_phone_number
        # Compatibilidad para instalaciones en que users.id coincide con el id VMAPS.
        user = db.get(Users, user_id)
        return user.phone_number if user and user.status == 1 else None

    async def _send_individual(
        self,
        db: Session,
        chat: Chats,
        recipient_id: int,
        phone_number: str,
        alert_type: str,
        now: datetime,
    ) -> bool:
        contact_name = self._contact_name(chat.id, db)
        elapsed_minutes = max(int((now - chat.hora_ultimo_mensaje_entrante).total_seconds() // 60), 1)
        url = f"{(settings.frontend_url or '').rstrip('/')}/quotation-integration/{chat.id}"
        try:
            await self.whatsapp.send_template_message(
                to=phone_number,
                template=ALERT_TEMPLATE,
                parameters=[
                    contact_name,
                    str(chat.quotation_id),
                    f"{elapsed_minutes} min",
                    url,
                ],
                language_code=settings.whatsapp_alert_template_language,
            )
        except Exception:
            logger.exception("No se pudo enviar alerta de cliente esperando para chat %s", chat.id)
            return False

        chat.ultima_alerta_enviada = now
        chat.etapa_escalamiento = 1 if alert_type == "individual" else 2
        db.add(ClientWaitingAlertLog(
            recipient_user_id=recipient_id, chat_id=chat.id, alert_type=alert_type
        ))
        return True

    async def _send_summary(
        self,
        db: Session,
        recipient_id: int,
        phone_number: str,
        entries: Iterable[Tuple[Chats, str]],
        now: datetime,
    ) -> bool:
        entries = list(entries)
        dashboard_url = f"{(settings.frontend_url or '').rstrip('/')}/chat"
        try:
            await self.whatsapp.send_template_message(
                to=phone_number,
                template=ALERT_TEMPLATE,
                parameters=[
                    f"Tienes {len(entries)} conversaciones pendientes",
                    "Varias cotizaciones",
                    "ahora",
                    dashboard_url,
                ],
                language_code=settings.whatsapp_alert_template_language,
            )
        except Exception:
            logger.exception("No se pudo enviar resumen de conversaciones pendientes")
            return False

        for chat, alert_type in entries:
            chat.ultima_alerta_enviada = now
            chat.etapa_escalamiento = 1 if alert_type == "individual" else 2
        db.add(ClientWaitingAlertLog(
            recipient_user_id=recipient_id, chat_id=None, alert_type="summary"
        ))
        return True

    @staticmethod
    def _contact_name(chat_id: int, db: Session) -> str:
        row = (
            db.query(Contact.display_name, Contact.name)
            .join(ChatMembers, ChatMembers.contact_id == Contact.id)
            .filter(ChatMembers.chat_id == chat_id, ChatMembers.status == 1)
            .first()
        )
        return (row[0] or row[1]) if row else "Cliente"
