"""
Patient + Couple, modeled from the existing frontend's PATIENT/PARTNER
shapes (ARCHITECTURE.md §3). A Couple links two Patients as a treatment
pair without collapsing the partner into a "spouse name" text field —
this was called out explicitly as a design requirement in the original
frontend context doc, and the schema preserves it.
"""
import enum
import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base_model import TimestampMixin, UUIDPrimaryKeyMixin
from app.core.database import Base


class Patient(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "patients"

    uhid: Mapped[str] = mapped_column(String(32), unique=True, nullable=False, index=True)  # DAIVF-YYYY-NNNNN
    full_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    date_of_birth: Mapped[date | None] = mapped_column(Date, nullable=True)
    gender: Mapped[str] = mapped_column(String(16), nullable=False)
    blood_group: Mapped[str | None] = mapped_column(String(16), nullable=True)  # e.g. "B Positive"

    # New requirement (source doc §4) — nothing distinguished an Indian
    # from an international patient before this, which is what the
    # mandatory-Aadhaar / mandatory-visa rule needs to key off of.
    # NEEDS HOSPITAL CONFIRMATION: exact registration field list — see
    # NEW_FEATURES_GAP_ANALYSIS.md §1. `nationality` is free text (e.g.
    # "Indian", "British") rather than an ISO country enum, since the only
    # confirmed rule so far is the binary Indian/international split.
    nationality: Mapped[str | None] = mapped_column(String(64), nullable=True)
    is_international: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    # use_alter + a name: patients -> patient_documents -> patients would
    # otherwise be a hard circular FK dependency (patient_documents.patient_id
    # already points back at patients), which breaks SQLAlchemy's
    # create_all/drop_all table ordering (confirmed by the test suite).
    # use_alter defers this specific constraint to a separate ALTER TABLE
    # after both tables exist, breaking the cycle without changing any
    # runtime behavior.
    photo_document_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("patient_documents.id", use_alter=True, name="fk_patients_photo_document_id"),
        nullable=True,
    )

    phone: Mapped[str | None] = mapped_column(String(20), nullable=True, index=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)

    occupation: Mapped[str | None] = mapped_column(String(128), nullable=True)
    emergency_contact: Mapped[str | None] = mapped_column(String(255), nullable=True)
    referral_source: Mapped[str | None] = mapped_column(String(255), nullable=True)
    allergies: Mapped[str | None] = mapped_column(Text, nullable=True)

    primary_doctor_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)


class Couple(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """A treatment case linking two patients as partners."""
    __tablename__ = "couples"

    female_patient_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False, unique=True)
    male_patient_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False, unique=True)

    female_patient: Mapped["Patient"] = relationship(foreign_keys=[female_patient_id], lazy="selectin")
    male_patient: Mapped["Patient"] = relationship(foreign_keys=[male_patient_id], lazy="selectin")

    relationship_info: Mapped[str | None] = mapped_column(String(255), nullable=True)  # "Married — 6 Years"
    infertility_type: Mapped[str | None] = mapped_column(String(64), nullable=True)  # Primary / Secondary
    infertility_duration: Mapped[str | None] = mapped_column(String(64), nullable=True)
    previous_iui_cycles: Mapped[int] = mapped_column(default=0)
    previous_ivf_cycles: Mapped[int] = mapped_column(default=0)
    previous_treatment_notes: Mapped[str | None] = mapped_column(Text, nullable=True)


class DocumentVerificationStatus(str, enum.Enum):
    NOT_REQUIRED = "not_required"
    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"


# New requirement (source doc §4) — document_type stays a plain string
# column (unchanged, for backward compatibility with existing rows and
# other document types this list doesn't try to be exhaustive about),
# but Aadhaar/visa/photo are now named constants the backend validates
# against for the mandatory-document rule, instead of every caller
# guessing a spelling.
DOCUMENT_TYPE_AADHAAR = "aadhaar"
DOCUMENT_TYPE_VISA = "visa"
DOCUMENT_TYPE_PHOTO = "photo"


class PatientDocument(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Metadata row for a file stored in MinIO — see app/integrations/storage.py.
    The object itself lives in object storage; this row never holds binary data."""
    __tablename__ = "patient_documents"

    patient_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False, index=True)
    couple_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("couples.id"), nullable=True, index=True)

    document_type: Mapped[str] = mapped_column(String(64), nullable=False)  # consent_form, lab_report, id_proof, aadhaar, visa, photo, ...
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_object_key: Mapped[str] = mapped_column(String(512), unique=True, nullable=False)  # randomized, never user input
    content_type: Mapped[str] = mapped_column(String(128), nullable=False)
    size_bytes: Mapped[int] = mapped_column(nullable=False)

    uploaded_by_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    signed: Mapped[bool] = mapped_column(default=False)  # e.g. consent forms

    # New requirement (source doc §4/§5) — verification tracking, distinct
    # from the existing generic audit trail so "which documents still need
    # front-desk review" can be queried directly.
    verification_status: Mapped[DocumentVerificationStatus] = mapped_column(
        Enum(DocumentVerificationStatus), default=DocumentVerificationStatus.NOT_REQUIRED, index=True
    )
    verified_by_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class VisaSupportStatus(str, enum.Enum):
    REQUESTED = "requested"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class VisaSupportRequest(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """New requirement (source doc §4) — the hospital provides visa support
    to international patients; this tracks that as its own auditable
    workflow rather than a free-text note somewhere."""
    __tablename__ = "visa_support_requests"

    patient_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False, index=True)
    request_type: Mapped[str] = mapped_column(String(128), nullable=False)  # e.g. "invitation_letter", "extension_support"
    status: Mapped[VisaSupportStatus] = mapped_column(Enum(VisaSupportStatus), default=VisaSupportStatus.REQUESTED, index=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    handled_by_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
