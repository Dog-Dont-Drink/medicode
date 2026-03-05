"""Async SQLAlchemy engine and session factory."""

from uuid import uuid4

from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import get_settings

settings = get_settings()

def _build_database_url(raw_url: str):
    database_url = raw_url.strip()
    if database_url.startswith("postgres://"):
        database_url = "postgresql://" + database_url[len("postgres://"):]

    url = make_url(database_url)
    if url.drivername == "postgresql":
        url = url.set(drivername="postgresql+asyncpg")
    elif url.drivername != "postgresql+asyncpg":
        raise RuntimeError("DATABASE_URL must use the PostgreSQL protocol.")

    host = url.host or ""
    if "supabase" not in host:
        raise RuntimeError("DATABASE_URL must point to a Supabase Postgres host.")

    return url


database_url = _build_database_url(settings.DATABASE_URL)
ssl_mode = database_url.query.get("sslmode", "require")
if "sslmode" in database_url.query:
    query_without_sslmode = dict(database_url.query)
    query_without_sslmode.pop("sslmode", None)
    database_url = database_url.set(query=query_without_sslmode)

connect_args = {
    "ssl": ssl_mode,
    "server_settings": {
        "application_name": "medicode-backend",
    }
}
engine_kwargs = {
    "echo": settings.APP_ENV == "development",
    "pool_pre_ping": True,
    "connect_args": connect_args,
}

# Supabase transaction pooler sits behind a PgBouncer-compatible proxy.
if (database_url.host or "").endswith(".pooler.supabase.com") and database_url.port == 6543:
    database_url = database_url.update_query_dict({"prepared_statement_cache_size": "0"})
    engine_kwargs["poolclass"] = NullPool
    connect_args["prepared_statement_name_func"] = lambda: f"__asyncpg_{uuid4().hex}__"

engine = create_async_engine(database_url, **engine_kwargs)

async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db():
    """FastAPI dependency that yields an async DB session."""
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
