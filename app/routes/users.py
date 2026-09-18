from typing import Dict, Optional

from fastapi import APIRouter, Depends, Form
from sqlalchemy.orm import Session

from app.crud.users import create_user, delete_user, get_all_users_vmaps, update_user, get_all_users
from app.database import get_db, get_db_vmaps
from app.models import UserAlertSettings
from app.crud.users import clean_user_phone_number


router = APIRouter(prefix="/users", tags=["users"])


def validate_required_fields(fields: Dict[str, str]) -> Optional[str]:
    for field_name, value in fields.items():
        if not value or not value.strip():
            return f"El campo {field_name} es requerido"

    return None


def serialize_user(user) -> dict:
    return {
        "id": user.idusuario,
        "usuario": user.usuario,
        "name": user.nombres,
        "email": user.correo,
        "phone_number": '',
        "status": user.estado,
        "created_at": user.fecha_registro.isoformat() if user.fecha_registro else None,
    }


@router.get("/list")
async def get_all_users_route(db_vmaps: Session = Depends(get_db_vmaps)):
    users = get_all_users_vmaps(db_vmaps)
    return {
        "success": True,
        "data": [serialize_user(user) for user in users]
    }


@router.post("/create")
async def create_user_route(
    name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    phone_number: str = Form(...),
    db: Session = Depends(get_db),
):
    validation_error = validate_required_fields({
        "name": name,
        "email": email,
        "password": password,
        "phone_number": phone_number,
    })
    if validation_error:
        return {
            "success": False,
            "message": validation_error,
        }

    user = create_user(
        db,
        name=name.strip(),
        email=email.strip(),
        password=password.strip(),
        phone_number=phone_number.strip(),
    )

    return {
        "success": True,
        "message": "Usuario creado",
        "data": serialize_user(user),
    }


@router.put("/update/{user_id}")
async def update_user_route(
    user_id: int,
    name: Optional[str] = Form(None),
    email: Optional[str] = Form(None),
    phone_number: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    user = update_user(
        db,
        user_id=user_id,
        name=name,
        email=email,
        phone_number=phone_number,
    )

    if user is None:
        return {
            "success": False,
            "message": "Usuario no encontrado",
        }

    return {
        "success": True,
        "message": "Usuario actualizado",
        "data": serialize_user(user),
    }


@router.post("/delete/{user_id}")
async def delete_user_route(user_id: int, db: Session = Depends(get_db)):
    success = delete_user(db, user_id)
    if not success:
        return {
            "success": False,
            "message": "Usuario no encontrado",
        }

    return {
        "success": True,
        "message": "Usuario eliminado",
    }


@router.put("/{user_id}/alert-settings")
async def update_alert_settings_route(
    user_id: int,
    whatsapp_phone_number: str = Form(...),
    supervisor_user_id: Optional[int] = Form(None),
    db: Session = Depends(get_db),
):
    """Configura el teléfono y responsable usados solo por alertas backend."""
    phone_number = clean_user_phone_number(whatsapp_phone_number)
    if not phone_number:
        return {"success": False, "message": "whatsapp_phone_number es requerido"}

    setting = db.get(UserAlertSettings, user_id)
    if setting is None:
        setting = UserAlertSettings(user_id=user_id, whatsapp_phone_number=phone_number)
        db.add(setting)
    else:
        setting.whatsapp_phone_number = phone_number
        setting.status = 1
    setting.supervisor_user_id = supervisor_user_id
    db.commit()

    return {
        "success": True,
        "data": {
            "user_id": setting.user_id,
            "supervisor_user_id": setting.supervisor_user_id,
            "whatsapp_phone_number": setting.whatsapp_phone_number,
        },
    }
