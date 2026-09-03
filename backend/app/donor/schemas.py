import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.donor.models import DonorCategory, DonorStatus


class DonorCreate(BaseModel):
    category: DonorCategory
    full_name: str
    contact_phone: str | None = None
    screening_notes: str | None = None


class DonorOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    donor_code: str
    category: DonorCategory
    status: DonorStatus
    full_name: str
    contact_phone: str | None
    screening_notes: str | None
    created_at: datetime


class DonorMatchCreate(BaseModel):
    donor_id: uuid.UUID
    patient_id: uuid.UUID
    couple_id: uuid.UUID | None = None


class DonorMatchEnd(BaseModel):
    reason: str = Field(min_length=3)


class DonorMatchOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    donor_id: uuid.UUID
    patient_id: uuid.UUID
    couple_id: uuid.UUID | None
    is_active: bool
    matched_by_id: uuid.UUID
    matched_at: datetime
    ended_at: datetime | None
    ended_reason: str | None


class DonorBenchmarkCreate(BaseModel):
    donor_id: uuid.UUID
    metric_name: str
    expected_value: float
    actual_value: float
    threshold_percent: float = Field(gt=0, description="Deviation threshold beyond which is_underperforming should be set — hospital-defined per metric, never hardcoded")
    notes: str | None = None


class DonorBenchmarkOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    donor_id: uuid.UUID
    metric_name: str
    expected_value: float
    actual_value: float
    threshold_percent: float
    deviation_percent: float
    is_underperforming: bool
    notes: str | None
    recorded_by_id: uuid.UUID
    created_at: datetime
