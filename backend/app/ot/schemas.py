import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict

from app.ot.models import ProcedureStatus


class ProcedureCreate(BaseModel):
    patient_id: uuid.UUID
    cycle_id: uuid.UUID | None = None
    procedure_type: str
    ot_room: str
    scheduled_at: datetime
    doctor_id: uuid.UUID
    nurse_id: uuid.UUID | None = None
    embryologist_id: uuid.UUID | None = None


class ProcedureStatusUpdate(BaseModel):
    status: ProcedureStatus


class ProcedureOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    patient_id: uuid.UUID
    procedure_type: str
    ot_room: str
    scheduled_at: datetime
    consent_verified: bool
    status: ProcedureStatus


class ChecklistItem(BaseModel):
    item: str
    status: str = "pending"  # pending, ok, issue
    checked_by: str | None = None
    checked_time: str | None = None
    issue: str | None = None


class ChecklistCreate(BaseModel):
    department: str
    checklist_date: date
    items: list[ChecklistItem]


class ChecklistOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    department: str
    checklist_date: date
    items: list[dict]
    verified_by_id: uuid.UUID | None
