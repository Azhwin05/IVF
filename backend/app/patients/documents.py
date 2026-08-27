"""
Document upload/download endpoints — separated from patients/router.py
to keep the storage-integration concern isolated (patients/router.py
stays about patient CRUD, this file is about the MinIO round-trip).
"""
import uuid

from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.service import record_audit_event
from app.core.config import get_settings
from app.core.database import get_db
from app.core.deps import require_permission
from app.core.exceptions import NotFoundError
from app.integrations.storage import (
    generate_object_key,
    get_presigned_download_url,
    upload_object,
    validate_upload,
)
from app.patients.models import PatientDocument
from app.users.models import User

router = APIRouter(prefix="/patients", tags=["patient-documents"])
settings = get_settings()


@router.post("/{patient_id}/documents", status_code=201)
async def upload_document(
    patient_id: str,
    document_type: str,
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_db),
    current: User = Depends(require_permission("patients.update")),
) -> dict:
    contents = await file.read()
    verified_type = validate_upload(
        filename=file.filename or "upload",
        declared_content_type=file.content_type or "application/octet-stream",
        size_bytes=len(contents),
        header_bytes=contents[:16],
    )

    object_key = generate_object_key(bucket_prefix=f"patients/{patient_id}", content_type=verified_type)
    upload_object(
        bucket=settings.MINIO_BUCKET_DOCUMENTS, object_key=object_key, data=contents, content_type=verified_type
    )

    doc = PatientDocument(
        patient_id=patient_id,
        document_type=document_type,
        original_filename=file.filename or "upload",
        storage_object_key=object_key,
        content_type=verified_type,
        size_bytes=len(contents),
        uploaded_by_id=current.id,
    )
    session.add(doc)
    await session.flush()

    await record_audit_event(
        session, actor_id=current.id, actor_role=current.role.code,
        action="patients.document_uploaded", entity_type="PatientDocument", entity_id=str(doc.id),
        after_state={"document_type": document_type, "size_bytes": len(contents)},
    )
    return {"id": str(doc.id), "document_type": document_type, "filename": doc.original_filename}


@router.get("/documents/{document_id}/download-url")
async def get_download_url(
    document_id: str,
    session: AsyncSession = Depends(get_db),
    current: User = Depends(require_permission("patients.read")),
) -> dict:
    doc = await session.get(PatientDocument, document_id)
    if not doc:
        raise NotFoundError("Document not found")

    url = get_presigned_download_url(bucket=settings.MINIO_BUCKET_DOCUMENTS, object_key=doc.storage_object_key)

    await record_audit_event(
        session, actor_id=current.id, actor_role=current.role.code,
        action="patients.document_downloaded", entity_type="PatientDocument", entity_id=str(doc.id),
    )
    return {"url": url, "expires_in_seconds": 300}
