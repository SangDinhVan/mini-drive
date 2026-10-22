from io import BytesIO
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from PIL import Image
from sqlalchemy import create_engine, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker

from app.core.config import Settings
from app.db.models import Base, StoredFile
from app.main import create_app


@pytest.fixture
def context(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'test.db'}")
    Base.metadata.create_all(engine)
    sessions = sessionmaker(engine, expire_on_commit=False)
    settings = Settings(upload_dir=tmp_path / "uploads", max_upload_mb=1)
    with TestClient(create_app(settings, sessions)) as client:
        yield client, settings, sessions
    engine.dispose()


def upload(client, name="notes.txt", data=b"hello", content_type="text/plain"):
    return client.post("/api/files", files={"file": (name, data, content_type)})


def image_bytes(format="PNG"):
    stream = BytesIO()
    Image.new("RGB", (2, 2), "green").save(stream, format=format)
    return stream.getvalue()


def test_lifecycle_and_persistence(context):
    client, settings, sessions = context
    assert client.get("/api/health").json() == {"status": "ok"}
    assert client.get("/api/files").json() == []
    response = upload(client, "ghi chu.txt")
    assert response.status_code == 201
    item = response.json()
    assert item["name"] == "ghi chu.txt"
    assert item["size_bytes"] == 5
    assert item["preview_url"] is None
    assert "storage_key" not in item
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-request-id"]
    assert client.get(f"/api/files/{item['id']}").json() == item
    assert len(list(settings.upload_dir.iterdir())) == 1
    with TestClient(create_app(settings, sessions)) as restarted:
        assert restarted.get("/api/files").json() == [item]
        content = restarted.get(item["download_url"])
        assert content.content == b"hello"
        assert "attachment" in content.headers["content-disposition"]
        assert restarted.delete(f"/api/files/{item['id']}").status_code == 204
    assert client.get("/api/files").json() == []
    assert list(settings.upload_dir.iterdir()) == []
    assert client.get(item["download_url"]).status_code == 404


@pytest.mark.parametrize("format,mime", [("PNG", "image/png"), ("JPEG", "image/jpeg"), ("WEBP", "image/webp")])
def test_verified_image_preview(context, format, mime):
    client, _, _ = context
    data = image_bytes(format)
    response = upload(client, "photo.bin", data, "application/octet-stream")
    assert response.status_code == 201
    item = response.json()
    assert item["content_type"] == mime
    preview = client.get(item["preview_url"])
    assert preview.content == data
    assert preview.headers["content-type"] == mime
    assert "inline" in preview.headers["content-disposition"]
    assert "attachment" in client.get(item["download_url"]).headers["content-disposition"]


@pytest.mark.parametrize("name", ["../outside.txt", "..\\outside.txt", "/tmp/file", " ", ".", ".."])
def test_rejects_unsafe_names(context, name):
    client, settings, _ = context
    assert upload(client, name).status_code == 400
    assert client.get("/api/files").json() == []
    assert not settings.upload_dir.exists() or list(settings.upload_dir.iterdir()) == []


def test_actual_size_limit_and_cleanup(context):
    client, settings, _ = context
    assert upload(client, data=b"a" * (1024 * 1024)).status_code == 201
    response = upload(client, data=b"b" * (1024 * 1024 + 1))
    assert response.status_code == 413
    assert len(client.get("/api/files").json()) == 1
    assert len(list(settings.upload_dir.iterdir())) == 1


def test_forged_image_and_html(context):
    client, settings, _ = context
    assert upload(client, "fake.png", b"<script>alert(1)</script>", "image/png").status_code == 415
    assert list(settings.upload_dir.iterdir()) == []
    item = upload(client, "page.html", b"<h1>unsafe</h1>", "text/html").json()
    assert item["preview_url"] is None
    content = client.get(f"/api/files/{item['id']}/content")
    assert content.headers["content-type"] == "application/octet-stream"
    assert "attachment" in content.headers["content-disposition"]


def test_missing_and_invalid_ids(context):
    client, _, _ = context
    for path in [f"/api/files/{uuid4()}", f"/api/files/{uuid4()}/content"]:
        assert client.get(path).status_code == 404
    assert client.delete(f"/api/files/{uuid4()}").status_code == 404
    assert client.get("/api/files/not-a-uuid").status_code == 422


def test_missing_bytes_can_still_remove_metadata(context):
    client, settings, _ = context
    item = upload(client).json()
    next(settings.upload_dir.iterdir()).unlink()
    assert client.get(item["download_url"]).status_code == 404
    assert client.delete(f"/api/files/{item['id']}").status_code == 204
    assert client.get("/api/files").json() == []


def test_database_upload_failure_cleans_bytes(context, monkeypatch):
    client, settings, sessions = context

    def fail_commit(self):
        raise SQLAlchemyError("private database error")

    monkeypatch.setattr(sessions.class_, "commit", fail_commit)
    response = upload(client)
    assert response.status_code == 503
    assert "private" not in response.text
    assert list(settings.upload_dir.iterdir()) == []
    assert client.get("/api/files").json() == []


def test_database_delete_failure_restores_bytes(context, monkeypatch):
    client, settings, sessions = context
    item = upload(client).json()

    def fail_commit(self):
        raise SQLAlchemyError("private database error")

    monkeypatch.setattr(sessions.class_, "commit", fail_commit)
    assert client.delete(f"/api/files/{item['id']}").status_code == 503
    assert client.get(item["download_url"]).content == b"hello"
    assert len(list(settings.upload_dir.iterdir())) == 1
    with sessions() as db:
        assert db.scalar(select(StoredFile)).original_name == "notes.txt"


def test_storage_delete_failure_keeps_metadata(context, monkeypatch):
    client, settings, _ = context
    item = upload(client).json()
    from app.services.storage import LocalStorage

    def fail_stage(self, key):
        raise PermissionError("private filesystem path")

    monkeypatch.setattr(LocalStorage, "stage_delete", fail_stage)
    response = client.delete(f"/api/files/{item['id']}")
    assert response.status_code == 500
    assert "private" not in response.text
    assert client.get(item["download_url"]).content == b"hello"
    assert len(list(settings.upload_dir.iterdir())) == 1


def test_unconfigured_database_returns_actionable_error(tmp_path):
    with TestClient(create_app(Settings(upload_dir=tmp_path))) as client:
        assert client.get("/api/health").status_code == 200
        response = client.get("/api/files")
        assert response.status_code == 503
        assert "DATABASE_URL" in response.json()["detail"]


def test_list_newest_first(context):
    client, _, _ = context
    first = upload(client, "first.txt").json()
    second = upload(client, "second.txt").json()
    assert [item["id"] for item in client.get("/api/files").json()] == [second["id"], first["id"]]


def test_rejects_large_body_before_multipart_spooling(context, monkeypatch):
    client, settings, _ = context
    from starlette.formparsers import MultiPartParser

    def reject_spooling(*args, **kwargs):
        raise AssertionError("Oversized request should be stopped before writing temporary data")

    monkeypatch.setattr(MultiPartParser, "on_part_data", reject_spooling)
    response = client.post("/api/files", files={"file": ("big.txt", b"x" * (2 * 1024 * 1024))}, headers={"content-length": "1"})
    assert response.status_code == 413
    assert not settings.upload_dir.exists() or not list(settings.upload_dir.iterdir())


def test_truncated_jpeg_cannot_be_previewed(context):
    client, settings, _ = context
    data = image_bytes("JPEG")[:-2]
    response = upload(client, "broken.jpg", data, "image/jpeg")
    assert response.status_code == 415
    assert list(settings.upload_dir.iterdir()) == []
