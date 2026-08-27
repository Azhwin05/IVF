import uuid

from pydantic import BaseModel, ConfigDict

from app.laboratory.models import LabOrderPriority, LabOrderSource, LabOrderStatus


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
    test_name: str
    source: LabOrderSource
    external_lab_name: str | None
    priority: LabOrderPriority
    status: LabOrderStatus
