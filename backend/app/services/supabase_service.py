"""Supabase client integration used by FastAPI services."""

from typing import Any, Dict, List, Optional

from supabase import AClient, acreate_client

from app.core.config import get_settings

_supabase_client: Optional[AClient] = None


async def get_supabase_client() -> AClient:
    global _supabase_client

    if _supabase_client is not None:
        return _supabase_client

    settings = get_settings()
    api_key = settings.SUPABASE_KEY or settings.SUPABASE_PUBLISHABLE_KEY
    if not settings.SUPABASE_URL or not api_key:
        raise RuntimeError(
            "Supabase is not configured. Set SUPABASE_URL and SUPABASE_KEY "
            "(or SUPABASE_PUBLISHABLE_KEY for read-only testing)."
        )

    _supabase_client = await acreate_client(
        settings.SUPABASE_URL,
        api_key,
    )
    return _supabase_client


async def select_rows(table_name: str, columns: str = "*", limit: int = 100) -> List[Dict[str, Any]]:
    client = await get_supabase_client()
    response = await client.table(table_name).select(columns).limit(limit).execute()
    return response.data
