import base64
import hashlib
import hmac
import json
import os
import secrets
import string
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Header, HTTPException

from app.config import settings
from app.models import Messages


def generate_alphanumeric_code(length: int = 12) -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def base64_url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("utf-8")


def base64_url_decode(data: str) -> bytes:
    padded_data = data + "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(padded_data.encode("utf-8"))


def hash_password(password: str) -> str:
    if not settings.secret_key:
        raise ValueError("SECRET_KEY no esta configurada")

    return hmac.new(
        settings.secret_key.encode("utf-8"),
        password.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def get_token_encryption_key() -> bytes:
    if not settings.secret_key:
        raise ValueError("SECRET_KEY no esta configurada")

    return hmac.new(
        settings.secret_key.encode("utf-8"),
        b"chat-member-token",
        hashlib.sha256,
    ).digest()


def build_token_keystream(key: bytes, nonce: bytes, length: int) -> bytes:
    stream = b""
    counter = 0
    while len(stream) < length:
        stream += hmac.new(
            key,
            nonce + counter.to_bytes(4, "big"),
            hashlib.sha256,
        ).digest()
        counter += 1
    return stream[:length]


def encrypt_token(token: str) -> str:
    key = get_token_encryption_key()
    nonce = os.urandom(16)
    token_bytes = token.encode("utf-8")
    keystream = build_token_keystream(key, nonce, len(token_bytes))
    encrypted = bytes(
        token_byte ^ key_byte
        for token_byte, key_byte in zip(token_bytes, keystream)
    )
    signature = hmac.new(key, nonce + encrypted, hashlib.sha256).digest()[:16]

    return f"enc:v1:{base64_url_encode(nonce + signature + encrypted)}"


def decrypt_token(token: Optional[str]) -> Optional[str]:
    if token is None or not token.startswith("enc:v1:"):
        return token

    key = get_token_encryption_key()
    encrypted_data = base64_url_decode(token[len("enc:v1:"):])
    if len(encrypted_data) < 32:
        return token

    nonce = encrypted_data[:16]
    signature = encrypted_data[16:32]
    encrypted = encrypted_data[32:]
    expected_signature = hmac.new(key, nonce + encrypted, hashlib.sha256).digest()[:16]
    if not hmac.compare_digest(signature, expected_signature):
        return token

    keystream = build_token_keystream(key, nonce, len(encrypted))
    decrypted = bytes(
        encrypted_byte ^ key_byte
        for encrypted_byte, key_byte in zip(encrypted, keystream)
    )
    return decrypted.decode("utf-8")


def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None,
) -> str:
    if not settings.secret_key:
        raise ValueError("SECRET_KEY no esta configurada")

    now = datetime.now(timezone.utc)
    expires_at = now + (
        expires_delta
        if expires_delta is not None
        else timedelta(minutes=settings.access_token_expire_minutes)
    )
    header = {
        "alg": "HS256",
        "typ": "JWT",
    }
    payload = {
        **data,
        "iat": int(now.timestamp()),
        "exp": int(expires_at.timestamp()),
    }

    encoded_header = base64_url_encode(
        json.dumps(header, separators=(",", ":")).encode("utf-8")
    )
    encoded_payload = base64_url_encode(
        json.dumps(payload, separators=(",", ":")).encode("utf-8")
    )
    unsigned_token = f"{encoded_header}.{encoded_payload}"
    signature = hmac.new(
        settings.secret_key.encode("utf-8"),
        unsigned_token.encode("utf-8"),
        hashlib.sha256,
    ).digest()

    return f"{unsigned_token}.{base64_url_encode(signature)}"


def decode_access_token(token: str) -> dict:
    if not settings.secret_key:
        raise HTTPException(status_code=500, detail="SECRET_KEY no esta configurada")

    try:
        encoded_header, encoded_payload, received_signature = token.split(".")
        unsigned_token = f"{encoded_header}.{encoded_payload}"
        expected_signature = hmac.new(
            settings.secret_key.encode("utf-8"),
            unsigned_token.encode("utf-8"),
            hashlib.sha256,
        ).digest()

        if not hmac.compare_digest(
            base64_url_encode(expected_signature),
            received_signature,
        ):
            raise HTTPException(status_code=401, detail="Token invalido")

        header = json.loads(base64_url_decode(encoded_header))
        payload = json.loads(base64_url_decode(encoded_payload))
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=401, detail="Token invalido") from exc

    if header.get("alg") != "HS256":
        raise HTTPException(status_code=401, detail="Token invalido")

    expires_at = payload.get("exp")
    if not expires_at or int(expires_at) < int(datetime.now(timezone.utc).timestamp()):
        raise HTTPException(status_code=401, detail="Token expirado")

    return payload


def validate_access_token(authorization: Optional[str] = Header(None)) -> dict:
    if not authorization:
        raise HTTPException(status_code=401, detail="Token requerido")

    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(status_code=401, detail="Token invalido")

    return decode_access_token(token)


def normalize_phone_number(phone_number: str) -> str:
    normalized_phone_number = phone_number.replace("+", "").strip()
    if normalized_phone_number.startswith("52") and not normalized_phone_number.startswith("521"):
        return f"521{normalized_phone_number[2:]}"
    return normalized_phone_number


def get_whatsapp_message_id(result: dict) -> Optional[str]:
    messages = result.get("messages", [])
    if not messages:
        return None
    return messages[0].get("id")


def get_incoming_message_text(message: dict) -> Optional[str]:
    message_type = message.get("type")

    if message_type == "text":
        return message.get("text", {}).get("body")
    if message_type == "button":
        return message.get("button", {}).get("text")
    if message_type == "interactive":
        interactive = message.get("interactive", {})
        button_reply = interactive.get("button_reply")
        list_reply = interactive.get("list_reply")
        if button_reply:
            return button_reply.get("title")
        if list_reply:
            return list_reply.get("title")

    return None


def build_incoming_message(message: dict) -> Optional[Messages]:
    phone = message.get("from")
    if not phone:
        return None

    return Messages(
        phone_number=normalize_phone_number(phone),
        direction="incoming",
        message_type=message.get("type", "unknown"),
        text=get_incoming_message_text(message),
        whatsapp_message_id=message.get("id"),
    )


def serialize_message(message: Messages) -> dict:
    return {
        "id": message.id,
        "phone_number": message.phone_number,
        "direction": message.direction,
        "message_type": message.message_type,
        "text": message.text,
        "whatsapp_message_id": message.whatsapp_message_id,
        "created_at": message.created_at.isoformat() if message.created_at else None,
    }
