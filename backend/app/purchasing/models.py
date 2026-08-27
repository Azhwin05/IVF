"""
Purchase Request -> Approval -> Purchase Order -> GRN -> Stock Entry,
per spec §16.
"""
import enum
import uuid
from datetime import date

from sqlalchemy import Date, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base_model import TimestampMixin, UUIDPrimaryKeyMixin
from app.core.database import Base


class PurchaseOrderStatus(str, enum.Enum):
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    DISPATCHED = "dispatched"
    RECEIVED = "received"
    REJECTED = "rejected"


class PurchaseOrder(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "purchase_orders"

    po_number: Mapped[str] = mapped_column(String(32), unique=True, nullable=False, index=True)
    item_description: Mapped[str] = mapped_column(String(255), nullable=False)
    inventory_item_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("inventory_items.id"), nullable=True)
    medicine_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("medicines.id"), nullable=True)

    supplier: Mapped[str] = mapped_column(String(255), nullable=False)
    quantity_ordered: Mapped[int] = mapped_column(Integer, nullable=False)
    amount_paise: Mapped[int] = mapped_column(Integer, nullable=False)

    requested_by_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    approved_by_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    status: Mapped[PurchaseOrderStatus] = mapped_column(Enum(PurchaseOrderStatus), default=PurchaseOrderStatus.PENDING_APPROVAL, index=True)

    grn: Mapped["GoodsReceiptNote | None"] = relationship(back_populates="purchase_order", lazy="selectin", uselist=False)


class GoodsReceiptNote(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "goods_receipt_notes"

    purchase_order_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("purchase_orders.id"), nullable=False, unique=True)
    purchase_order: Mapped["PurchaseOrder"] = relationship(back_populates="grn")

    received_quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    damaged_quantity: Mapped[int] = mapped_column(Integer, default=0)
    free_quantity: Mapped[int] = mapped_column(Integer, default=0)
    supplier_invoice_number: Mapped[str | None] = mapped_column(String(64), nullable=True)
    received_by_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    received_date: Mapped[date] = mapped_column(Date, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
