from typing import Optional

import httpx
from fastapi import APIRouter, Form, HTTPException, status

from app.config import settings


router = APIRouter(prefix="/emails", tags=["emails"])


def _resend_error_detail(response: httpx.Response) -> str:
    try:
        payload = response.json()
    except ValueError:
        return "Resend no pudo procesar el correo."

    return payload.get("message") or payload.get("name") or "Resend no pudo procesar el correo."


@router.post("/send", status_code=status.HTTP_200_OK)
async def send_email(
    to: str = Form(..., min_length=3),
    subject: str = Form(..., min_length=1),
    html: Optional[str] = Form(None),
    text: Optional[str] = Form(None),
    reply_to: Optional[str] = Form(None),
):
    if not settings.resend_api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="RESEND_API_KEY no está configurada.",
        )

    if not settings.resend_from_email:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="RESEND_FROM_EMAIL no está configurada.",
        )

    if not html and not text:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Debes enviar al menos uno de los campos: html o text.",
        )

    payload = {
        "from": settings.resend_from_email,
        "to": [to],
        "subject": subject,
    }
    if html:
        payload["html"] = html
    if text:
        payload["text"] = text
    if reply_to:
        payload["reply_to"] = reply_to

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                "https://api.resend.com/emails",
                headers={
                    "Authorization": "Bearer {0}".format(settings.resend_api_key),
                    "Content-Type": "application/json",
                },
                json=payload,
            )
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No fue posible conectar con Resend.",
        ) from exc

    if response.is_error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=_resend_error_detail(response),
        )

    return {
        "success": True,
        "message": "Correo enviado",
        "data": response.json(),
    }
