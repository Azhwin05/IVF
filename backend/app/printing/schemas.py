import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class PrintLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    document_type: str
    patient_id: uuid.UUID | None
    context_entity_type: str | None
    context_entity_id: str | None
    printed_by_id: uuid.UUID
    printed_at: datetime
