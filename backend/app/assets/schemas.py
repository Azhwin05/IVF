import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict

from app.assets.models import AssetStatus


class AssetCreate(BaseModel):
    name: str
    category: str | None = None
    brand: str | None = None
    model: str | None = None
    serial_number: str | None = None
    purchase_date: date | None = None
    cost_paise: int | None = None
    current_location: str | None = None
    warranty_until: date | None = None
    amc_until: date | None = None


class AssetOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    asset_code: str
    name: str
    category: str | None
    current_location: str | None
    status: AssetStatus


class AssetMoveRequest(BaseModel):
    to_location: str
    notes: str | None = None


class AssetMovementOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    event_type: str
    from_location: str | None
    to_location: str | None
    occurred_at: datetime
    performed_by_id: uuid.UUID
