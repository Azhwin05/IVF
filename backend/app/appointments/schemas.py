import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.appointments.models import AppointmentChannel, AppointmentStatus


class AppointmentCreate(BaseModel):
    patient_id: uuid.UUID
    doctor_id: uuid.UUID
    scheduled_at: datetime
    visit_type: str
    channel: AppointmentChannel


class AppointmentStatusUpdate(BaseModel):
    status: AppointmentStatus
    reason: str | None = None  # required by the service layer for CANCELLED/NO_SHOW


class AppointmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    patient_id: uuid.UUID
    doctor_id: uuid.UUID
    scheduled_at: datetime
    visit_type: str
    channel: AppointmentChannel
    status: AppointmentStatus
    checked_in_at: datetime | None
