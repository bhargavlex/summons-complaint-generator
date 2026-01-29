"""
Application configuration settings.
"""

from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # API Configuration
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Summons & Complaint Generator"
    
    # Database
    DATABASE_URL: str = "mysql+pymysql://user:password@localhost:3306/summons_db"
    
    # OpenAI Configuration (Standard OpenAI)
    
    
    # Azure OpenAI Configuration
    AZURE_OPENAI_KEY: Optional[str] = os.getenv("AZURE_OPENAI_KEY")
    AZURE_OPENAI_ENDPOINT: Optional[str] = os.getenv("AZURE_OPENAI_ENDPOINT")
    AZURE_OPENAI_DEPLOYMENT: Optional[str] = os.getenv("AZURE_OPENAI_DEPLOYMENT")
    AZURE_OPENAI_API_VERSION: Optional[str] = os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview")
    
    # PDF to Image Configuration
    POPPLER_PATH: Optional[str] = os.getenv("POPPLER_PATH")
    
    # Determine which provider to use
    @property
    def use_azure_openai(self) -> bool:
        """Check if Azure OpenAI configuration is available"""
        return bool(self.AZURE_OPENAI_KEY and self.AZURE_OPENAI_ENDPOINT and self.AZURE_OPENAI_DEPLOYMENT)
    
    # File Storage
    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB
    
    # CORS
    BACKEND_CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:5173"]
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

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
