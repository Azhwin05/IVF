import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class PatientCreate(BaseModel):
    full_name: str
    date_of_birth: date | None = None
    gender: str
    blood_group: str | None = None
    phone: str | None = None
    email: str | None = None
    address: str | None = None
    occupation: str | None = None
    emergency_contact: str | None = None
    referral_source: str | None = None
    allergies: str | None = None


class PatientUpdate(BaseModel):
    full_name: str | None = None
    phone: str | None = None
    email: str | None = None
    address: str | None = None
    occupation: str | None = None
    emergency_contact: str | None = None
    allergies: str | None = None
    primary_doctor_id: uuid.UUID | None = None


# Purpose-specific response shapes, per spec §9/§32 — never a monolithic
# "everything about this patient" endpoint.

class PatientListRow(BaseModel):
    """Powers GET /patients — matches the frontend's PatientRow shape."""
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    uhid: str
    full_name: str
    date_of_birth: date | None
    gender: str
    phone: str | None


class PatientSummary(BaseModel):
    """Powers GET /patients/{id}/summary — the Patient 360 header, not the full history."""
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    uhid: str
    full_name: str
    date_of_birth: date | None
    gender: str
    blood_group: str | None
    phone: str | None
    email: str | None
    allergies: str | None
    created_at: datetime


class CoupleCreate(BaseModel):
    female_patient: PatientCreate
    male_patient: PatientCreate
    relationship_info: str | None = None
    infertility_type: str | None = None
    infertility_duration: str | None = None
    previous_iui_cycles: int = 0
    previous_ivf_cycles: int = 0
    previous_treatment_notes: str | None = None


class CoupleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    female_patient: PatientSummary
    male_patient: PatientSummary
    relationship_info: str | None
    infertility_type: str | None
    infertility_duration: str | None
