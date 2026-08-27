"""
Consultations and the patient timeline — the central read-model
combining events from other modules described in spec §11 ("Patient 360")
and §2.5 of ARCHITECTURE.md.
"""
import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import TimestampMixin, UUIDPrimaryKeyMixin
from app.core.database import Base


class Consultation(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "consultations"

    patient_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False, index=True)
    doctor_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    appointment_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("appointments.id"), nullable=True)

    consultation_type: Mapped[str] = mapped_column(String(128), nullable=False)
    notes: Mapped[str] = mapped_column(Text, nullable=False)

    # A correction never overwrites clinical history in place — it links to
    # what it corrects and both remain readable, per spec §7 ("Clinical and
    # financial corrections should create a new correction/version event
    # rather than silently overwriting important history").
    corrects_consultation_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("consultations.id"), nullable=True)
    correction_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)


class TimelineEventType(str, enum.Enum):
    CONSULTATION = "consultation"
    INVESTIGATION = "investigation"
    STIMULATION_START = "stimulation_start"
    MONITORING_VISIT = "monitoring_visit"
    TRIGGER = "trigger"
    RETRIEVAL = "retrieval"
    EMBRYOLOGY_UPDATE = "embryology_update"
    EMBRYO_TRANSFER = "embryo_transfer"
    PREGNANCY_MILESTONE = "pregnancy_milestone"
    BILLING = "billing"
    DOCUMENT = "document"


class ClinicalTimelineEvent(Base, UUIDPrimaryKeyMixin):
    """Denormalized, append-only projection written to by other modules'
    services (e.g. ivf.service, embryology.service) whenever something
    timeline-worthy happens — powers a single fast query for the Patient
    360 timeline tab instead of joining across eight tables live."""
    __tablename__ = "clinical_timeline_events"

    patient_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False, index=True)
    couple_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("couples.id"), nullable=True, index=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)

    event_type: Mapped[TimelineEventType] = mapped_column(Enum(TimelineEventType), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_entity_type: Mapped[str] = mapped_column(String(64), nullable=False)
    source_entity_id: Mapped[str] = mapped_column(String(64), nullable=False)
