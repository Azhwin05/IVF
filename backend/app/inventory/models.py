import enum
import uuid
from datetime import date

from sqlalchemy import Boolean, Date, Enum, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import TimestampMixin, UUIDPrimaryKeyMixin
from app.core.database import Base


class InventoryCategory(str, enum.Enum):
    IVF_CONSUMABLES = "ivf_consumables"
    CRYOGENIC_SUPPLIES = "cryogenic_supplies"
    LAB_SUPPLIES = "lab_supplies"
    SURGICAL_EQUIPMENT = "surgical_equipment"


class InventoryItem(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "inventory_items"

    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    category: Mapped[InventoryCategory] = mapped_column(Enum(InventoryCategory), nullable=False, index=True)
    unit: Mapped[str] = mapped_column(String(32), nullable=False)
    stock: Mapped[int] = mapped_column(Integer, default=0)
    reorder_level: Mapped[int] = mapped_column(Integer, default=0)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    supplier: Mapped[str | None] = mapped_column(String(255), nullable=True)
    last_restocked: Mapped[date | None] = mapped_column(Date, nullable=True)


class StockMovementType(str, enum.Enum):
    RESTOCK = "restock"
    CONSUMED = "consumed"
    ADJUSTMENT = "adjustment"
    WRITE_OFF = "write_off"


class StockMovement(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Immutable movement ledger — the running `stock` count on
    InventoryItem is a cache derived from summing these; every change to
    it is explained by exactly one row here, per spec §33's
    'Prevent: Negative inventory' and the general audit requirement for
    stock adjustments/write-offs (critical actions per spec §6)."""
    __tablename__ = "stock_movements"

    item_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("inventory_items.id"), nullable=False, index=True)
    movement_type: Mapped[StockMovementType] = mapped_column(Enum(StockMovementType), nullable=False)
    quantity_delta: Mapped[int] = mapped_column(Integer, nullable=False)  # signed
    reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    performed_by_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
