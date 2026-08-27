import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class CryoLocationCreate(BaseModel):
    tank: str
    canister: str
    cane: str
    goblet: str
    straw: str
    embryo_id: uuid.UUID
    frozen_at: date
    consent_verified: bool = False
    renewal_due: date | None = None


class CryoLocationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    tank: str
    canister: str
    cane: str
    goblet: str
    straw: str
    embryo_id: uuid.UUID | None
    frozen_at: date | None
    consent_verified: bool
    renewal_due: date | None
    is_active: bool


class CustodyEventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    event_type: str
    performed_by_id: uuid.UUID
    witnessed_by_id: uuid.UUID | None
    occurred_at: datetime
    notes: str | None


class CryoMoveRequest(BaseModel):
    location_id: uuid.UUID
    new_tank: str
    new_canister: str
    new_cane: str
    new_goblet: str
    new_straw: str
    witnessed_by_id: uuid.UUID
    notes: str | None = None


class TransferCreate(BaseModel):
    cycle_id: uuid.UUID
    embryo_id: uuid.UUID
    procedure_doctor_id: uuid.UUID
    embryologist_id: uuid.UUID
    transfer_date: date


class ChecklistItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    item_code: str
    label: str
    checked: bool
    checked_by_id: uuid.UUID | None
    checked_at: datetime | None


class TransferOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    cycle_id: uuid.UUID
    embryo_id: uuid.UUID
    transfer_date: date
    completed: bool
    checklist: list[ChecklistItemOut]
