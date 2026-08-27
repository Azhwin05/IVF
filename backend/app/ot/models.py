"""OT/procedure scheduling and readiness checklists, per spec §17/§18."""
import enum
import uuid
from datetime import date, datetime

from sqlalchemy import JSON, Boolean, Date, DateTime, Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import TimestampMixin, UUIDPrimaryKeyMixin
from app.core.database import Base


class ProcedureStatus(str, enum.Enum):
    SCHEDULED = "scheduled"
    PREPARATION = "preparation"
    READY = "ready"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Procedure(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "procedures"

    patient_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False, index=True)
    cycle_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("ivf_cycles.id"), nullable=True)
    procedure_type: Mapped[str] = mapped_column(String(128), nullable=False)  # "Oocyte Retrieval", "Embryo Transfer"
    ot_room: Mapped[str] = mapped_column(String(64), nullable=False)

    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    doctor_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    nurse_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    embryologist_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    consent_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[ProcedureStatus] = mapped_column(Enum(ProcedureStatus), default=ProcedureStatus.SCHEDULED, index=True)


class ReadinessChecklist(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Daily departmental readiness checklists, per spec §18 (OT, Scan,
    Laboratory, Cryostorage). A new instance is generated each day, never
    reused — see app/workers/tasks.py's daily checklist generation job."""
    __tablename__ = "readiness_checklists"

    department: Mapped[str] = mapped_column(String(64), nullable=False, index=True)  # "OT", "Scan", "Laboratory", "Cryostorage"
    checklist_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    items: Mapped[list] = mapped_column(JSON, nullable=False, default=list)  # [{item, status, checked_by, checked_time, issue}]
    verified_by_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
