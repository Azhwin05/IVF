"""Artifact storage for generated report jobs.

Same small seam shape as ``app.laboratory.storage``: opaque keys, write-once,
swappable for MinIO later. Kept independent so the two modules stay decoupled.
"""

from __future__ import annotations

import io
import shutil
import uuid
from pathlib import Path
from typing import BinaryIO, Protocol

from app.core.config import Settings


class ReportArtifactStorage(Protocol):
    def put(self, data: bytes, *, suffix: str = "") -> str: ...
    def open(self, key: str) -> BinaryIO: ...
    def delete(self, key: str) -> None: ...


class LocalReportStorage:
    """Filesystem-backed artifact store for local dev and the worker."""

    def __init__(self, root: str | Path) -> None:
        self._root = Path(root)
        self._root.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        candidate = (self._root / key).resolve()
        if candidate.parent != self._root.resolve():
            raise ValueError("Invalid storage key.")
        return candidate

    def put(self, data: bytes, *, suffix: str = "") -> str:
        key = f"{uuid.uuid4()}{suffix}"
        self._path(key).write_bytes(data)
        return key

    def open(self, key: str) -> BinaryIO:
        return self._path(key).open("rb")

    def delete(self, key: str) -> None:
        self._path(key).unlink(missing_ok=True)


class InMemoryReportStorage:
    """Ephemeral artifact store used by the test suite."""

    def __init__(self) -> None:
        self._blobs: dict[str, bytes] = {}

    def put(self, data: bytes, *, suffix: str = "") -> str:
        key = f"{uuid.uuid4()}{suffix}"
        self._blobs[key] = data
        return key

    def open(self, key: str) -> BinaryIO:
        try:
            return io.BytesIO(self._blobs[key])
        except KeyError:
            raise FileNotFoundError(key) from None

    def delete(self, key: str) -> None:
        self._blobs.pop(key, None)


_storage: ReportArtifactStorage | None = None


def get_report_storage() -> ReportArtifactStorage:
    """FastAPI dependency returning the process-wide artifact store."""
    global _storage
    if _storage is None:
        from app.core.config import get_settings

        _storage = LocalReportStorage(get_settings().REPORT_STORAGE_DIR)
    return _storage


def build_report_storage(settings: Settings) -> LocalReportStorage:
    """Construct a store from settings without touching the global (used by the
    Celery task, which runs in its own process)."""
    return LocalReportStorage(settings.REPORT_STORAGE_DIR)


def set_report_storage(storage: ReportArtifactStorage | None) -> None:  # pragma: no cover
    """Test helper: pin (or clear) the process-wide store."""
    global _storage
    if storage is None and isinstance(_storage, LocalReportStorage):
        shutil.rmtree(_storage._root, ignore_errors=True)
    _storage = storage
