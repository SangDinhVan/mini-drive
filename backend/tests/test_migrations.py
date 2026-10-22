from pathlib import Path

from alembic import command
from alembic.config import Config
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from sqlalchemy import create_engine, inspect

from app.core.config import BACKEND_DIR, Settings
from app.db.models import Base
import pytest


def test_migration_matches_model_and_is_reversible(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'migration.db'}")
    config = Config(str(BACKEND_DIR / "alembic.ini"))
    with engine.begin() as connection:
        config.attributes["connection"] = connection
        command.upgrade(config, "head")
        assert "files" in inspect(connection).get_table_names()
        assert compare_metadata(MigrationContext.configure(connection), Base.metadata) == []
        command.downgrade(config, "base")
        assert "files" not in inspect(connection).get_table_names()
    engine.dispose()


def test_settings_resolve_backend_path_and_require_postgresql_tls():
    settings = Settings(database_url="postgresql://user:password@host/db", upload_dir=Path("uploads"))
    assert settings.upload_dir == BACKEND_DIR / "uploads"
    assert settings.database_url == "postgresql+psycopg://user:password@host/db?sslmode=require"
    with pytest.raises(ValueError):
        Settings(database_url="sqlite:///app.db")
    with pytest.raises(ValueError):
        Settings(max_upload_mb=0)
