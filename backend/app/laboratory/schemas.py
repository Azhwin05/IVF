import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.laboratory.models import LabOrderPriority, LabOrderSource, LabOrderStatus, LabResultFlag


class LabOrderCreate(BaseModel):
    patient_id: uuid.UUID
    test_name: str
    test_catalogue_id: uuid.UUID | None = None
    sample_type: str | None = None
    source: LabOrderSource = LabOrderSource.INTERNAL
    external_lab_name: str | None = None
    priority: LabOrderPriority = LabOrderPriority.ROUTINE


class LabOrderStatusUpdate(BaseModel):
    status: LabOrderStatus


class LabOrderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    order_number: str
    patient_id: uuid.UUID
    ordered_by_id: uuid.UUID
    test_name: str
    sample_type: str | None
    source: LabOrderSource
    external_lab_name: str | None
    priority: LabOrderPriority
    status: LabOrderStatus
    created_at: datetime


class LabResultCreate(BaseModel):
    parameter_name: str
    value: str
    unit: str | None = None
    reference_range: str | None = None
    flag: LabResultFlag = LabResultFlag.NORMAL


class LabResultOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    order_id: uuid.UUID
    parameter_name: str
    value: str
    unit: str | None
    reference_range: str | None
    flag: LabResultFlag
    entered_by_id: uuid.UUID
    created_at: datetime
