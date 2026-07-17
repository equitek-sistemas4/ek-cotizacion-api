from datetime import timedelta

from app.crud.chats_members import get_chat_member_by_code
from app.database import get_db
from app.utils.utils import decrypt_token
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session


router = APIRouter(prefix="/chat_members", tags=["chat_members"])


@router.get("/by-code/{access_code}")
async def get_chat_member_by_access_code_route(
    access_code: str,
    db: Session = Depends(get_db),
):
    chat_member = get_chat_member_by_code(db, access_code)
    if chat_member is None:
        raise HTTPException(status_code=404, detail="Chat member not found")
    return {
        "success": True,
        "data": {
            "id": chat_member.id,
            "chat_id": chat_member.chat_id,
            "contact_id": chat_member.contact_id,
            "token": decrypt_token(chat_member.token),
            "created_at": chat_member.created_at.isoformat() if chat_member.created_at else None,
        }
    }
