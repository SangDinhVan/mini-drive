from datetime import datetime, timezone
from uuid import UUID

from pydantic import BaseModel

from app.db.models import StoredFile
from app.services.file_service import PREVIEW_TYPES


class FileItem(BaseModel):
    id: UUID
    name: str
    content_type: str | None
    size_bytes: int
    created_at: datetime
    download_url: str
    preview_url: str | None

    @classmethod
    def from_record(cls, item: StoredFile):
        content_url = f"/api/files/{item.id}/content"
        created_at = item.created_at
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)
        return cls(id=item.id, name=item.original_name, content_type=item.content_type,
                   size_bytes=item.size_bytes, created_at=created_at,
                   download_url=f"{content_url}?download=1",
                   preview_url=content_url if item.content_type in PREVIEW_TYPES.values() else None)
