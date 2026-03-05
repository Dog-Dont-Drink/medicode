"""Supabase Storage integration for dataset files."""

from typing import Optional
from urllib.parse import urlparse

from app.core.config import get_settings
from app.services.supabase_service import get_supabase_client


class SupabaseStorageService:
    def __init__(self) -> None:
        self.settings = get_settings()

    def _ensure_config(self) -> None:
        if not self.settings.SUPABASE_URL or not self.settings.SUPABASE_KEY:
            raise RuntimeError("Supabase Storage is not configured. Set SUPABASE_URL and SUPABASE_KEY.")

    async def upload(self, object_key: str, content: bytes, content_type: str) -> str:
        self._ensure_config()
        client = await get_supabase_client()
        await client.storage.from_(self.settings.STORAGE_BUCKET).upload(
            object_key,
            content,
            {"content-type": content_type, "x-upsert": "false"},
        )

        return object_key

    async def delete(self, object_key: str) -> None:
        self._ensure_config()
        client = await get_supabase_client()
        await client.storage.from_(self.settings.STORAGE_BUCKET).remove([object_key])

    async def get_public_url(self, object_key: str) -> str:
        self._ensure_config()
        client = await get_supabase_client()
        return await client.storage.from_(self.settings.STORAGE_BUCKET).get_public_url(object_key)

    def extract_object_key(self, file_url: str) -> Optional[str]:
        if not file_url:
            return None

        parsed = urlparse(file_url)
        marker = f"/storage/v1/object/public/{self.settings.STORAGE_BUCKET}/"
        if marker not in parsed.path:
            return None

        return parsed.path.split(marker, 1)[1]


storage_service = SupabaseStorageService()
