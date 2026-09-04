"""Database access and orchestration for outside-lab report ingestion.

Kept separate from ``app.laboratory.service`` (lab orders / hand-entered
results) so the two concerns stay decoupled. Everything here operates on
``LabReport`` / ``LabReportResult`` / ``LabReportResultCorrection`` only.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from app.core.config import Settings
from app.core.exceptions import ConflictError, NotFoundError, ValidationFailedError
from app.core.pagination import paginate
from app.laboratory.extraction import extract_document
from app.laboratory.models import (
    CorrectionField,
    EntryOrigin,
    ExtractionMethod,
    ExtractionStatus,
    LabReport,
    LabReportResult,
    LabReportResultCorrection,
    NormalizationMatch,
    ResultValidationStatus,
)
from app.laboratory.report_schemas import (
    LabReportResultCorrectionRequest,
    LabReportResultManualCreate,
)
from app.laboratory.storage import ObjectStorage
from app.patients.models import Patient

_CORRECTABLE_FIELDS: tuple[str, ...] = ("test_name", "value", "unit", "reference_range")

_SUFFIX_BY_TYPE = {
    "application/pdf": ".pdf",
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "image/tiff": ".tif",
}


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _suffix_for(filename: str, content_type: str) -> str:
    if "." in filename:
        return filename[filename.rindex(".") :][:12]
    return _SUFFIX_BY_TYPE.get(content_type.lower(), "")


async def _patient_exists(session: AsyncSession, patient_id: UUID) -> bool:
    return (
        await session.execute(sa.select(Patient.id).where(Patient.id == patient_id))
    ).scalar_one_or_none() is not None


async def _load_report(session: AsyncSession, report_id: UUID) -> LabReport | None:
    result = await session.execute(
        sa.select(LabReport)
        .options(joinedload(LabReport.patient), selectinload(LabReport.results))
        .where(LabReport.id == report_id)
    )
    return result.unique().scalar_one_or_none()


async def create_report(
    session: AsyncSession,
    storage: ObjectStorage,
    *,
    patient_id: UUID,
    filename: str,
    content_type: str,
    data: bytes,
) -> LabReport:
    if not data:
        raise ValidationFailedError("The uploaded file is empty.")

    if not await _patient_exists(session, patient_id):
        raise ValidationFailedError(
            "That patient does not exist. Choose a registered patient."
        )

    digest = hashlib.sha256(data).hexdigest()
    existing = await session.execute(
        sa.select(LabReport.id).where(
            LabReport.patient_id == patient_id, LabReport.document_sha256 == digest
        )
    )
    if existing.scalar_one_or_none() is not None:
        raise ConflictError("This exact document has already been uploaded for this patient.")

    storage_key = storage.put(data, suffix=_suffix_for(filename, content_type))

    report = LabReport(
        patient_id=patient_id,
        original_filename=filename[:255],
        content_type=(content_type or "application/octet-stream")[:120],
        byte_size=len(data),
        storage_key=storage_key,
        document_sha256=digest,
        extraction_status=ExtractionStatus.pending,
        extraction_method=ExtractionMethod.none,
    )
    session.add(report)
    try:
        await session.commit()
    except IntegrityError:  # pragma: no cover - storage keys are unique by construction
        await session.rollback()
        storage.delete(storage_key)
        raise ConflictError("The document could not be stored. Try again.") from None

    loaded = await _load_report(session, report.id)
    assert loaded is not None
    return loaded


async def get_report(session: AsyncSession, report_id: UUID) -> LabReport | None:
    return await _load_report(session, report_id)


async def list_reports(
    session: AsyncSession,
    *,
    limit: int,
    cursor: str | None = None,
    patient_id: UUID | None = None,
) -> tuple[list[LabReport], str | None, bool]:
    stmt = sa.select(LabReport).options(joinedload(LabReport.patient))
    if patient_id is not None:
        stmt = stmt.where(LabReport.patient_id == patient_id)
    return await paginate(session, stmt, model=LabReport, cursor=cursor, limit=limit)


async def get_report_document(
    session: AsyncSession, storage: ObjectStorage, report_id: UUID
) -> tuple[LabReport, bytes] | None:
    report = await _load_report(session, report_id)
    if report is None:
        return None
    try:
        with storage.open(report.storage_key) as fh:
            return report, fh.read()
    except FileNotFoundError:
        raise NotFoundError("The stored document is missing.") from None


async def run_extraction(
    session: AsyncSession,
    storage: ObjectStorage,
    settings: Settings,
    report_id: UUID,
) -> LabReport:
    report = await _load_report(session, report_id)
    if report is None:
        raise NotFoundError("Lab report not found.")

    try:
        with storage.open(report.storage_key) as fh:
            data = fh.read()
    except FileNotFoundError:
        raise NotFoundError("The stored document is missing.") from None

    outcome = extract_document(
        data,
        filename=report.original_filename,
        content_type=report.content_type,
        settings=settings,
    )

    # Replace any prior extracted rows; hand-entered rows are kept.
    await session.execute(
        sa.delete(LabReportResult).where(
            LabReportResult.report_id == report.id,
            LabReportResult.entry_origin == EntryOrigin.extracted,
        )
    )

    report.document_kind = outcome.document_kind
    report.extraction_method = outcome.method
    report.page_count = outcome.page_count
    report.extracted_at = _utcnow()

    if outcome.error:
        report.extraction_status = ExtractionStatus.failed
        report.extraction_error = outcome.error[:500]
    else:
        report.extraction_status = ExtractionStatus.completed
        report.extraction_error = None
        for row in outcome.rows:
            session.add(
                LabReportResult(
                    report_id=report.id,
                    test_name=row.test_name,
                    value=row.value,
                    unit=row.unit,
                    reference_range=row.reference_range,
                    extracted_test_name=row.test_name,
                    extracted_value=row.value,
                    extracted_unit=row.unit,
                    extracted_reference_range=row.reference_range,
                    entry_origin=EntryOrigin.extracted,
                    normalization_match=row.normalization_match,
                    normalization_note=row.normalization_note,
                    validation_status=row.validation_status,
                    validation_notes=list(row.validation_notes),
                    source_snippet=row.source_snippet,
                    source_location=row.source_location,
                    confidence=row.confidence,
                )
            )

    await session.commit()
    # Detach identity-map copies so the reload builds fresh instances (the
    # statement-level DELETE above does not update already-loaded collections).
    session.expunge_all()
    loaded = await _load_report(session, report.id)
    assert loaded is not None
    return loaded


async def get_result(session: AsyncSession, result_id: UUID) -> LabReportResult | None:
    result = await session.execute(
        sa.select(LabReportResult)
        .options(selectinload(LabReportResult.corrections))
        .where(LabReportResult.id == result_id)
    )
    return result.scalar_one_or_none()


def _manual_status(payload: LabReportResultManualCreate) -> ResultValidationStatus:
    if payload.value is None or not str(payload.value).strip():
        return ResultValidationStatus.not_extracted
    return ResultValidationStatus.ok


async def add_manual_result(
    session: AsyncSession, report_id: UUID, payload: LabReportResultManualCreate
) -> LabReportResult:
    exists = await session.execute(sa.select(LabReport.id).where(LabReport.id == report_id))
    if exists.scalar_one_or_none() is None:
        raise NotFoundError("Lab report not found.")

    result = LabReportResult(
        report_id=report_id,
        test_name=payload.test_name,
        value=payload.value,
        unit=payload.unit,
        reference_range=payload.reference_range,
        # No extracted_* snapshot: this row was never extracted.
        entry_origin=EntryOrigin.manual,
        normalization_match=NormalizationMatch.manual,
        validation_status=_manual_status(payload),
        validation_notes=[],
    )
    session.add(result)
    await session.commit()
    loaded = await get_result(session, result.id)
    assert loaded is not None
    return loaded


async def correct_result(
    session: AsyncSession,
    result_id: UUID,
    payload: LabReportResultCorrectionRequest,
    *,
    corrected_by_id: UUID,
) -> LabReportResult:
    result = await get_result(session, result_id)
    if result is None:
        raise NotFoundError("Lab result not found.")

    changed = [f for f in _CORRECTABLE_FIELDS if f in payload.model_fields_set]
    if not changed:
        raise ValidationFailedError("Provide at least one field to correct.")

    made_a_change = False
    for field in changed:
        new_value = getattr(payload, field)
        current = getattr(result, field)
        if new_value == current:
            continue
        result.corrections.append(
            LabReportResultCorrection(
                field=CorrectionField(field),
                previous_value=current,
                new_value=new_value,
                corrected_by_id=corrected_by_id,
                reason=payload.reason,
            )
        )
        setattr(result, field, new_value)
        made_a_change = True

    if not made_a_change:
        raise ValidationFailedError("The supplied values match the current values.")

    await session.commit()
    loaded = await get_result(session, result.id)
    assert loaded is not None
    return loaded


async def list_corrections(
    session: AsyncSession, result_id: UUID
) -> list[LabReportResultCorrection]:
    exists = await session.execute(
        sa.select(LabReportResult.id).where(LabReportResult.id == result_id)
    )
    if exists.scalar_one_or_none() is None:
        raise NotFoundError("Lab result not found.")
    rows = await session.execute(
        sa.select(LabReportResultCorrection)
        .where(LabReportResultCorrection.result_id == result_id)
        .order_by(LabReportResultCorrection.created_at, LabReportResultCorrection.id)
    )
    return list(rows.scalars().all())
