import uuid
from datetime import date

from pydantic import BaseModel, ConfigDict, Field

from app.inventory.models import InventoryCategory, StockMovementType


class InventoryItemCreate(BaseModel):
    name: str
    category: InventoryCategory
    unit: str
    stock: int = 0
    reorder_level: int = 0
    location: str | None = None
    supplier: str | None = None


class InventoryItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    name: str
    category: InventoryCategory
    unit: str
    stock: int
    reorder_level: int
    location: str | None
    supplier: str | None
    last_restocked: date | None


class StockAdjustment(BaseModel):
    item_id: uuid.UUID
    movement_type: StockMovementType
    quantity_delta: int
    reason: str = Field(min_length=5)
