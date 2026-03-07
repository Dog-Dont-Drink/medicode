"""FastAPI application entry point."""

import logging
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import inspect, text

from app.api.v1.api import router as api_v1_router
from app.core.config import get_settings
from app.core.exceptions import AppException
from app.db.database import engine
from app.db.models.base import Base

# Import all models so Base.metadata knows about them
from app.db.models import user, project, dataset, analysis, order  # noqa: F401

settings = get_settings()
logger = logging.getLogger(__name__)
local_storage_dir = Path(settings.LOCAL_STORAGE_DIR).expanduser().resolve()


def _ensure_runtime_schema(sync_conn) -> None:
    inspector = inspect(sync_conn)
    if "token_usage" not in inspector.get_table_names():
        return

    existing_columns = {column["name"] for column in inspector.get_columns("token_usage")}
    if "actual_tokens_consumed" not in existing_columns:
        sync_conn.execute(
            text("ALTER TABLE token_usage ADD COLUMN actual_tokens_consumed INTEGER NOT NULL DEFAULT 0")
        )

app = FastAPI(
    title="MediCode API",
    description="医学统计分析平台后端接口",
    version="1.0.0",
)

if settings.STORAGE_BACKEND == "local":
    local_storage_dir.mkdir(parents=True, exist_ok=True)
    app.mount("/uploads", StaticFiles(directory=local_storage_dir), name="uploads")

# ── CORS ──────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Startup event — create tables (dev only) ─────────────
@app.on_event("startup")
async def on_startup():
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            await conn.run_sync(_ensure_runtime_schema)
    except Exception as exc:
        logger.exception("Database startup failed")
        raise RuntimeError("Failed to initialize database. Please verify DATABASE_URL and local DB dependencies.") from exc


@app.on_event("shutdown")
async def on_shutdown():
    await engine.dispose()


# ── Global error handler ─────────────────────────────────
@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


# ── Routes ────────────────────────────────────────────────
app.include_router(api_v1_router)


@app.get("/health", tags=["健康检查"])
async def health_check():
    return {"status": "ok", "version": "1.0.0"}
