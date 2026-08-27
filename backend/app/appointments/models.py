"""
Appointment + patient status flow, from the frontend's BookingSlot shape
and spec §12's queue:
  Registered -> Arrived -> Waiting -> Consultation -> Investigation/Scan/
  Procedure -> Billing -> Pharmacy -> Follow-up -> Completed
"""
import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import TimestampMixin, UUIDPrimaryKeyMixin
from app.core.database import Base


class AppointmentChannel(str, enum.Enum):
    WALK_IN = "walk_in"
    ONLINE = "online"
    PHONE = "phone"


class AppointmentStatus(str, enum.Enum):
    REGISTERED = "registered"
    ARRIVED = "arrived"
    WAITING = "waiting"
    CONSULTATION = "consultation"
    INVESTIGATION = "investigation"
    BILLING = "billing"
    PHARMACY = "pharmacy"
    FOLLOW_UP = "follow_up"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"


# The only status transitions the workflow engine allows — enforced in
# service.py, not just documented. Authorized emergency overrides bypass
# this via a separate, audited code path (see workflow engine, Phase 3).
ALLOWED_TRANSITIONS: dict[AppointmentStatus, set[AppointmentStatus]] = {
    AppointmentStatus.REGISTERED: {AppointmentStatus.ARRIVED, AppointmentStatus.CANCELLED, AppointmentStatus.NO_SHOW},
    AppointmentStatus.ARRIVED: {AppointmentStatus.WAITING, AppointmentStatus.CANCELLED},
    AppointmentStatus.WAITING: {AppointmentStatus.CONSULTATION, AppointmentStatus.CANCELLED},
    AppointmentStatus.CONSULTATION: {AppointmentStatus.INVESTIGATION, AppointmentStatus.BILLING, AppointmentStatus.FOLLOW_UP},
    AppointmentStatus.INVESTIGATION: {AppointmentStatus.BILLING, AppointmentStatus.CONSULTATION},
    AppointmentStatus.BILLING: {AppointmentStatus.PHARMACY, AppointmentStatus.FOLLOW_UP, AppointmentStatus.COMPLETED},
    AppointmentStatus.PHARMACY: {AppointmentStatus.FOLLOW_UP, AppointmentStatus.COMPLETED},
    AppointmentStatus.FOLLOW_UP: {AppointmentStatus.COMPLETED},
    AppointmentStatus.COMPLETED: set(),
    AppointmentStatus.CANCELLED: set(),
    AppointmentStatus.NO_SHOW: set(),
}


class Appointment(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "appointments"

    patient_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False, index=True)
    doctor_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)

    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    visit_type: Mapped[str] = mapped_column(String(128), nullable=False)  # "Follicle Monitoring", "IVF Consultation", ...
    channel: Mapped[AppointmentChannel] = mapped_column(Enum(AppointmentChannel), nullable=False)
    status: Mapped[AppointmentStatus] = mapped_column(
        Enum(AppointmentStatus), nullable=False, default=AppointmentStatus.REGISTERED, index=True
    )

    checked_in_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancellation_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
