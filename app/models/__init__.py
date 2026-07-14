from datetime import datetime
from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from app.database import Base


class Messages(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    phone_number = Column(String(30), index=True, nullable=False)
    direction = Column(String(20), nullable=False)
    message_type = Column(String(50), default="text")
    text = Column(Text, nullable=True)
    whatsapp_message_id = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.now)


class Chats(Base):
    __tablename__ = "chats"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    user_id = Column(Integer, nullable=False)
    status = Column(Integer, default=1)  # 1: active, 0: inactive
    created_at = Column(DateTime, default=datetime.now)


class ChatMembers(Base):
    __tablename__ = "chat_members"

    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(Integer, nullable=False)
    contact_id = Column(Integer, nullable=True)
    status = Column(Integer, default=1)  # 1: active, 0: inactive
    token = Column(Text, nullable=True)
    access_code = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.now)


class ChatMessages(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(Integer, nullable=False)
    text = Column(Text, nullable=False)
    sender_id = Column(Integer, nullable=True)  # Optional: ID of the sender (Contact)
    sender_type = Column(Enum("user", "contact"), nullable=False)  # 'user' or 'contact'
    status = Column(Integer, default=1)  # 1: active, 0: inactive
    created_at = Column(DateTime, default=datetime.now)
    files = relationship("ChatFiles", back_populates="message", cascade="all, delete-orphan")


class ChatFiles(Base):
    __tablename__ = "chat_files"

    id = Column(Integer, primary_key=True, index=True)
    chat_message_id = Column(Integer, ForeignKey("chat_messages.id"), nullable=False, index=True)
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    created_at = Column(DateTime, default=datetime.now)

    message = relationship("ChatMessages", back_populates="files")


class Contact(Base):
    __tablename__ = "contacts"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    phone_number = Column(String(30), index=True, nullable=False)
    display_name = Column(String(100), nullable=True)
    company = Column(String(100), nullable=True)
    status = Column(Integer, default=1)  # 1: active, 0: inactive
    created_at = Column(DateTime, default=datetime.now)


class Users(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password = Column(String(255), nullable=False)
    phone_number = Column(String(30), index=True, nullable=False)
    status = Column(Integer, default=1)  # 1: active, 0: inactive
    created_at = Column(DateTime, default=datetime.now)
