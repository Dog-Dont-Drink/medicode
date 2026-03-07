"""Storage service abstraction with local filesystem as the default backend."""

from pathlib import Path, PurePosixPath
from typing import Optional
from urllib.parse import quote, unquote, urlparse

from app.core.config import get_settings
from app.services.supabase_service import get_supabase_client


class LocalStorageService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.base_dir = Path(self.settings.LOCAL_STORAGE_DIR).expanduser().resolve()
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.public_base_url = self.settings.PUBLIC_BASE_URL.rstrip("/")

    def _resolve_path(self, object_key: str) -> Path:
        relative_path = Path(PurePosixPath(object_key))
        if relative_path.is_absolute() or ".." in relative_path.parts:
            raise RuntimeError("Invalid storage object key.")
        return self.base_dir / relative_path

    async def upload(self, object_key: str, content: bytes, content_type: str) -> str:
        file_path = self._resolve_path(object_key)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "wb") as file_obj:
            file_obj.write(content)
        return object_key

    async def delete(self, object_key: str) -> None:
        file_path = self._resolve_path(object_key)
        if file_path.exists():
            file_path.unlink()

    async def download(self, object_key: str) -> bytes:
        file_path = self._resolve_path(object_key)
        if not file_path.exists():
            raise RuntimeError("Stored file does not exist.")
        with open(file_path, "rb") as file_obj:
            return file_obj.read()

    async def get_public_url(self, object_key: str) -> str:
        normalized_key = object_key.lstrip("/")
        return f"{self.public_base_url}/uploads/{quote(normalized_key, safe='/')}"

    def extract_object_key(self, file_url: str) -> Optional[str]:
        if not file_url:
            return None

        parsed = urlparse(file_url)
        marker = "/uploads/"
        if marker not in parsed.path:
            return None

        return unquote(parsed.path.split(marker, 1)[1])


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

    async def download(self, object_key: str) -> bytes:
        self._ensure_config()
        client = await get_supabase_client()
        data = await client.storage.from_(self.settings.STORAGE_BUCKET).download(object_key)
        if isinstance(data, bytes):
            return data
        if isinstance(data, str):
            return data.encode("utf-8")
        raise RuntimeError("Failed to download object from Supabase Storage.")

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


def _build_storage_service():
    settings = get_settings()
    if settings.STORAGE_BACKEND == "supabase":
        return SupabaseStorageService()
    return LocalStorageService()


storage_service = _build_storage_service()
