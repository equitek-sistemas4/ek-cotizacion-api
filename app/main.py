import logging
from pathlib import Path

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.database import Base, engine
from app import models
from app.routes.contacts import router as contacts_router
from app.routes.whatsapp import router as whatsapp_router
from app.routes.chats import router as chats_router
from app.routes.chats_whatsapp import router as chats_whatsapp_router
from app.routes.users import router as users_router
from app.routes.auth import router as auth_router
from app.routes.chat_messages import router as chat_messages_router
from app.routes.chat_files import router as chat_files_router
from app.routes.chat_websocket import router as chat_websocket_router
from app.routes.quotations import router as quotations_router
from app.routes.chat_members import router as chat_members_router
from app.routes.roles import router as roles_router
from app.routes.notifications import router as notifications_router
from app.routes.quotation_events import router as quotation_events_router
from app.utils.utils import validate_access_token


Base.metadata.create_all(bind=engine)
logging.basicConfig(level=logging.INFO)

app = FastAPI(title="PruebasCom API", version="0.1.0")

uploads_directory = Path(__file__).resolve().parents[1] / "uploads"
uploads_directory.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=uploads_directory), name="uploads")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_origin_regex=(
        r"https?://(localhost|127\.0\.0\.1)(:\d+)?"
        r"|https?://\d{1,3}(\.\d{1,3}){3}(:\d+)?"
        r"|https://[a-zA-Z0-9-]+\.(ngrok-free\.app|ngrok-free\.dev|ngrok\.io)"
    ),
    allow_credentials="*" not in settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(whatsapp_router)
app.include_router(chat_websocket_router)
app.include_router(chats_router, dependencies=[Depends(validate_access_token)])
app.include_router(chats_whatsapp_router, dependencies=[Depends(validate_access_token)])
app.include_router(chat_messages_router, dependencies=[Depends(validate_access_token)])
app.include_router(chat_files_router, dependencies=[Depends(validate_access_token)])
app.include_router(contacts_router, dependencies=[Depends(validate_access_token)])
app.include_router(users_router, dependencies=[Depends(validate_access_token)])
app.include_router(roles_router, dependencies=[Depends(validate_access_token)])
app.include_router(notifications_router, dependencies=[Depends(validate_access_token)])
app.include_router(quotation_events_router, dependencies=[Depends(validate_access_token)])
app.include_router(quotations_router, dependencies=[Depends(validate_access_token)])
app.include_router(chat_members_router)
app.include_router(auth_router)
