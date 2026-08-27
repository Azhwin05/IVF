import uuid

from pydantic import BaseModel, ConfigDict, Field

from app.billing.models import InvoiceStatus, PaymentMethod


class ChargeCreate(BaseModel):
    service_code: str
    description: str
    amount_paise: int = Field(gt=0)
    source_module: str | None = None
    source_entity_id: str | None = None


class InvoiceCreate(BaseModel):
    patient_id: uuid.UUID
    couple_id: uuid.UUID | None = None
    charges: list[ChargeCreate]


class ChargeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    service_code: str
    description: str
    amount_paise: int
    covered_by_package: bool


class InvoiceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    invoice_number: str
    patient_id: uuid.UUID
    status: InvoiceStatus
    total_amount_paise: int
    paid_amount_paise: int
    discount_paise: int
    outstanding_paise: int
    charges: list[ChargeOut]


class PaymentCreate(BaseModel):
    invoice_id: uuid.UUID
    amount_paise: int = Field(gt=0)
    method: PaymentMethod
    reference: str | None = None


class RefundCreate(BaseModel):
    invoice_id: uuid.UUID
    amount_paise: int = Field(gt=0)
    reason: str = Field(min_length=5)


class DiscountApply(BaseModel):
    invoice_id: uuid.UUID
    discount_paise: int = Field(gt=0)
    reason: str = Field(min_length=5)


class BillingOverrideCreate(BaseModel):
    invoice_id: uuid.UUID
    reason: str = Field(min_length=10)


class PaymentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    receipt_number: str
    invoice_id: uuid.UUID
    amount_paise: int
    method: PaymentMethod
    is_refund: bool
