from urllib.parse import quote_plus

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import settings


password = quote_plus(settings.mysql_password)


# Modifica tu bloque actual por este:
if settings.mysql_host == "localhost" or settings.mysql_host == "127.0.0.1":
    # En Ubuntu, la ruta por defecto del archivo socket de MySQL es esta:
    DATABASE_URL = (
        f"mysql+pymysql://{settings.mysql_user}:{settings.mysql_password}"
        f"@/{settings.mysql_database}?unix_socket=/var/run/mysqld/mysqld.sock&charset=utf8mb4"
    )
else:
    # Esta queda de respaldo por si en el futuro te conectas a una IP remota
    DATABASE_URL = (
        f"mysql+pymysql://{settings.mysql_user}:{settings.mysql_password}"
        f"@{settings.mysql_host}:{settings.mysql_port}/{settings.mysql_database}?charset=utf8mb4"
    )


#DATABASE_URL = (
#    f"mysql+pymysql://{settings.mysql_user}:{password}"
#    f"@{settings.mysql_host}:{settings.mysql_port}/{settings.mysql_database}"
#    "?charset=utf8mb4"
#)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
