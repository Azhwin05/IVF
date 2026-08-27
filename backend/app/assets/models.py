"""QR-coded physical asset register + immutable movement history, spec §20."""
import enum
import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import TimestampMixin, UUIDPrimaryKeyMixin
from app.core.database import Base


class AssetStatus(str, enum.Enum):
    ACTIVE = "active"
    UNDER_MAINTENANCE = "under_maintenance"
    SENT_FOR_SERVICE = "sent_for_service"
    RETIRED = "retired"


class Asset(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "assets"

    asset_code: Mapped[str] = mapped_column(String(32), unique=True, nullable=False, index=True)  # encoded in the QR
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str | None] = mapped_column(String(128), nullable=True)
    brand: Mapped[str | None] = mapped_column(String(128), nullable=True)
    model: Mapped[str | None] = mapped_column(String(128), nullable=True)
    serial_number: Mapped[str | None] = mapped_column(String(128), nullable=True)

    purchase_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    cost_paise: Mapped[int | None] = mapped_column(Integer, nullable=True)
    current_location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    assigned_to_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    warranty_until: Mapped[date | None] = mapped_column(Date, nullable=True)
    amc_until: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[AssetStatus] = mapped_column(Enum(AssetStatus), default=AssetStatus.ACTIVE, index=True)


class AssetMovement(Base, UUIDPrimaryKeyMixin):
    """Immutable — same DB-grant policy as audit_events and
    cryo_custody_events (spec §20: 'Movement history must be immutable')."""
    __tablename__ = "asset_movements"

    asset_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("assets.id"), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(32), nullable=False)  # "move", "service", "damage", "verify"
    from_location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    to_location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    notes: Mapped[str | None] = mapped_column(String(500), nullable=True)
    performed_by_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
