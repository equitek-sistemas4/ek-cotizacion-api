import os
from dotenv import load_dotenv

# Cargar variables del archivo .env
load_dotenv()


class Settings:
    whatsapp_api_version = os.getenv("WHATSAPP_API_VERSION")
    whatsapp_phone_number_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
    whatsapp_phone_number = os.getenv("WHATSAPP_PHONE_NUMBER")
    whatsapp_access_token = os.getenv("WHATSAPP_ACCESS_TOKEN")
    whatsapp_verify_token = os.getenv("WHATSAPP_VERIFY_TOKEN")
    
    mysql_host = os.getenv("MYSQL_HOST")
    mysql_port = os.getenv("MYSQL_PORT")
    mysql_user = os.getenv("MYSQL_USER")
    mysql_password = os.getenv("MYSQL_PASSWORD")
    mysql_database = os.getenv("MYSQL_DATABASE")

    mysql_host_quote = os.getenv("MYSQL_HOST_QUOTE")
    mysql_port_quote = os.getenv("MYSQL_PORT_QUOTE")
    mysql_user_quote = os.getenv("MYSQL_USER_QUOTE")
    mysql_password_quote = os.getenv("MYSQL_PASSWORD_QUOTE")
    mysql_database_quote = os.getenv("MYSQL_DATABASE_QUOTE")

    secret_key = os.getenv("SECRET_KEY")
    access_token_expire_minutes = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "600"))
    cors_origins = [
        origin.strip()
        for origin in os.getenv("CORS_ORIGINS", "*").split(",")
        if origin.strip()
    ]


settings = Settings()
