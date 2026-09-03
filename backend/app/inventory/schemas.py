import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.inventory.models import InventoryCategory, ReservationStatus, StockMovementType


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
    reserved_qty: int
    available_qty: int
    reorder_level: int
    location: str | None
    supplier: str | None
    last_restocked: date | None


class StockAdjustment(BaseModel):
    item_id: uuid.UUID
    movement_type: StockMovementType
    quantity_delta: int
    reason: str = Field(min_length=5)


class StockReservationCreate(BaseModel):
    item_id: uuid.UUID
    quantity: int = Field(gt=0)
    procedure_entity_type: str
    procedure_entity_id: str


class StockReservationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    item_id: uuid.UUID
    quantity: int
    procedure_entity_type: str
    procedure_entity_id: str
    status: ReservationStatus
    reserved_by_id: uuid.UUID
    created_at: datetime


class ProcedureReadinessCheck(BaseModel):
    """Response for 'is this procedure's required stock ready'."""
    ready: bool
    shortages: list[dict]  # [{item_id, name, required, available}]
