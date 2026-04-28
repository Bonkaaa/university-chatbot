from chainlit.data.storage_clients.base import BaseStorageClient
from pathlib import Path
from urllib.parse import quote
from ...config import PUBLIC_ROOT

import uuid


PUBLIC_DIR = PUBLIC_ROOT.resolve()
UPLOADS_DIR = PUBLIC_DIR / "uploads"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

class LocalPublicStorageClient(BaseStorageClient):
    """
    Local storage provider for Chainlit elements.
    Files are stored in ./public/uploads and served by Chainlit at /public/uploads/*.
    """

    def _path_for_key(self, object_key: str) -> Path:
        safe_key = object_key.strip().replace("\\", "/").lstrip("/")
        if not safe_key:
            safe_key = str(uuid.uuid4())
        return (UPLOADS_DIR / safe_key).resolve()

    async def upload_file(
        self,
        object_key: str,
        data: bytes | str,
        mime: str = "application/octet-stream",
        overwrite: bool = True,
        content_disposition: str | None = None,
    ) -> dict:
        file_path = self._path_for_key(object_key)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        if file_path.exists() and not overwrite:
            raise FileExistsError(f"File already exists: {file_path}")

        if isinstance(data, str):
            file_path.write_text(data, encoding="utf-8")
        else:
            file_path.write_bytes(data)

        relative = file_path.relative_to(PUBLIC_DIR.resolve()).as_posix()
        return {
            "object_key": object_key,
            "url": f"/public/{quote(relative)}",
        }

    async def delete_file(self, object_key: str) -> bool:
        file_path = self._path_for_key(object_key)
        if file_path.exists():
            file_path.unlink()
        return True

    async def get_read_url(self, object_key: str) -> str:
        file_path = self._path_for_key(object_key)
        if not file_path.exists():
            raise FileNotFoundError(f"Missing object: {object_key}")
        relative = file_path.relative_to(PUBLIC_DIR.resolve()).as_posix()
        return f"/public/{quote(relative)}"

    async def close(self) -> None:
        return None