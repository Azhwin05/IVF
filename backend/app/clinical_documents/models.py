"""
Consent forms and MRD (Medical Record Department) documentation — new
requirement (source doc §14). Both are stored as a hospital-supplied
template merged with real patient data, never as legal/medical language
generated here — the source doc is explicit: "Do not invent legal/
medical consent language." `template_id`/`content` are filled in by the
hospital once they provide the actual approved wording (NEEDS HOSPITAL
CONFIRMATION, NEW_FEATURES_GAP_ANALYSIS.md §11); until then this module
has nowhere it silently makes up consent text — creating one requires
passing the content explicitly, which is a visible, obviously-a-stopgap
value at the API boundary rather than a hardcoded default.
"""
import enum
import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import TimestampMixin, UUIDPrimaryKeyMixin
from app.core.database import Base


class ConsentFormStatus(str, enum.Enum):
    DRAFT = "draft"
    SIGNED = "signed"
    WITHDRAWN = "withdrawn"


class ConsentForm(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "consent_forms"

    patient_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False, index=True)
    couple_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("couples.id"), nullable=True)
    form_type: Mapped[str] = mapped_column(String(128), nullable=False)  # e.g. "IVF Treatment Consent", "ICSI Procedure Consent"
    content: Mapped[str] = mapped_column(Text, nullable=False)  # the hospital-approved wording, passed in verbatim — never generated here
    status: Mapped[ConsentFormStatus] = mapped_column(Enum(ConsentFormStatus), default=ConsentFormStatus.DRAFT, index=True)
    signed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)


class MRDRecord(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Deliberately a free-form JSON `fields` blob rather than fixed
    columns — the hospital's approved MRD format is one of the items
    needing confirmation (NEW_FEATURES_GAP_ANALYSIS.md §11); this stores
    whatever structure they specify without this codebase guessing it."""
    __tablename__ = "mrd_records"

    patient_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False, index=True)
    record_type: Mapped[str] = mapped_column(String(128), nullable=False)
    fields: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_by_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
