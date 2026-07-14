from datetime import timedelta

from fastapi import APIRouter, Depends, Form
from sqlalchemy.orm import Session

from app.crud.chats import get_chat_by_id
from app.crud.chats_members import get_chat_member, update_token_member_chat
from app.crud.contacts import get_contact_by_id
from app.crud.users import get_user_by_email, validate_user_password
from app.database import get_db
from app.routes.users import serialize_user
from app.utils.utils import create_access_token, validate_access_token


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login")
async def login_route(
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    user = get_user_by_email(db, email=email.strip())
    if user is None:
        return {
            "success": False,
            "message": "El email no existe",
        }

    if not validate_user_password(user, password.strip()):
        return {
            "success": False,
            "message": "Password incorrecto",
        }

    access_token = create_access_token({
        "sub": str(user.id),
        "email": user.email,
    })

    return {
        "success": True,
        "message": "Login correcto",
        "data": {
            "user": serialize_user(user),
            "access_token": access_token,
            "token_type": "bearer",
        },
    }


@router.post("/logout")
async def logout_route(_payload: dict = Depends(validate_access_token)):
    return {
        "success": True,
        "message": "Sesion cerrada",
    }


@router.post("/chat-contact-token")
async def create_chat_contact_token_route(
    chat_id: int = Form(...),
    contact_id: int = Form(...),
    db: Session = Depends(get_db),
    _payload: dict = Depends(validate_access_token),
):
    chat = get_chat_by_id(db, chat_id)
    if chat is None:
        return {
            "success": False,
            "message": "Chat no encontrado",
        }

    contact = get_contact_by_id(db, contact_id)
    if contact is None:
        return {
            "success": False,
            "message": "Contacto no encontrado",
        }

    member = get_chat_member(db, chat_id, contact_id)
    if member is None:
        return {
            "success": False,
            "message": "El contacto no pertenece al chat",
        }

    access_token = create_access_token({
        "sub": f"chat:{chat.id}:contact:{contact_id}",
        "chat_id": chat.id,
        "contact_id": contact_id,
        "token_use": "chat_contact",
    }, expires_delta=timedelta(days=180))

    chat_member = update_token_member_chat(db, chat.id, contact_id, access_token)
    if chat_member is None:
        return {
            "success": False,
            "message": "No se pudo actualizar el token del miembro",
        }

    return {
        "success": True,
        "message": "Token generado",
        "data": {
            "access_token": access_token,
            "token_type": "bearer",
            "chat_id": chat_id,
            "contact_id": contact_id,
        },
    }
