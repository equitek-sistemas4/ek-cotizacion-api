from typing import Dict, List, Optional, Tuple

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from app.crud.chats import get_chat_by_id
from app.crud.chats_messages import create_chat_message
from app.crud.contacts import get_contact_by_id
from app.crud.users import get_user_by_id
from app.database import SessionLocal, SessionLocal_vmaps
from app.schemas.chat_messages import serialize_chat_message
from app.utils.utils import decode_access_token, normalize_phone_number


router = APIRouter(prefix="/chats", tags=["chat_websocket"])


class ChatConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, List[WebSocket]] = {}

    async def connect(self, chat_id: int, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.setdefault(chat_id, []).append(websocket)

    def disconnect(self, chat_id: int, websocket: WebSocket):
        connections = self.active_connections.get(chat_id, [])
        if websocket in connections:
            connections.remove(websocket)

        if not connections and chat_id in self.active_connections:
            del self.active_connections[chat_id]

    async def broadcast(self, chat_id: int, payload: dict):
        disconnected = []
        for connection in self.active_connections.get(chat_id, []):
            try:
                await connection.send_json(payload)
            except RuntimeError:
                disconnected.append(connection)

        for connection in disconnected:
            self.disconnect(chat_id, connection)


manager = ChatConnectionManager()


class WhatsAppConnectionManager:
    def __init__(self):
        self.active_connections: List[Tuple[WebSocket, Optional[str]]] = []

    async def connect(
        self,
        websocket: WebSocket,
        phone_number: Optional[str] = None,
    ):
        await websocket.accept()
        self.active_connections.append((websocket, phone_number))

    def disconnect(self, websocket: WebSocket):
        self.active_connections = [
            connection
            for connection in self.active_connections
            if connection[0] is not websocket
        ]

    async def broadcast_message(self, message: dict):
        disconnected = []
        for connection, phone_number in self.active_connections:
            if phone_number and phone_number != message["phone_number"]:
                continue

            try:
                await connection.send_json({
                    "type": "whatsapp_message",
                    "data": message,
                })
            except RuntimeError:
                disconnected.append(connection)

        for connection in disconnected:
            self.disconnect(connection)


whatsapp_manager = WhatsAppConnectionManager()


@router.websocket("/whatsapp/ws")
async def whatsapp_messages_websocket(
    websocket: WebSocket,
    token: Optional[str] = None,
    phone_number: Optional[str] = None,
):
    if not token:
        await websocket.close(code=1008, reason="Token requerido")
        return

    try:
        decode_access_token(token)
    except HTTPException as exc:
        await websocket.close(code=1008, reason=str(exc.detail))
        return
    except Exception:
        await websocket.close(code=1008, reason="Token invalido")
        return

    normalized_phone_number = (
        normalize_phone_number(phone_number) if phone_number else None
    )

    await whatsapp_manager.connect(websocket, normalized_phone_number)
    await websocket.send_json({
        "type": "connected",
        "data": {"phone_number": normalized_phone_number},
    })

    try:
        while True:
            await websocket.receive()
    except WebSocketDisconnect:
        whatsapp_manager.disconnect(websocket)
    except Exception:
        whatsapp_manager.disconnect(websocket)
        await websocket.close(code=1011, reason="Error interno")


def get_sender_from_token(payload: dict, chat_id: int) -> Tuple[int, str]:
    if payload.get("token_use") == "chat_contact":
        token_chat_id = int(payload.get("chat_id", 0))
        if token_chat_id != chat_id:
            raise HTTPException(status_code=403, detail="Token no pertenece a este chat")

        return int(payload["contact_id"]), "contact"

    return int(payload["sub"]), "user"


def get_sender(db: Session, db_vmaps: Session, sender_id: int, sender_type: str):
    if sender_type == "contact":
        return get_contact_by_id(db, sender_id), None

    return None, get_user_by_id(db_vmaps, sender_id)


@router.websocket("/{chat_id}/ws")
async def chat_websocket(websocket: WebSocket, chat_id: int, token: Optional[str] = None):
    if not token:
        await websocket.close(code=1008, reason="Token requerido")
        return

    try:
        payload = decode_access_token(token)
        sender_id, sender_type = get_sender_from_token(payload, chat_id)
    except HTTPException as exc:
        await websocket.close(code=1008, reason=str(exc.detail))
        return
    except Exception:
        await websocket.close(code=1008, reason="Token invalido")
        return

    db = SessionLocal()
    db_vmaps = SessionLocal_vmaps()
    try:
        chat = get_chat_by_id(db, chat_id)
        if chat is None:
            await websocket.close(code=1008, reason="Chat no encontrado")
            return

        contact, user = get_sender(db, db_vmaps, sender_id, sender_type)
        if sender_type == "contact" and contact is None:
            await websocket.close(code=1008, reason="Contacto no encontrado")
            return
        if sender_type == "user" and user is None:
            await websocket.close(code=1008, reason="Usuario no encontrado")
            return

        await manager.connect(chat_id, websocket)
        await websocket.send_json({
            "type": "connected",
            "data": {
                "chat_id": chat_id,
                "sender_id": sender_id,
                "sender_type": sender_type,
            },
        })

        while True:
            try:
                data = await websocket.receive_json()
            except ValueError:
                await websocket.send_json({
                    "type": "error",
                    "message": "El mensaje debe ser JSON valido",
                })
                continue

            text = str(data.get("text", "")).strip()
            if not text:
                await websocket.send_json({
                    "type": "error",
                    "message": "El campo text es requerido",
                })
                continue

            message = create_chat_message(
                db,
                chat_id=chat_id,
                sender_id=sender_id,
                sender_type=sender_type,
                text=text,
            )
            db.refresh(message)
            serialized_message = serialize_chat_message(message, contact, user)

            await manager.broadcast(chat_id, {
                "type": "message",
                "data": serialized_message,
            })
    except WebSocketDisconnect:
        manager.disconnect(chat_id, websocket)
    except Exception:
        manager.disconnect(chat_id, websocket)
        await websocket.close(code=1011, reason="Error interno")
    finally:
        db.close()
        db_vmaps.close()
