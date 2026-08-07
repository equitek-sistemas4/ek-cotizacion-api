from datetime import timedelta

from fastapi import APIRouter, Depends, Form
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.crud.chats import get_chat_by_id
from app.crud.chats_members import get_chat_member, update_token_member_chat
from app.crud.contacts import get_contact_by_id
from app.crud.users import get_user_by_email, get_user_by_username_vmaps, validate_user_password_vmaps
from app.database import get_db, get_db_vmaps
from app.utils.utils import create_access_token, validate_access_token


router = APIRouter(prefix="/auth", tags=["auth"])


def serialize_vmaps_user(user) -> dict:
    return {
        "id": user.idusuario,
        "username": user.usuario,
        "name": " ".join(
            part for part in (user.nombres, user.apellido_paterno, user.apellido_materno) if part
        ),
        "email": user.correo,
        "status": user.estado,
    }


@router.post("/login")
async def login_route(
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db_vmaps),
):
    try:
        user = get_user_by_username_vmaps(db, username=email.strip())
        if user is None:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "message": "El usuario no existe",
                },
            )

        if not validate_user_password_vmaps(user, password.strip()):
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "message": "Contraseña incorrecta",
                },
            )

        access_token = create_access_token({
            "sub": str(user.idusuario),
            "email": user.correo,
        })

        return {
            "success": True,
            "message": "Login correcto",
            "data": {
                "user": serialize_vmaps_user(user),
                "access_token": access_token,
                "token_type": "bearer",
            },
        }
    except Exception as error:
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "message": str(error),
            },
        )


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
