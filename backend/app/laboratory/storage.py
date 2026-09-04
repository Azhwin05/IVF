"""Object-storage seam for uploaded lab report documents.

SCOPE NOTE - this is deliberately a small seam, not the platform object store.

The rest of this backend stores binaries in MinIO via ``app.integrations.storage``.
Laboratory report ingestion was built against a minimal three-method interface
with a local-filesystem implementation so it can run (and be tested) without a
MinIO round trip. Callers only ever hold the opaque ``storage_key`` returned by
:meth:`put`; they never build a path or URL. To move report documents into MinIO
later, add a ``MinioObjectStorage`` with the same three methods and swap the
dependency in ``app.laboratory.router`` - nothing else moves, and stored keys
stay valid because they carry no filesystem meaning.
"""

from __future__ import annotations

import io
import shutil
import uuid
from pathlib import Path
from typing import BinaryIO, Protocol

from app.core.config import Settings


class ObjectStorage(Protocol):
    """Minimal blob store: write once, read back, delete."""

    def put(self, data: bytes, *, suffix: str = "") -> str: ...
    def open(self, key: str) -> BinaryIO: ...
    def delete(self, key: str) -> None: ...


class LocalObjectStorage:
    """Filesystem-backed :class:`ObjectStorage` for local dev and the worker.

    Keys are ``<uuid4><suffix>`` and files live directly under ``root``. The key
    is opaque to callers; the layout here is an implementation detail.
    """

    def __init__(self, root: str | Path) -> None:
        self._root = Path(root)
        self._root.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        # Reject any key that tries to escape the root - keys are generated here
        # and never contain separators, so anything else is tampering.
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


class InMemoryObjectStorage:
    """Ephemeral :class:`ObjectStorage` used by the test suite."""

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


_storage: LocalObjectStorage | None = None


def get_object_storage() -> ObjectStorage:
    """FastAPI dependency returning the process-wide storage backend."""
    global _storage
    if _storage is None:
        from app.core.config import get_settings

        _storage = LocalObjectStorage(get_settings().LAB_STORAGE_DIR)
    return _storage


def build_storage(settings: Settings) -> LocalObjectStorage:
    """Construct a backend from settings without touching the global."""
    return LocalObjectStorage(settings.LAB_STORAGE_DIR)


def _reset_for_tests() -> None:  # pragma: no cover - test helper
    global _storage
    if isinstance(_storage, LocalObjectStorage):
        shutil.rmtree(_storage._root, ignore_errors=True)
    _storage = None
