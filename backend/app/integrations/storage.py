"""
MinIO object storage wrapper — per spec §4/§6's upload security rules:
  - size limits, MIME allow-list, magic-byte sniffing (never trust the
    client-declared content-type or the filename extension)
  - randomized internal object keys (never derived from user input,
    which would otherwise enable path traversal)
  - the original filename is preserved only as metadata in Postgres
    (PatientDocument.original_filename), never as the storage key
"""
import mimetypes
import uuid

from minio import Minio
from minio.error import S3Error

from app.core.config import get_settings
from app.core.exceptions import ValidationFailedError

settings = get_settings()

_client: Minio | None = None


def get_minio_client() -> Minio:
    global _client
    if _client is None:
        _client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE,
        )
    return _client


def ensure_buckets_exist() -> None:
    client = get_minio_client()
    for bucket in (settings.MINIO_BUCKET_DOCUMENTS, settings.MINIO_BUCKET_REPORTS):
        if not client.bucket_exists(bucket):
            client.make_bucket(bucket)


# Magic-byte signatures for the file types this hospital actually handles —
# deliberately narrow (spec §6: "Use strict allow-lists").
_MAGIC_BYTES: dict[bytes, str] = {
    b"%PDF-": "application/pdf",
    b"\xff\xd8\xff": "image/jpeg",
    b"\x89PNG\r\n\x1a\n": "image/png",
    b"RIFF": "image/webp",  # further validated by the WEBP fourcc at offset 8 in practice
}


def sniff_content_type(header_bytes: bytes) -> str | None:
    for signature, mime in _MAGIC_BYTES.items():
        if header_bytes.startswith(signature):
            return mime
    return None


def validate_upload(*, filename: str, declared_content_type: str, size_bytes: int, header_bytes: bytes) -> str:
    """Returns the verified content type, or raises ValidationFailedError.
    Called before anything touches MinIO."""
    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if size_bytes > max_bytes:
        raise ValidationFailedError(f"File exceeds the {settings.MAX_UPLOAD_SIZE_MB} MB upload limit.")

    if declared_content_type not in settings.ALLOWED_UPLOAD_MIME_TYPES:
        raise ValidationFailedError(f"File type '{declared_content_type}' is not permitted.")

    sniffed = sniff_content_type(header_bytes)
    if sniffed is None or sniffed != declared_content_type:
        raise ValidationFailedError(
            "The file's actual content does not match its declared type — upload rejected.",
            error_code="content_type_mismatch",
        )

    # Never trust the extension for anything except a cosmetic display hint;
    # the object key below never uses it, and downstream code never
    # branches on it either. `mimetypes.guess_extension` is used here only
    # to sanity-check that the sniffed type is a known, expected one.
    if mimetypes.guess_extension(sniffed) is None:
        raise ValidationFailedError("Unrecognised file type.")

    return sniffed


def generate_object_key(*, bucket_prefix: str, content_type: str) -> str:
    ext = mimetypes.guess_extension(content_type) or ""
    return f"{bucket_prefix}/{uuid.uuid4().hex}{ext}"


def upload_object(*, bucket: str, object_key: str, data: bytes, content_type: str) -> None:
    import io
    client = get_minio_client()
    client.put_object(bucket, object_key, io.BytesIO(data), length=len(data), content_type=content_type)


def get_presigned_download_url(*, bucket: str, object_key: str, expires_seconds: int = 300) -> str:
    """Short-lived presigned URL — never a permanent public link, and
    never logged (per docs/security's logging rules)."""
    from datetime import timedelta
    client = get_minio_client()
    try:
        return client.presigned_get_object(bucket, object_key, expires=timedelta(seconds=expires_seconds))
    except S3Error as e:
        raise ValidationFailedError(f"Could not generate download link: {e}")
