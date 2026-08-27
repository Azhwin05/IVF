"""Preventive/corrective maintenance, AMC, calibration — spec §21."""
import enum
import uuid
from datetime import date

from sqlalchemy import Date, Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import TimestampMixin, UUIDPrimaryKeyMixin
from app.core.database import Base


class MaintenanceType(str, enum.Enum):
    PREVENTIVE = "preventive"
    CORRECTIVE = "corrective"
    AMC_RENEWAL = "amc_renewal"
    CALIBRATION = "calibration"


class MaintenanceStatus(str, enum.Enum):
    SCHEDULED = "scheduled"
    DUE = "due"
    COMPLETED = "completed"
    OVERDUE = "overdue"


class MaintenanceTask(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "maintenance_tasks"

    equipment_name: Mapped[str] = mapped_column(String(255), nullable=False)  # "Generator", "HVAC", asset name, ...
    asset_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("assets.id"), nullable=True)
    task_type: Mapped[MaintenanceType] = mapped_column(Enum(MaintenanceType), nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    status: Mapped[MaintenanceStatus] = mapped_column(Enum(MaintenanceStatus), default=MaintenanceStatus.SCHEDULED, index=True)

    assigned_to_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    completed_by_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    completed_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
