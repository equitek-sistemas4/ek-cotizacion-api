import httpx
import logging
from typing import List, Optional

from pydantic import BaseModel

from app.config import settings

logger = logging.getLogger(__name__)


class WhatsAppService:
    def __init__(self):
        self.base_url = (
            f"https://graph.facebook.com/{settings.whatsapp_api_version}/"
            f"{settings.whatsapp_phone_number_id}"
        )


    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {settings.whatsapp_access_token}",
            "Content-Type": "application/json",
        }


    def _auth_headers(self) -> dict:
        return {
            "Authorization": f"Bearer {settings.whatsapp_access_token}",
        }


    #Funcion para enviar mensajes de texto simple a traves de la API
    async def send_text_message(self, to: str, text: str) -> dict:
        if not settings.whatsapp_phone_number_id:
            raise RuntimeError("WHATSAPP_PHONE_NUMBER_ID no está configurado")
        if not settings.whatsapp_access_token:
            raise RuntimeError("WHATSAPP_ACCESS_TOKEN no está configurado")

        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "text",
            "text": {"body": text},
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.base_url}/messages",
                headers=self._headers(),
                json=payload,
            )
        
        response_data = response.json()

        if response.status_code >= 400:
            error_detail = response_data if isinstance(response_data, dict) else response.text
            logger.error(f"Error al enviar mensaje: {error_detail}")
            raise RuntimeError(f"Error al enviar mensaje de WhatsApp: {error_detail}")

        if "error" in response_data:
            logger.error(f"Error en respuesta: {response_data['error']}")
            raise RuntimeError(f"Error al enviar mensaje de WhatsApp: {response_data['error']}")

        return response_data
    

    #Funcion para enviar mensajes usando plantillas aprobadas en Meta
    async def send_template_message(
        self,
        to: str,
        template: str,
        parameters: list = None,
        language_code: str = "en_US",
        components: list = None,
    ) -> dict:
        if not settings.whatsapp_phone_number_id:
            raise RuntimeError("WHATSAPP_PHONE_NUMBER_ID no está configurado")
        if not settings.whatsapp_access_token:
            raise RuntimeError("WHATSAPP_ACCESS_TOKEN no está configurado")

        phone_number = to.replace("+", "") if to.startswith("+") else to

        template_components = []
        if components:
            for component in components:
                if isinstance(component, BaseModel):
                    if hasattr(component, "model_dump"):
                        template_components.append(component.model_dump(exclude_none=True))
                    else:
                        template_components.append(component.dict(exclude_none=True))
                elif isinstance(component, dict):
                    template_components.append({
                        key: value
                        for key, value in component.items()
                        if value is not None
                    })

        if parameters:
            body_parameters = []
            for param in parameters:
                if isinstance(param, BaseModel):
                    if hasattr(param, "model_dump"):
                        body_parameters.append(param.model_dump())
                    else:
                        body_parameters.append(param.dict())
                elif isinstance(param, dict):
                    body_parameters.append(param)
                else:
                    body_parameters.append({"type": "text", "text": str(param)})

            template_components.append({
                "type": "body",
                "parameters": body_parameters
            })

        payload = {
            "messaging_product": "whatsapp",
            "to": phone_number,
            "type": "template",
            "template": {
                "name": template,
                "language": {
                    "code": language_code
                }
            }
        }
        
        if template_components:
            payload["template"]["components"] = template_components

        logger.info(f"Enviando plantilla '{template}' a {phone_number}")
        logger.debug(f"Payload: {payload}")

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.base_url}/messages",
                headers=self._headers(),
                json=payload,
            )

        logger.info(f"Respuesta status: {response.status_code}")
        
        response_data = response.json()
        logger.info(f"Respuesta JSON: {response_data}")

        if response.status_code >= 400:
            error_detail = response_data if isinstance(response_data, dict) else response.text
            logger.error(f"Error al enviar plantilla: {error_detail}")
            raise RuntimeError(f"Error al enviar plantilla de WhatsApp: {error_detail}")

        if "error" in response_data:
            logger.error(f"Error en respuesta: {response_data['error']}")
            raise RuntimeError(f"Error al enviar plantilla de WhatsApp: {response_data['error']}")

        return response_data


    async def upload_media(
        self,
        file_bytes: bytes,
        filename: str,
        content_type: str,
    ) -> dict:
        if not settings.whatsapp_phone_number_id:
            raise RuntimeError("WHATSAPP_PHONE_NUMBER_ID no estÃ¡ configurado")
        if not settings.whatsapp_access_token:
            raise RuntimeError("WHATSAPP_ACCESS_TOKEN no estÃ¡ configurado")

        data = {
            "messaging_product": "whatsapp",
            "type": content_type,
        }
        files = {
            "file": (filename, file_bytes, content_type),
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.base_url}/media",
                headers=self._auth_headers(),
                data=data,
                files=files,
            )

        response_data = response.json()

        if response.status_code >= 400:
            error_detail = response_data if isinstance(response_data, dict) else response.text
            logger.error(f"Error al subir archivo: {error_detail}")
            raise RuntimeError(f"Error al subir archivo a WhatsApp: {error_detail}")

        if "error" in response_data:
            logger.error(f"Error en respuesta: {response_data['error']}")
            raise RuntimeError(f"Error al subir archivo a WhatsApp: {response_data['error']}")

        return response_data


    async def send_media_message(
        self,
        to: str,
        media_type: str,
        media_id: str,
        caption: Optional[str] = None,
        filename: Optional[str] = None,
    ) -> dict:
        if not settings.whatsapp_phone_number_id:
            raise RuntimeError("WHATSAPP_PHONE_NUMBER_ID no estÃ¡ configurado")
        if not settings.whatsapp_access_token:
            raise RuntimeError("WHATSAPP_ACCESS_TOKEN no estÃ¡ configurado")

        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": media_type,
            media_type: {
                "id": media_id,
            },
        }

        if media_type in {"document", "image", "video"} and caption:
            payload[media_type]["caption"] = caption
        if media_type == "document" and filename:
            payload[media_type]["filename"] = filename

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.base_url}/messages",
                headers=self._headers(),
                json=payload,
            )

        response_data = response.json()

        if response.status_code >= 400:
            error_detail = response_data if isinstance(response_data, dict) else response.text
            logger.error(f"Error al enviar archivo: {error_detail}")
            raise RuntimeError(f"Error al enviar archivo de WhatsApp: {error_detail}")

        if "error" in response_data:
            logger.error(f"Error en respuesta: {response_data['error']}")
            raise RuntimeError(f"Error al enviar archivo de WhatsApp: {response_data['error']}")

        return response_data


    async def create_group(
        self,
        subject: str,
        description: Optional[str] = None,
        join_approval_mode: Optional[str] = None,
    ) -> dict:
        if not settings.whatsapp_phone_number_id:
            raise RuntimeError("WHATSAPP_PHONE_NUMBER_ID no estÃ¡ configurado")
        if not settings.whatsapp_access_token:
            raise RuntimeError("WHATSAPP_ACCESS_TOKEN no estÃ¡ configurado")

        payload = {
            "messaging_product": "whatsapp",
            "subject": subject,
        }

        if description:
            payload["description"] = description
        if join_approval_mode:
            payload["join_approval_mode"] = join_approval_mode

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.base_url}/groups",
                headers=self._headers(),
                json=payload,
            )

        response_data = response.json()

        if response.status_code >= 400:
            error_detail = response_data if isinstance(response_data, dict) else response.text
            logger.error(f"Error al crear grupo de WhatsApp: {error_detail}")
            raise RuntimeError(f"Error al crear grupo de WhatsApp: {error_detail}")

        if "error" in response_data:
            logger.error(f"Error en respuesta: {response_data['error']}")
            raise RuntimeError(f"Error al crear grupo de WhatsApp: {response_data['error']}")

        return response_data


    async def add_group_participants(
        self,
        group_id: str,
        participants: List[str],
    ) -> dict:
        if not settings.whatsapp_access_token:
            raise RuntimeError("WHATSAPP_ACCESS_TOKEN no estÃ¡ configurado")

        payload = {
            "messaging_product": "whatsapp",
            "participants": [
                {"user": participant.replace("+", "").strip()}
                for participant in participants
            ],
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"https://graph.facebook.com/{settings.whatsapp_api_version}/{group_id}/participants",
                headers=self._headers(),
                json=payload,
            )

        response_data = response.json()

        if response.status_code >= 400:
            error_detail = response_data if isinstance(response_data, dict) else response.text
            logger.error(f"Error al agregar participantes al grupo de WhatsApp: {error_detail}")
            raise RuntimeError(f"Error al agregar participantes al grupo de WhatsApp: {error_detail}")

        if "error" in response_data:
            logger.error(f"Error en respuesta: {response_data['error']}")
            raise RuntimeError(f"Error al agregar participantes al grupo de WhatsApp: {response_data['error']}")

        return response_data


    async def get_active_groups(
        self,
        limit: Optional[int] = None,
        after: Optional[str] = None,
        before: Optional[str] = None,
    ) -> dict:
        if not settings.whatsapp_phone_number_id:
            raise RuntimeError("WHATSAPP_PHONE_NUMBER_ID no estÃ¡ configurado")
        if not settings.whatsapp_access_token:
            raise RuntimeError("WHATSAPP_ACCESS_TOKEN no estÃ¡ configurado")

        params = {}
        if limit is not None:
            params["limit"] = limit
        if after:
            params["after"] = after
        if before:
            params["before"] = before

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{self.base_url}/groups",
                headers=self._headers(),
                params=params,
            )

        response_data = response.json()

        if response.status_code >= 400:
            error_detail = response_data if isinstance(response_data, dict) else response.text
            logger.error(f"Error al obtener grupos activos de WhatsApp: {error_detail}")
            raise RuntimeError(f"Error al obtener grupos activos de WhatsApp: {error_detail}")

        if "error" in response_data:
            logger.error(f"Error en respuesta: {response_data['error']}")
            raise RuntimeError(f"Error al obtener grupos activos de WhatsApp: {response_data['error']}")

        return response_data
    
    
    # Funcion para verificar el webhook
    def verify_webhook(self, mode: str, token: str, challenge: str) -> str:
        if mode == "subscribe" and token == settings.whatsapp_verify_token:
            return challenge
        raise RuntimeError("Token de verificación inválido")


    # Funcion para procesar los eventos recibidos en el webhook
    def process_webhook(self, payload: dict) -> dict:
        return {
            "status": "received",
            "entries": len(payload.get("entry", [])),
        }
