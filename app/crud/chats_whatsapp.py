from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from app.models import Chats_Whatsapp, Contact, Usuarios


def create_chat_whatsapp(
    db: Session,
    user_id: int,
    contact_id: Optional[int] = None,
) -> Chats_Whatsapp:
    chat_whatsapp = Chats_Whatsapp(
        user_id=user_id,
        contact_id=contact_id,
    )
    db.add(chat_whatsapp)
    db.commit()
    db.refresh(chat_whatsapp)
    return chat_whatsapp


def get_chat_whatsapp_by_id(
    db: Session,
    chat_whatsapp_id: int,
) -> Optional[Chats_Whatsapp]:
    return (
        db.query(Chats_Whatsapp)
        .filter(Chats_Whatsapp.id == chat_whatsapp_id)
        .first()
    )


def get_all_chats_whatsapp(db: Session, db_vmaps: Session, user_id: Optional[int] = None) -> List[Dict]:
    rows = (
        db.query(Chats_Whatsapp, Contact)
        .outerjoin(Contact, Chats_Whatsapp.contact_id == Contact.id)
        .filter(Chats_Whatsapp.status == 1, Chats_Whatsapp.user_id == user_id) if user_id is not None else db.query(Chats_Whatsapp, Contact).outerjoin(Contact, Chats_Whatsapp.contact_id == Contact.id).filter(Chats_Whatsapp.status == 1)
        .order_by(Chats_Whatsapp.created_at.desc())
        .all()
    )

    user_ids = {chat.user_id for chat, _contact in rows}
    users_by_id = {
        user.idusuario: user
        for user in (
            db_vmaps.query(Usuarios)
            .filter(Usuarios.idusuario.in_(user_ids))
            .all()
        )
    } if user_ids else {}

    return [
        {
            "id": chat.id,
            "user_id": chat.user_id,
            "contact_id": chat.contact_id,
            "status": chat.status,
            "created_at": chat.created_at.isoformat() if chat.created_at else None,
            "user": {
                "id": user.idusuario,
                "username": user.usuario,
                "name": user.nombres,
                "last_name": user.apellido_paterno,
                "second_last_name": user.apellido_materno,
                "email": user.correo,
                "status": user.estado,
                "created_at": (
                    user.fecha_registro.isoformat() if user.fecha_registro else None
                ),
            }
            if user
            else None,
            "contact": {
                "id": contact.id,
                "name": contact.name,
                "display_name": contact.display_name,
                "phone_number": contact.phone_number,
                "company": contact.company,
                "position": contact.position,
                "status": contact.status,
                "created_at": (
                    contact.created_at.isoformat() if contact.created_at else None
                ),
            }
            if contact
            else None,
        }
        for chat, contact in rows
        for user in [users_by_id.get(chat.user_id)]
    ]


def update_chat_whatsapp(
    db: Session,
    chat_whatsapp_id: int,
    user_id: Optional[int] = None,
    contact_id: Optional[int] = None,
    status: Optional[int] = None,
) -> Optional[Chats_Whatsapp]:
    chat_whatsapp = get_chat_whatsapp_by_id(db, chat_whatsapp_id)
    if chat_whatsapp is None:
        return None

    if user_id is not None:
        chat_whatsapp.user_id = user_id
    if contact_id is not None:
        chat_whatsapp.contact_id = contact_id
    if status is not None:
        chat_whatsapp.status = status

    db.commit()
    db.refresh(chat_whatsapp)
    return chat_whatsapp


def delete_chat_whatsapp(db: Session, chat_whatsapp_id: int) -> bool:
    chat_whatsapp = get_chat_whatsapp_by_id(db, chat_whatsapp_id)
    if chat_whatsapp is None:
        return False

    chat_whatsapp.status = 0
    db.commit()
    db.refresh(chat_whatsapp)
    return True
