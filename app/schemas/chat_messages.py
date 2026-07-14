from typing import List, Optional, Tuple

from app.models import ChatMessages, Contact, Users


def serialize_sender(
    message: ChatMessages,
    contact: Optional[Contact] = None,
    user: Optional[Users] = None,
) -> Optional[dict]:
    if message.sender_type == "contact" and contact:
        return {
            "id": contact.id,
            "type": "contact",
            "display_name": contact.display_name,
        }

    if message.sender_type == "user" and user:
        return {
            "id": user.id,
            "type": "user",
            "display_name": user.name,
        }

    return None


def serialize_chat_message(
    message: ChatMessages,
    contact: Optional[Contact] = None,
    user: Optional[Users] = None,
) -> dict:
    return {
        "message": {
            "id": message.id,
            "chat_id": message.chat_id,
            "sender_id": message.sender_id,
            "sender_type": message.sender_type,
            "text": message.text,
            "files": [
                {
                    "id": file.id,
                    "name": file.file_name,
                    "path": file.file_path,
                }
                for file in message.files
            ],
            "created_at": message.created_at.isoformat() if message.created_at else None,
        },
        "sender": serialize_sender(message, contact, user),
    }


def serialize_chat_messages(
    messages: List[Tuple[ChatMessages, Optional[Contact], Optional[Users]]],
) -> dict:
    return {
        "data": [
            serialize_chat_message(message, contact, user)
            for message, contact, user in messages
        ],
    }
