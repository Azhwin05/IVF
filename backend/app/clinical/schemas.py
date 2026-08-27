import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.clinical.models import TimelineEventType


class ConsultationCreate(BaseModel):
    patient_id: uuid.UUID
    appointment_id: uuid.UUID | None = None
    consultation_type: str
    notes: str


class ConsultationCorrection(BaseModel):
    corrects_consultation_id: uuid.UUID
    notes: str
    correction_reason: str


class ConsultationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    patient_id: uuid.UUID
    doctor_id: uuid.UUID
    consultation_type: str
    notes: str
    created_at: datetime
    corrects_consultation_id: uuid.UUID | None


class TimelineEventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    occurred_at: datetime
    event_type: TimelineEventType
    title: str
    summary: str | None
    source_entity_type: str
    source_entity_id: str
