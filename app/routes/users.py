from typing import Dict, Optional

from fastapi import APIRouter, Depends, Form
from sqlalchemy.orm import Session

from app.crud.users import create_user, delete_user, get_all_users_vmaps, update_user, get_all_users
from app.database import get_db, get_db_vmaps


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
