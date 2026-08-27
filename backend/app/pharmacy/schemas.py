import uuid
from datetime import date

from pydantic import BaseModel, ConfigDict, Field


class MedicineOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    generic_name: str
    brand_name: str | None
    category: str | None
    unit: str
    reorder_level: int
    total_available: int = 0


class BatchOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    batch_number: str
    expiry_date: date
    quantity_available: int
    selling_rate_paise: int


class DispenseLine(BaseModel):
    medicine_id: uuid.UUID
    quantity: int = Field(gt=0)


class DispenseRequest(BaseModel):
    patient_id: uuid.UUID
    prescribed_by_id: uuid.UUID | None = None
    lines: list[DispenseLine]
    create_invoice: bool = True


class SaleLineOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    medicine_id: uuid.UUID
    batch_id: uuid.UUID
    quantity: int
    unit_price_paise: int


class SaleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    bill_number: str
    patient_id: uuid.UUID
    total_amount_paise: int
    status: str
    lines: list[SaleLineOut]
