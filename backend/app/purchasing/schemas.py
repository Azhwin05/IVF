import uuid
from datetime import date

from pydantic import BaseModel, ConfigDict

from app.purchasing.models import PurchaseOrderStatus


class PurchaseOrderCreate(BaseModel):
    item_description: str
    inventory_item_id: uuid.UUID | None = None
    medicine_id: uuid.UUID | None = None
    supplier: str
    quantity_ordered: int
    amount_paise: int


class PurchaseOrderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    po_number: str
    item_description: str
    supplier: str
    quantity_ordered: int
    amount_paise: int
    status: PurchaseOrderStatus


class GRNCreate(BaseModel):
    purchase_order_id: uuid.UUID
    received_quantity: int
    damaged_quantity: int = 0
    free_quantity: int = 0
    supplier_invoice_number: str | None = None
    received_date: date
    notes: str | None = None
