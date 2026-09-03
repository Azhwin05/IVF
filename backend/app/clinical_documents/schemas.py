import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.clinical_documents.models import ConsentFormStatus


class ConsentFormCreate(BaseModel):
    patient_id: uuid.UUID
    couple_id: uuid.UUID | None = None
    form_type: str
    content: str  # hospital-approved wording, passed in verbatim — never generated server-side


class ConsentFormSign(BaseModel):
    pass


class ConsentFormOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    patient_id: uuid.UUID
    couple_id: uuid.UUID | None
    form_type: str
    content: str
    status: ConsentFormStatus
    signed_at: datetime | None
    created_by_id: uuid.UUID
    created_at: datetime


class MRDRecordCreate(BaseModel):
    patient_id: uuid.UUID
    record_type: str
    fields: dict


class MRDRecordOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    patient_id: uuid.UUID
    record_type: str
    fields: dict
    created_by_id: uuid.UUID
    created_at: datetime
