import os
import re
import tempfile
from pathlib import Path
from typing import BinaryIO
from uuid import uuid4


class UploadTooLarge(ValueError):
    pass


class LocalStorage:
    def __init__(self, directory: Path):
        self.directory = directory

    def path(self, key: str):
        if not re.fullmatch(r"[0-9a-f]{32}", key):
            raise ValueError("Invalid storage key")
        path = self.directory / key
        if path.is_symlink():
            raise OSError("Storage file must not be a symlink")
        return path

    def save(self, source: BinaryIO, max_bytes: int):
        self.directory.mkdir(parents=True, exist_ok=True)
        key = uuid4().hex
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(dir=self.directory, prefix=".upload-", delete=False) as output:
                temporary = Path(output.name)
                size = 0
                while chunk := source.read(64 * 1024):
                    size += len(chunk)
                    if size > max_bytes:
                        raise UploadTooLarge
                    output.write(chunk)
                output.flush()
                os.fsync(output.fileno())
            os.replace(temporary, self.path(key))
            return key, size
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)

    def remove(self, key: str):
        self.path(key).unlink(missing_ok=True)

    def stage_delete(self, key: str):
        original = self.path(key)
        staged = self.directory / f".delete-{key}-{uuid4().hex}"
        try:
            original.rename(staged)
        except FileNotFoundError:
            return None
        return staged

    def restore(self, key: str, staged: Path | None):
        if staged is not None:
            staged.rename(self.path(key))
