from typing import List, Optional

from sqlalchemy.orm import Session

from app.models import Roles, Role_permission, Permissions


def get_all_roles(db: Session) -> List[Roles]:
    return db.query(Roles).order_by(Roles.created_at.desc()).all()


def get_all_permissions(db: Session) -> List[Permissions]:
    return db.query(Permissions).order_by(Permissions.created_at.desc()).all()


def create_role(
    db: Session,
    name: str,
    description: str,
) -> Roles:
    role = Roles(
        name=name,
        description=description
    )
    db.add(role)
    db.commit()
    db.refresh(role)
    return role


def add_role_permissions(
    db: Session,
    role_id: int,
    permission_ids: List[int],
) -> List[Role_permission]:
    role_permissions = [
        Role_permission(role_id=role_id, permission_id=permission_id)
        for permission_id in permission_ids
    ]
    db.add_all(role_permissions)
    db.commit()

    for role_permission in role_permissions:
        db.refresh(role_permission)

    return role_permissions


def get_role_permissions(db: Session, role_id: int) -> List[Role_permission]:
    return (
        db.query(Role_permission)
        .filter(Role_permission.role_id == role_id)
        .order_by(Role_permission.created_at.desc())
        .all()
    )


def delete_role_permission(db: Session, role_permission_id: int) -> bool:
    role_permission = db.query(Role_permission).filter(Role_permission.id == role_permission_id).first()
    if role_permission is None:
        return False

    db.delete(role_permission)
    db.commit()
    return True
    
