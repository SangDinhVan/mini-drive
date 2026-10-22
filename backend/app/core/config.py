import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy.engine import make_url

BACKEND_DIR = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Settings:
    database_url: str | None = None
    upload_dir: Path = BACKEND_DIR / "uploads"
    max_upload_mb: int = 10

    def __post_init__(self):
        if self.max_upload_mb <= 0:
            raise ValueError("MAX_UPLOAD_MB must be a positive integer")
        directory = Path(self.upload_dir)
        if not directory.is_absolute():
            directory = BACKEND_DIR / directory
        object.__setattr__(self, "upload_dir", directory.resolve())
        if self.database_url:
            url = make_url(self.database_url)
            if url.get_backend_name() != "postgresql":
                raise ValueError("DATABASE_URL must point to PostgreSQL")
            url = url.set(drivername="postgresql+psycopg")
            url = url.update_query_dict({"sslmode": "require"})
            object.__setattr__(self, "database_url", url.render_as_string(hide_password=False))

    @classmethod
    def from_env(cls):
        load_dotenv(BACKEND_DIR / ".env")
        return cls(
            database_url=os.getenv("DATABASE_URL") or None,
            upload_dir=Path(os.getenv("UPLOAD_DIR", "uploads")),
            max_upload_mb=int(os.getenv("MAX_UPLOAD_MB", "10")),
        )
