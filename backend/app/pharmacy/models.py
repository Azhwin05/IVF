"""
Pharmacy domain: Medicine (catalogue) -> MedicineBatch (stock, FEFO) ->
PharmacySale (dispensing transaction), from spec §15.
"""
import enum
import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base_model import TimestampMixin, UUIDPrimaryKeyMixin
from app.core.database import Base


class Medicine(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "medicines"

    generic_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    brand_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    manufacturer: Mapped[str | None] = mapped_column(String(255), nullable=True)
    strength: Mapped[str | None] = mapped_column(String(64), nullable=True)
    dosage_form: Mapped[str | None] = mapped_column(String(64), nullable=True)  # injection, tablet, ...
    category: Mapped[str | None] = mapped_column(String(128), nullable=True)
    unit: Mapped[str] = mapped_column(String(32), nullable=False)  # Pen, Vial, Strip, ...
    hsn_code: Mapped[str | None] = mapped_column(String(16), nullable=True)
    gst_percent: Mapped[int] = mapped_column(Integer, default=12)
    reorder_level: Mapped[int] = mapped_column(Integer, default=0)
    minimum_stock: Mapped[int] = mapped_column(Integer, default=0)

    batches: Mapped[list["MedicineBatch"]] = relationship(back_populates="medicine", lazy="selectin")


class MedicineBatch(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "medicine_batches"

    medicine_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("medicines.id"), nullable=False, index=True)
    medicine: Mapped["Medicine"] = relationship(back_populates="batches")

    batch_number: Mapped[str] = mapped_column(String(64), nullable=False)
    manufacturing_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    expiry_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)  # FEFO ordering key
    supplier: Mapped[str | None] = mapped_column(String(255), nullable=True)

    purchase_rate_paise: Mapped[int] = mapped_column(Integer, nullable=False)
    selling_rate_paise: Mapped[int] = mapped_column(Integer, nullable=False)

    quantity_received: Mapped[int] = mapped_column(Integer, nullable=False)
    quantity_available: Mapped[int] = mapped_column(Integer, nullable=False)  # decremented on dispense, never negative


class SaleStatus(str, enum.Enum):
    DISPENSED = "dispensed"
    RETURNED = "returned"
    PARTIALLY_RETURNED = "partially_returned"


class PharmacySale(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "pharmacy_sales"

    bill_number: Mapped[str] = mapped_column(String(32), unique=True, nullable=False, index=True)
    patient_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False, index=True)
    prescribed_by_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    dispensed_by_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    invoice_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("invoices.id"), nullable=True)
    total_amount_paise: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[SaleStatus] = mapped_column(Enum(SaleStatus), default=SaleStatus.DISPENSED)

    lines: Mapped[list["PharmacySaleLine"]] = relationship(back_populates="sale", lazy="selectin")


class PharmacySaleLine(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "pharmacy_sale_lines"

    sale_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("pharmacy_sales.id"), nullable=False)
    sale: Mapped["PharmacySale"] = relationship(back_populates="lines")

    medicine_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("medicines.id"), nullable=False)
    batch_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("medicine_batches.id"), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price_paise: Mapped[int] = mapped_column(Integer, nullable=False)
