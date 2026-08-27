"""
Patient + Couple, modeled from the existing frontend's PATIENT/PARTNER
shapes (ARCHITECTURE.md §3). A Couple links two Patients as a treatment
pair without collapsing the partner into a "spouse name" text field —
this was called out explicitly as a design requirement in the original
frontend context doc, and the schema preserves it.
"""
import uuid
from datetime import date

from sqlalchemy import Date, ForeignKey, String, Text
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


class PatientDocument(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Metadata row for a file stored in MinIO — see app/integrations/storage.py.
    The object itself lives in object storage; this row never holds binary data."""
    __tablename__ = "patient_documents"

    patient_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False, index=True)
    couple_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("couples.id"), nullable=True, index=True)

    document_type: Mapped[str] = mapped_column(String(64), nullable=False)  # consent_form, lab_report, id_proof, ...
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_object_key: Mapped[str] = mapped_column(String(512), unique=True, nullable=False)  # randomized, never user input
    content_type: Mapped[str] = mapped_column(String(128), nullable=False)
    size_bytes: Mapped[int] = mapped_column(nullable=False)

    uploaded_by_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    signed: Mapped[bool] = mapped_column(default=False)  # e.g. consent forms
