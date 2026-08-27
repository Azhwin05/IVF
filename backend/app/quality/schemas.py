import uuid
from datetime import date

from pydantic import BaseModel, ConfigDict

from app.quality.models import QAFrequency


class QATemplateCreate(BaseModel):
    title: str
    department: str
    frequency: QAFrequency
    checklist_description: str | None = None


class QATaskInstanceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    template_id: uuid.UUID
    due_date: date
    completed: bool
    completed_by_id: uuid.UUID | None
    verified_by_id: uuid.UUID | None


class QATaskComplete(BaseModel):
    pass
