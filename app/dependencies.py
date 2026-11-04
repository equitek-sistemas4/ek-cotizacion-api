from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db_quote
from app.models import usuarios
from app.utils.utils import validate_access_token


ALLOWED_USER_TYPES_FOR_USER_MANAGEMENT = {1, 17}


def validate_user_management_access(
    payload: dict = Depends(validate_access_token),
    db_quote: Session = Depends(get_db_quote),
) -> dict:
    try:
        user_id = int(payload["sub"])
    except (KeyError, TypeError, ValueError) as exc:
        raise HTTPException(status_code=403, detail="No tienes permisos para acceder a este recurso") from exc

    user = (
        db_quote.query(usuarios)
        .filter(usuarios.idusuario == user_id, usuarios.estado == 1)
        .first()
    )
    if user is None or user.fk_idtipo not in ALLOWED_USER_TYPES_FOR_USER_MANAGEMENT:
        raise HTTPException(status_code=403, detail="No tienes permisos para acceder a este recurso")

    return payload
