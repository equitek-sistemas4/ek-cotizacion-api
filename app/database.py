from urllib.parse import quote_plus

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import settings


password = quote_plus(settings.mysql_password)


if settings.mysql_host == "localhost" or settings.mysql_host == "127.0.0.1":
    DATABASE_URL = (
        f"mysql+pymysql://{settings.mysql_user}:{settings.mysql_password}"
        f"@/{settings.mysql_database}?unix_socket=/var/run/mysqld/mysqld.sock&charset=utf8mb4"
    )
else:
    DATABASE_URL = (
        f"mysql+pymysql://{settings.mysql_user}:{settings.mysql_password}"
        f"@{settings.mysql_host}:{settings.mysql_port}/{settings.mysql_database}?charset=utf8mb4"
    )


engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


########################## BASE DE DATOS DE COTIZACIONES ##########################
if settings.mysql_host_quote == "localhost" or settings.mysql_host_quote == "127.0.0.1":
    DATABASE_URL_QUOTE = (
        f"mysql+pymysql://{settings.mysql_user_quote}:{settings.mysql_password_quote}"
        f"@/{settings.mysql_database_quote}?unix_socket=/var/run/mysqld/mysqld.sock&charset=utf8mb4"
    )
else:
    DATABASE_URL_QUOTE = (
        f"mysql+pymysql://{settings.mysql_user_quote}:{settings.mysql_password_quote}"
        f"@{settings.mysql_host_quote}:{settings.mysql_port_quote}/{settings.mysql_database_quote}?charset=utf8mb4"
    )


engine_quote = create_engine(DATABASE_URL_QUOTE, pool_pre_ping=True)
SessionLocal_quote = sessionmaker(autocommit=False, autoflush=False, bind=engine_quote)
Base_quote = declarative_base()


def get_db_quote():
    db = SessionLocal_quote()
    try:
        yield db
    finally:
        db.close()