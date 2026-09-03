"""Print history — new requirement (client meeting, source doc §5): every
print/export action must record who printed what, for whom, and when.
Previously nothing in the printing module tracked this at all."""
import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import UUIDPrimaryKeyMixin
from app.core.database import Base


class PrintLog(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "print_logs"

    document_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)  # e.g. "id_card", "qr", "invoice", "consent_form"
    patient_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=True, index=True)
    context_entity_type: Mapped[str | None] = mapped_column(String(64), nullable=True)  # e.g. "LabOrder", "Invoice"
    context_entity_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    printed_by_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    printed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
