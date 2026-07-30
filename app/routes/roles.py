from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, Form
from sqlalchemy.orm import Session

from app.crud.roles import (
    add_role_permissions,
    create_role,
    delete_role_permission,
    get_all_roles,
    get_role_permissions,
    get_all_permissions,
)
from app.database import get_db
from app.models import Permissions


router = APIRouter(prefix="/roles", tags=["roles"])


def validate_required_fields(fields: Dict[str, str]) -> Optional[str]:
    for field_name, value in fields.items():
        if not value or not value.strip():
            return f"El campo {field_name} es requerido"

    return None


def serialize_role(role) -> dict:
    return {
        "id": role.id,
        "name": role.name,
        "description": role.description,
        "created_at": role.created_at.isoformat() if role.created_at else None,
    }


@router.get("/list")
async def get_all_roles_route(db: Session = Depends(get_db)):
    roles = get_all_roles(db)
    return {
        "success": True,
        "data": [serialize_role(role) for role in roles]
    }


@router.get("/permissions/list")
async def get_all_permissions_route(db: Session = Depends(get_db)):
    roles = get_all_permissions(db)
    return {
        "success": True,
        "data": [serialize_role(role) for role in roles]
    }


@router.post("/create")
async def create_role_route(
    name: str = Form(...),
    description: str = Form(...),
    db: Session = Depends(get_db),
):
    validation_error = validate_required_fields({
        "name": name,
        "description": description,
    })
    if validation_error:
        return {
            "success": False,
            "message": validation_error,
        }

    role = create_role(
        db,
        name=name.strip(),
        description=description.strip(),
    )

    return {
        "success": True,
        "message": "Role Creado",
        "data": serialize_role(role),
    }


@router.post("/permissions/create")
async def create_role_permissions_route(
    role_id: int = Form(...),
    permission_ids: Optional[List[int]] = Form(None),
    permission_id: Optional[int] = Form(None),
    db: Session = Depends(get_db),
):
    requested_permission_ids = permission_ids or []
    if permission_id is not None:
        requested_permission_ids.append(permission_id)

    if not requested_permission_ids:
        return {
            "success": False,
            "message": "Debes enviar al menos un permission_id",
        }

    role_permissions = add_role_permissions(
        db,
        role_id=role_id,
        permission_ids=requested_permission_ids,
    )

    return {
        "success": True,
        "message": "Permisos asignados al rol",
        "data": [
            {
                "id": role_permission.id,
                "role_id": role_permission.role_id,
                "permission_id": role_permission.permission_id,
                "created_at": (
                    role_permission.created_at.isoformat()
                    if role_permission.created_at
                    else None
                ),
            }
            for role_permission in role_permissions
        ],
    }


@router.get("/{role_id}/permissions")
async def get_role_permissions_route(
    role_id: int,
    db: Session = Depends(get_db),
):
    role_permissions = get_role_permissions(db, role_id)
    permissions_by_id = {
        permission.id: permission
        for permission in (
            db.query(Permissions)
            .filter(Permissions.id.in_([item.permission_id for item in role_permissions]))
            .all()
        )
    }

    return {
        "success": True,
        "data": [
            {
                "id": role_permission.id,
                "role_id": role_permission.role_id,
                "permission_id": role_permission.permission_id,
                "name": permissions_by_id[role_permission.permission_id].name,
                "description": permissions_by_id[role_permission.permission_id].description,
                "created_at": (
                    role_permission.created_at.isoformat()
                    if role_permission.created_at
                    else None
                ),
            }
            for role_permission in role_permissions
        ],
    }


@router.delete("/permissions/{role_permission_id}")
async def delete_role_permission_route(
    role_permission_id: int,
    db: Session = Depends(get_db),
):
    deleted = delete_role_permission(db, role_permission_id)
    if not deleted:
        return {
            "success": False,
            "message": "Registro de permiso no encontrado",
        }

    return {
        "success": True,
        "message": "Permiso eliminado del rol",
    }
