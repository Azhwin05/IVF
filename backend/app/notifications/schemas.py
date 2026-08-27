import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.notifications.models import NotificationTone, TaskStatus


class NotificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    title: str
    body: str | None
    tone: NotificationTone
    is_read: bool
    created_at: datetime


class TaskCreate(BaseModel):
    assigned_to_id: uuid.UUID
    title: str
    detail: str | None = None
    due_at: datetime
    related_entity_type: str | None = None
    related_entity_id: str | None = None


class TaskResolve(BaseModel):
    resolution: str


class TaskOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    title: str
    detail: str | None
    due_at: datetime
    status: TaskStatus
    resolution: str | None
