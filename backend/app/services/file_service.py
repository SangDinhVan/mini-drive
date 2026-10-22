import logging
import warnings
from pathlib import Path
from uuid import UUID

from fastapi import HTTPException, UploadFile
from PIL import Image, UnidentifiedImageError

from app.core.config import Settings
from app.db.models import StoredFile
from app.repositories.file_repository import FileRepository
from app.services.storage import LocalStorage, UploadTooLarge

logger = logging.getLogger("mini_drive")
PREVIEW_TYPES = {"PNG": "image/png", "JPEG": "image/jpeg", "WEBP": "image/webp"}
PREVIEW_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}


def verified_content_type(path: Path, name: str, claimed_type: str | None):
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(path) as image:
                content_type = PREVIEW_TYPES.get(image.format)
                if content_type:
                    image.verify()
                    with Image.open(path) as decoded:
                        decoded.load()
                    return content_type
    except (UnidentifiedImageError, OSError, ValueError, SyntaxError, Image.DecompressionBombWarning, Image.DecompressionBombError):
        pass
    if claimed_type in PREVIEW_TYPES.values() or Path(name).suffix.lower() in PREVIEW_EXTENSIONS:
        raise HTTPException(415, "This image is invalid or exceeds safe image dimensions.")
    return "application/octet-stream"


class FileService:
    def __init__(self, repository: FileRepository, storage: LocalStorage, settings: Settings):
        self.repository = repository
        self.storage = storage
        self.settings = settings

    def get(self, file_id: UUID):
        item = self.repository.get(file_id)
        if item is None:
            raise HTTPException(404, "File not found.")
        return item

    def upload(self, upload: UploadFile):
        name = upload.filename or ""
        if not name.strip() or name in {".", ".."} or len(name) > 255 or any(c in name for c in "/\\") or any(ord(c) < 32 or ord(c) == 127 for c in name):
            raise HTTPException(400, "Use a filename without paths or control characters (maximum 255 characters).")
        key = None
        try:
            key, size = self.storage.save(upload.file, self.settings.max_upload_mb * 1024 * 1024)
            content_type = verified_content_type(self.storage.path(key), name, upload.content_type)
            return self.repository.add(StoredFile(original_name=name, storage_key=key, size_bytes=size, content_type=content_type))
        except UploadTooLarge:
            raise HTTPException(413, f"Each file must be at most {self.settings.max_upload_mb} MiB.") from None
        except Exception:
            self.repository.rollback()
            if key is not None:
                self.storage.remove(key)
            raise
        finally:
            upload.file.close()

    def content(self, file_id: UUID):
        item = self.get(file_id)
        path = self.storage.path(item.storage_key)
        if not path.is_file():
            raise HTTPException(404, "File content is missing from local storage.")
        return item, path

    def delete(self, file_id: UUID):
        item = self.get(file_id)
        staged = self.storage.stage_delete(item.storage_key)
        try:
            self.repository.delete(item)
        except Exception:
            self.repository.rollback()
            self.storage.restore(item.storage_key, staged)
            raise
        # shortcut: a process crash can leave staged bytes, add reconciliation before production use.
        if staged is not None:
            try:
                staged.unlink()
            except OSError:
                logger.error("Staged file cleanup failed for file_id=%s", file_id)
                raise
