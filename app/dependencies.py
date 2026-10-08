from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db_vmaps
from app.models import Usuarios
from app.utils.utils import validate_access_token


ALLOWED_USER_TYPES_FOR_USER_MANAGEMENT = {1, 17}


def validate_user_management_access(
    payload: dict = Depends(validate_access_token),
    db_vmaps: Session = Depends(get_db_vmaps),
) -> dict:
    try:
        user_id = int(payload["sub"])
    except (KeyError, TypeError, ValueError) as exc:
        raise HTTPException(status_code=403, detail="No tienes permisos para acceder a este recurso") from exc

    user = (
        db_vmaps.query(Usuarios)
        .filter(Usuarios.idusuario == user_id, Usuarios.estado == 1)
        .first()
    )
    if user is None or user.fk_idtipo not in ALLOWED_USER_TYPES_FOR_USER_MANAGEMENT:
        raise HTTPException(status_code=403, detail="No tienes permisos para acceder a este recurso")

    return payload
