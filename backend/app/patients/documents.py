"""
Document upload/download endpoints — separated from patients/router.py
to keep the storage-integration concern isolated (patients/router.py
stays about patient CRUD, this file is about the MinIO round-trip).
"""
import uuid

from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.service import record_audit_event
from app.core.config import get_settings
from app.core.database import get_db
from app.core.deps import get_current_user, require_permission
from app.core.exceptions import NotFoundError, PermissionDeniedError
from app.integrations.storage import (
    generate_object_key,
    get_presigned_download_url,
    upload_object,
    validate_upload,
)
from app.patients import service
from app.patients.models import (
    DOCUMENT_TYPE_AADHAAR,
    DOCUMENT_TYPE_PHOTO,
    DOCUMENT_TYPE_VISA,
    Patient,
    PatientDocument,
)
from app.patients.schemas import DocumentVerify, PatientDocumentOut
from app.users.models import User

SENSITIVE_DOCUMENT_TYPES = {DOCUMENT_TYPE_AADHAAR, DOCUMENT_TYPE_VISA}

router = APIRouter(prefix="/patients", tags=["patient-documents"])
settings = get_settings()


@router.get("/{patient_id}/documents", response_model=list[PatientDocumentOut])
async def list_documents(
    patient_id: str,
    session: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("patients.read")),
) -> list[PatientDocument]:
    result = await session.execute(
        select(PatientDocument)
        .where(PatientDocument.patient_id == patient_id)
        .order_by(PatientDocument.created_at.desc())
    )
    return list(result.scalars().all())


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

    if document_type == DOCUMENT_TYPE_PHOTO:
        # New requirement (source doc §4) — the profile photo is stored
        # through the same document pipeline (MinIO + PatientDocument),
        # not a separate blob column; Patient.photo_document_id just
        # points at whichever upload is "the" photo, so re-uploading a
        # photo naturally replaces which one displays without deleting
        # history of the old one.
        patient = await session.get(Patient, patient_id)
        if patient:
            patient.photo_document_id = doc.id

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
    current: User = Depends(get_current_user),
) -> dict:
    doc = await session.get(PatientDocument, document_id)
    if not doc:
        raise NotFoundError("Document not found")

    # New requirement (source doc §4/§30) — Aadhaar/visa need a stricter
    # tier than the general patients.read grant every clinical role has.
    # Checked here rather than as a router-level Depends() because the
    # required permission depends on this specific document's type.
    codes = {p.code for p in current.role.permissions}
    required = "patients.sensitive_documents" if doc.document_type in SENSITIVE_DOCUMENT_TYPES else "patients.read"
    if required not in codes:
        raise PermissionDeniedError(f"Missing required permission: {required}", error_code="permission_denied")

    url = get_presigned_download_url(bucket=settings.MINIO_BUCKET_DOCUMENTS, object_key=doc.storage_object_key)

    await record_audit_event(
        session, actor_id=current.id, actor_role=current.role.code,
        action="patients.document_downloaded", entity_type="PatientDocument", entity_id=str(doc.id),
    )
    return {"url": url, "expires_in_seconds": 300}


@router.post("/documents/{document_id}/verify", response_model=PatientDocumentOut)
async def verify_document(
    document_id: str,
    body: DocumentVerify,
    session: AsyncSession = Depends(get_db),
    current: User = Depends(require_permission("patients.sensitive_documents")),
) -> PatientDocumentOut:
    """New requirement (source doc §4) — Aadhaar/visa verification."""
    return await service.verify_document(
        session, document_id, approve=body.approve, notes=body.notes, actor_id=current.id, actor_role=current.role.code
    )
