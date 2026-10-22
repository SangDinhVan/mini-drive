from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import StoredFile


class FileRepository:
    def __init__(self, session: Session):
        self.session = session

    def list(self):
        return self.session.scalars(select(StoredFile).order_by(StoredFile.created_at.desc()).limit(100)).all()

    def get(self, file_id: UUID):
        return self.session.get(StoredFile, file_id)

    def add(self, item: StoredFile):
        self.session.add(item)
        self.session.commit()
        return item

    def delete(self, item: StoredFile):
        self.session.delete(item)
        self.session.commit()

    def rollback(self):
        self.session.rollback()
