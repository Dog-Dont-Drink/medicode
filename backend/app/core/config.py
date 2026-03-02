"""Application configuration loaded from environment variables."""
from __future__ import annotations

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # App
    APP_ENV: str = "development"
    APP_PORT: int = 8000

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost:5432/medicode"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # JWT
    JWT_SECRET_KEY: str = "change-me-to-a-random-secret-key"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_DAYS: int = 30
    JWT_REFRESH_EXPIRE_DAYS: int = 90

    # Storage
    STORAGE_BUCKET: str = "medicode-files"
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""

    # Alipay
    ALIPAY_APP_ID: str = ""
    ALIPAY_PRIVATE_KEY: str = ""
    ALIPAY_PUBLIC_KEY: str = ""
    ALIPAY_NOTIFY_URL: str = ""
    ALIPAY_SANDBOX: bool = True

    # SMTP
    SMTP_SERVER: str = "smtp.163.com"
    SMTP_PORT: int = 465
    SMTP_USER: str = "medicode@163.com"
    SMTP_PASSWORD: str = "XWpprxpQrGiue9ui"

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
