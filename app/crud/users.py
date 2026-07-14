from typing import List, Optional

from sqlalchemy.orm import Session

from app.models import Users
from app.utils.utils import hash_password


def clean_user_phone_number(phone_number: str) -> str:
    return phone_number.replace("+", "").strip()


def get_all_users(db: Session) -> List[Users]:
    return db.query(Users).order_by(Users.created_at.desc()).all()


def create_user(
    db: Session,
    name: str,
    email: str,
    password: str,
    phone_number: str,
) -> Users:
    user = Users(
        name=name,
        email=email,
        password=hash_password(password),
        phone_number=clean_user_phone_number(phone_number),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_user_by_email_and_password(
    db: Session,
    email: str,
    password: str,
) -> Optional[Users]:
    return (
        db.query(Users)
        .filter(
            Users.email == email,
            Users.password == hash_password(password),
        )
        .first()
    )


def get_user_by_email(db: Session, email: str) -> Optional[Users]:
    return db.query(Users).filter(Users.email == email).first()


def validate_user_password(user: Users, password: str) -> bool:
    return user.password == hash_password(password)


def get_user_by_id(db: Session, user_id: int) -> Optional[Users]:
    return db.query(Users).filter(Users.id == user_id).first()


def update_user(
    db: Session,
    user_id: int,
    name: Optional[str] = None,
    email: Optional[str] = None,
    password: Optional[str] = None,
    phone_number: Optional[str] = None,
) -> Optional[Users]:
    user = db.query(Users).filter(Users.id == user_id).first()
    if user is None:
        return None

    if name is not None:
        user.name = name
    if email is not None:
        user.email = email
    if password is not None:
        user.password = hash_password(password)
    if phone_number is not None:
        user.phone_number = clean_user_phone_number(phone_number)

    db.commit()
    db.refresh(user)
    return user


def delete_user(db: Session, user_id: int) -> bool:
    user = db.query(Users).filter(Users.id == user_id).first()
    if user is None:
        return False

    db.delete(user)
    db.commit()
    return True
