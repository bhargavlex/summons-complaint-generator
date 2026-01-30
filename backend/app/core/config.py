"""
Application configuration settings.
"""

from pydantic_settings import BaseSettings
from typing import Optional, List


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # --------------------
    # API Configuration
    # --------------------
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Summons & Complaint Generator"
    DEBUG: bool = True

    # --------------------
    # Database
    # --------------------
    DATABASE_URL: str = "mysql+pymysql://user:password@localhost:3306/summons_db"

    # --------------------
    # Redis
    # --------------------
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: Optional[str] = None
    REDIS_DB: int = 0

    # --------------------
    # Azure OpenAI Configuration
    # --------------------
    AZURE_OPENAI_KEY: Optional[str] = None
    AZURE_OPENAI_API_KEY: Optional[str] = None  # .env / Azure docs use this name
    AZURE_OPENAI_ENDPOINT: Optional[str] = None
    AZURE_OPENAI_DEPLOYMENT: Optional[str] = None
    AZURE_OPENAI_API_VERSION: str = "2024-12-01-preview"

    @property
    def azure_openai_key(self) -> Optional[str]:
        """Effective API key: AZURE_OPENAI_API_KEY (env) or AZURE_OPENAI_KEY."""
        return self.AZURE_OPENAI_API_KEY or self.AZURE_OPENAI_KEY

    @property
    def use_azure_openai(self) -> bool:
        """Check if Azure OpenAI configuration is available"""
        return all([
            self.azure_openai_key,
            self.AZURE_OPENAI_ENDPOINT,
            self.AZURE_OPENAI_DEPLOYMENT
        ])

    # --------------------
    # File Storage
    # --------------------
    UPLOAD_DIR: str = "./uploads"
    TEMPLATE_DIR: str = "./templates"
    PREVIEW_DIR: str = "./previews"
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB

    # --------------------
    # PDF to Image
    # --------------------
    POPPLER_PATH: Optional[str] = None

    # --------------------
    # CORS
    # --------------------
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173"
    ]

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
