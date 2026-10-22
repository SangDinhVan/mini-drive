from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, Request, Response, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories.file_repository import FileRepository
from app.schemas.file import FileItem
from app.services.file_service import FileService, PREVIEW_TYPES
from app.services.storage import LocalStorage

router = APIRouter(prefix="/api/files", tags=["files"])


def get_service(request: Request, session: Annotated[Session, Depends(get_db)]):
    settings = request.app.state.settings
    return FileService(FileRepository(session), LocalStorage(settings.upload_dir), settings)


Service = Annotated[FileService, Depends(get_service)]


@router.post("", response_model=FileItem, status_code=201)
def upload_file(service: Service, file: Annotated[UploadFile, File()]):
    return FileItem.from_record(service.upload(file))


@router.get("", response_model=list[FileItem])
def list_files(service: Service):
    return [FileItem.from_record(item) for item in service.repository.list()]


@router.get("/{file_id}", response_model=FileItem)
def get_file(file_id: UUID, service: Service):
    return FileItem.from_record(service.get(file_id))


@router.get("/{file_id}/content")
def get_content(file_id: UUID, service: Service, download: bool = False):
    item, path = service.content(file_id)
    preview = not download and item.content_type in PREVIEW_TYPES.values()
    return FileResponse(path, media_type=item.content_type or "application/octet-stream",
                        filename=item.original_name, content_disposition_type="inline" if preview else "attachment")


@router.delete("/{file_id}", status_code=204)
def delete_file(file_id: UUID, service: Service):
    service.delete(file_id)
    return Response(status_code=204)

