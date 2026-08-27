import uuid
from datetime import date

from pydantic import BaseModel, ConfigDict

from app.maintenance.models import MaintenanceStatus, MaintenanceType


class MaintenanceTaskCreate(BaseModel):
    equipment_name: str
    asset_id: uuid.UUID | None = None
    task_type: MaintenanceType
    due_date: date
    assigned_to_id: uuid.UUID | None = None


class MaintenanceTaskOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    equipment_name: str
    task_type: MaintenanceType
    due_date: date
    status: MaintenanceStatus


class MaintenanceComplete(BaseModel):
    notes: str | None = None
