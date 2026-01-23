"""
Application configuration
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "mysql+pymysql://appuser:apppass@localhost:3306/appdb"
    
    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = "redispass"
    REDIS_DB: int = 0
    
    # Application
    DEBUG: bool = True
    PROJECT_NAME: str = "Summons & Complaint Generator"
    
    # File Storage
    UPLOAD_DIR: str = "./uploads"
    TEMPLATE_DIR: str = "./templates"
    PREVIEW_DIR: str = "./previews"
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
