import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator


class AuditEventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    timestamp: datetime
    actor_id: uuid.UUID | None
    actor_role: str | None
    action: str
    entity_type: str
    entity_id: str | None
    reason: str | None
    source_ip: str | None

    @field_validator("source_ip", mode="before")
    @classmethod
    def _stringify_ip(cls, v: object) -> str | None:
        # asyncpg/SQLAlchemy return INET columns as ipaddress objects, not str.
        return str(v) if v is not None else None
