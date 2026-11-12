from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    PROJECT_NAME: str = "University Access Control & Attendance CRM"
    API_V1_STR: str = "/api/v1"
    
    # Database
    DATABASE_URL: str = "sqlite:///./access_control.db"
    
    # Uploads (Har doim loyiha ildizidagi uploads papkasi)
    UPLOAD_DIR: str = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "uploads")
    
    # CORS
    BACKEND_CORS_ORIGINS: list[str] = ["*"]
    
    # Telegram Bot
    ENABLE_TELEGRAM_BOT: bool = True
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "8929971710:AAH0b9dlx8R1KLGL_SqvYLtwb689GVlj9x8")
    TELEGRAM_MASTER_BOT_TOKEN: str = os.getenv("TELEGRAM_MASTER_BOT_TOKEN", "8640045696:AAGf_2-5YffGjht4jTQTKGWb3ltSf4uWcY8")
    SUPERADMIN_CHAT_ID: str = os.getenv("SUPERADMIN_CHAT_ID", "1801746044")
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
