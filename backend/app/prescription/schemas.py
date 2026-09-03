import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class PrescriptionLineCreate(BaseModel):
    medicine_id: uuid.UUID | None = None
    medicine_name: str
    dosage: str
    frequency: str
    timing: str | None = None
    duration: str | None = None
    instructions: str | None = None


class PrescriptionCreate(BaseModel):
    patient_id: uuid.UUID
    cycle_id: uuid.UUID | None = None
    category: str | None = None
    notes: str | None = None
    lines: list[PrescriptionLineCreate]


class PrescriptionLineOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    medicine_id: uuid.UUID | None
    medicine_name: str
    dosage: str
    frequency: str
    timing: str | None
    duration: str | None
    instructions: str | None


class PrescriptionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    patient_id: uuid.UUID
    cycle_id: uuid.UUID | None
    prescribed_by_id: uuid.UUID
    category: str | None
    notes: str | None
    created_at: datetime
    lines: list[PrescriptionLineOut]
