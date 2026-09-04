import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base_model import TimestampMixin, UUIDPrimaryKeyMixin
from app.core.database import Base
# Imported (not a string forward-ref) so `LabReport.patient` resolves even when
# a narrow entrypoint - e.g. scripts/seed_db.py - configures the laboratory
# mappers before app.patients.models has been imported. `patients` never
# imports `laboratory`, so there is no cycle.
from app.patients.models import Patient


class LabOrderSource(str, enum.Enum):
    INTERNAL = "internal_lab"
    EXTERNAL = "external_lab"


class LabOrderStatus(str, enum.Enum):
    ORDERED = "ordered"
    SAMPLE_COLLECTED = "sample_collected"
    IN_PROGRESS = "in_progress"
    REPORT_READY = "report_ready"
    DELIVERED = "delivered"


class LabOrderPriority(str, enum.Enum):
    ROUTINE = "routine"
    URGENT = "urgent"


class LabTestCatalogueItem(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "lab_test_catalogue"

    test_name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    price_paise: Mapped[int] = mapped_column(Integer, nullable=False)
    turnaround_time: Mapped[str] = mapped_column(String(64), nullable=False)  # "24 hrs"
    sample_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class LabOrder(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "lab_orders"

    order_number: Mapped[str] = mapped_column(String(32), unique=True, nullable=False, index=True)
    patient_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False, index=True)
    test_catalogue_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("lab_test_catalogue.id"), nullable=True)
    test_name: Mapped[str] = mapped_column(String(255), nullable=False)

    ordered_by_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    sample_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    source: Mapped[LabOrderSource] = mapped_column(Enum(LabOrderSource), default=LabOrderSource.INTERNAL)
    external_lab_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    priority: Mapped[LabOrderPriority] = mapped_column(Enum(LabOrderPriority), default=LabOrderPriority.ROUTINE)
    status: Mapped[LabOrderStatus] = mapped_column(Enum(LabOrderStatus), default=LabOrderStatus.ORDERED, index=True)

    result_document_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("patient_documents.id"), nullable=True)
    result_verified_by_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    result_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class LabResultFlag(str, enum.Enum):
    NORMAL = "normal"
    LOW = "low"
    HIGH = "high"
    CRITICAL = "critical"


class LabResult(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Structured, chartable result values — new requirement (source doc §6):
    previously a lab order's result existed only as an attached file
    (`LabOrder.result_document_id`), so nothing in the system could show a
    single numeric value like 'AMH: 2.4 ng/mL'. One order can have many
    parameters (e.g. a hormonal panel), hence a separate table rather than
    columns on LabOrder."""
    __tablename__ = "lab_results"

    order_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("lab_orders.id"), nullable=False, index=True)
    parameter_name: Mapped[str] = mapped_column(String(255), nullable=False)  # e.g. "AMH", "FSH", "Lead Follicle"
    value: Mapped[str] = mapped_column(String(64), nullable=False)  # kept as string — some params are qualitative ("Normal cavity")
    unit: Mapped[str | None] = mapped_column(String(32), nullable=True)
    reference_range: Mapped[str | None] = mapped_column(String(64), nullable=True)  # e.g. "1.0 – 4.0"
    flag: Mapped[LabResultFlag] = mapped_column(Enum(LabResultFlag), default=LabResultFlag.NORMAL)
    entered_by_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)


# ===========================================================================
# Outside-lab report ingestion (uploaded PDF/scan/image -> OCR / PDF-text
# extraction -> layout-aware parsing -> normalization -> validation ->
# structured, reviewable results with an append-only correction trail).
#
# This is a SEPARATE concern from LabOrder/LabResult above (which model
# ordering an internal/external test and hand-entering its parameters):
#   * LabOrder / LabResult          -> "we ordered a test, here are its values"
#   * LabReport / LabReportResult   -> "an outside lab sent us a document, here
#                                       is what we could read off it, and every
#                                       correction a human made afterwards"
# The two never share a table. A future enhancement may link a LabReport to a
# LabOrder, but that FK is intentionally not added yet.
# ===========================================================================


class DocumentKind(str, enum.Enum):
    digital_pdf = "digital_pdf"
    scanned_pdf = "scanned_pdf"
    image = "image"
    unknown = "unknown"


class ExtractionStatus(str, enum.Enum):
    pending = "pending"        # uploaded, extraction not yet run
    processing = "processing"  # extraction in progress
    completed = "completed"    # extraction ran (rows carry their own status)
    failed = "failed"          # extraction could not run at all; no rows invented


class ExtractionMethod(str, enum.Enum):
    native_pdf_text = "native_pdf_text"
    ocr = "ocr"
    ai_vision = "ai_vision"
    manual = "manual"
    none = "none"


class EntryOrigin(str, enum.Enum):
    extracted = "extracted"  # produced by the extraction pipeline
    manual = "manual"        # added by a person


class NormalizationMatch(str, enum.Enum):
    exact_alias = "exact_alias"  # test name mapped through the curated alias table
    unmatched = "unmatched"      # left as extracted; candidates may be suggested
    manual = "manual"            # set by a person


class ResultValidationStatus(str, enum.Enum):
    ok = "ok"
    needs_review = "needs_review"
    not_extracted = "not_extracted"  # "Not extracted - please enter manually."


class CorrectionField(str, enum.Enum):
    test_name = "test_name"
    value = "value"
    unit = "unit"
    reference_range = "reference_range"


class LabReport(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "lab_reports"

    patient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        # RESTRICT: a patient with lab history is never removed out from under it.
        ForeignKey("patients.id", ondelete="RESTRICT"),
        nullable=False,
    )

    # Uploaded document metadata. The binary lives in the object-storage seam
    # (app/laboratory/storage.py); this row only ever holds the opaque key.
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[str] = mapped_column(String(120), nullable=False)
    byte_size: Mapped[int] = mapped_column(Integer, nullable=False)
    storage_key: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    document_sha256: Mapped[str] = mapped_column(String(64), nullable=False)

    document_kind: Mapped[DocumentKind] = mapped_column(
        Enum(DocumentKind, name="lab_document_kind"),
        nullable=False,
        default=DocumentKind.unknown,
    )
    extraction_status: Mapped[ExtractionStatus] = mapped_column(
        Enum(ExtractionStatus, name="lab_extraction_status"),
        nullable=False,
        default=ExtractionStatus.pending,
    )
    extraction_method: Mapped[ExtractionMethod] = mapped_column(
        Enum(ExtractionMethod, name="lab_extraction_method"),
        nullable=False,
        default=ExtractionMethod.none,
    )
    extraction_error: Mapped[str | None] = mapped_column(String(500), nullable=True)
    page_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    extracted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # lazy="raise": a patient is only ever loaded through an explicit join.
    patient: Mapped[Patient] = relationship(Patient, lazy="raise")
    results: Mapped[list["LabReportResult"]] = relationship(
        back_populates="report",
        cascade="all, delete-orphan",
        order_by="LabReportResult.created_at, LabReportResult.id",
        lazy="raise",
    )

    __table_args__ = (
        Index(
            "ix_lab_reports_created_at_id",
            text("created_at DESC"),
            text("id DESC"),
        ),
        Index("ix_lab_reports_patient_created_at", "patient_id", text("created_at DESC")),
    )


class LabReportResult(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "lab_report_results"

    report_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("lab_reports.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Current values - what the review screen shows and edits. Any of these may
    # be NULL: a field that could not be read is left empty, never guessed.
    test_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    value: Mapped[str | None] = mapped_column(String(120), nullable=True)
    unit: Mapped[str | None] = mapped_column(String(60), nullable=True)
    reference_range: Mapped[str | None] = mapped_column(String(120), nullable=True)

    # Immutable snapshot of exactly what extraction produced. Written once, never
    # updated. NULL on every field when the row was added by hand. This is what
    # guarantees a correction can never destroy the original extracted value.
    extracted_test_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    extracted_value: Mapped[str | None] = mapped_column(String(120), nullable=True)
    extracted_unit: Mapped[str | None] = mapped_column(String(60), nullable=True)
    extracted_reference_range: Mapped[str | None] = mapped_column(String(120), nullable=True)

    entry_origin: Mapped[EntryOrigin] = mapped_column(
        Enum(EntryOrigin, name="lab_entry_origin"), nullable=False
    )
    normalization_match: Mapped[NormalizationMatch] = mapped_column(
        Enum(NormalizationMatch, name="lab_normalization_match"),
        nullable=False,
        default=NormalizationMatch.unmatched,
    )
    normalization_note: Mapped[str | None] = mapped_column(String(300), nullable=True)

    validation_status: Mapped[ResultValidationStatus] = mapped_column(
        Enum(ResultValidationStatus, name="lab_result_validation_status"),
        nullable=False,
        default=ResultValidationStatus.needs_review,
    )
    validation_notes: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)

    source_snippet: Mapped[str | None] = mapped_column(String(500), nullable=True)
    source_location: Mapped[str | None] = mapped_column(String(120), nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)

    report: Mapped[LabReport] = relationship(back_populates="results", lazy="raise")
    corrections: Mapped[list["LabReportResultCorrection"]] = relationship(
        back_populates="result",
        cascade="all, delete-orphan",
        order_by="LabReportResultCorrection.created_at",
        lazy="raise",
    )

    __table_args__ = (
        Index("ix_lab_report_results_report_id_id", "report_id", "id"),
    )


class LabReportResultCorrection(Base, UUIDPrimaryKeyMixin):
    """One field of one result, changed by one person. Append-only.

    Deliberately not TimestampMixin: it has no ``updated_at`` (rows are never
    updated), and its ``created_at`` is set statement-side with microsecond
    precision so the history sorts reliably in insert order even when several
    corrections land inside one request/transaction (a server-side
    ``func.now()`` returns the transaction start time - identical for every row
    in the batch - and would leave the order undefined).
    """

    __tablename__ = "lab_report_result_corrections"

    result_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("lab_report_results.id", ondelete="CASCADE"),
        nullable=False,
    )

    field: Mapped[CorrectionField] = mapped_column(
        Enum(CorrectionField, name="lab_correction_field"), nullable=False
    )
    previous_value: Mapped[str | None] = mapped_column(String(200), nullable=True)
    new_value: Mapped[str | None] = mapped_column(String(200), nullable=True)

    corrected_by_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    reason: Mapped[str | None] = mapped_column(String(300), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    result: Mapped[LabReportResult] = relationship(back_populates="corrections", lazy="raise")

    __table_args__ = (
        Index(
            "ix_lab_report_result_corrections_result_id_created_at",
            "result_id",
            "created_at",
        ),
    )
