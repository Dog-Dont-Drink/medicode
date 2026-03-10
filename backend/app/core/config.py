"""Application configuration loaded from environment variables."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings


ENV_FILE = Path(__file__).resolve().parents[2] / ".env"
DEFAULT_SQLITE_PATH = ENV_FILE.parent / "medicode.db"


class Settings(BaseSettings):
    # App
    APP_ENV: str = "development"
    APP_PORT: int = 8000

    # Database
    DATABASE_URL: str = f"sqlite+aiosqlite:///{DEFAULT_SQLITE_PATH.as_posix()}"
    DATABASE_ECHO: bool = False

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # JWT
    JWT_SECRET_KEY: str = "change-me-to-a-random-secret-key"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_DAYS: int = 30
    JWT_REFRESH_EXPIRE_DAYS: int = 90

    # Storage
    STORAGE_BACKEND: str = "local"
    STORAGE_BUCKET: str = "medicode-files"
    LOCAL_STORAGE_DIR: str = str(ENV_FILE.parent / "uploads")
    PUBLIC_BASE_URL: str = "http://localhost:8000"
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""
    SUPABASE_PUBLISHABLE_KEY: str = ""

    # Alipay
    ALIPAY_APP_ID: str = ""
    ALIPAY_PRIVATE_KEY: str = ""
    ALIPAY_PUBLIC_KEY: str = ""
    ALIPAY_NOTIFY_URL: str = ""
    ALIPAY_SANDBOX: bool = False

    # SMTP
    SMTP_SERVER: str = "smtp.163.com"
    SMTP_PORT: int = 465
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_USE_TLS: bool = True
    SMTP_START_TLS: bool = False

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    # LLM
    LLM_API_BASE_URL: str = "https://api.deepseek.com"
    LLM_API_KEY: str = ""
    LLM_MODEL: str = "deepseek-chat"
    LLM_TIMEOUT_SECONDS: int = 60

    # Resource billing
    DEFAULT_RESOURCE_BALANCE: int = 100
    AI_INTERPRETATION_RESOURCE_COST: int = 1
    PDF_EXPORT_RESOURCE_COST: int = 1
    RESOURCE_LABEL: str = "资源"
    RESOURCE_ICON: str = "⚡"

    # R runtime
    RSCRIPT_COMMAND: str = "Rscript"
    R_AUTO_INSTALL_ENABLED: bool = True
    R_PACKAGE_REPO: str = "https://cloud.r-project.org"
    R_INSTALL_TIMEOUT_SECONDS: int = 900

    model_config = {
        "env_file": str(ENV_FILE),
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


@lru_cache
def get_settings() -> Settings:
    return Settings()
