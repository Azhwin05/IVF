"""
Cryostorage location hierarchy (Tank -> Canister -> Cane -> Goblet ->
Straw), immutable custody events, and the embryo transfer procedure
with its 6-point safety checklist — from the frontend's CRYO_HIERARCHY
and TRANSFER_CHECKLIST shapes.
"""
import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base_model import TimestampMixin, UUIDPrimaryKeyMixin
from app.core.database import Base


class CryoLocation(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """A single addressable slot: Tank A / Canister 04 / Cane 02 / Goblet 05 / Straw 03."""
    __tablename__ = "cryo_locations"
    __table_args__ = (UniqueConstraint("tank", "canister", "cane", "goblet", "straw", name="uq_cryo_address"),)

    tank: Mapped[str] = mapped_column(String(32), nullable=False)
    canister: Mapped[str] = mapped_column(String(32), nullable=False)
    cane: Mapped[str] = mapped_column(String(32), nullable=False)
    goblet: Mapped[str] = mapped_column(String(32), nullable=False)
    straw: Mapped[str] = mapped_column(String(32), nullable=False)

    embryo_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("embryos.id"), nullable=True, unique=True)
    frozen_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    consent_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    renewal_due: Mapped[date | None] = mapped_column(Date, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)  # False once vacated (thawed/transferred/discarded)


class CryoCustodyEvent(Base, UUIDPrimaryKeyMixin):
    """Immutable — never updated or deleted, same DB-grant policy as
    audit_events. Every physical handling of a stored embryo gets a row."""
    __tablename__ = "cryo_custody_events"

    location_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("cryo_locations.id"), nullable=False, index=True)
    embryo_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("embryos.id"), nullable=False, index=True)

    event_type: Mapped[str] = mapped_column(String(64), nullable=False)  # "vitrified", "moved", "witness_verified", "thawed"
    performed_by_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    witnessed_by_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


class EmbryoTransfer(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """The transfer procedure itself, gated by the 6-point checklist below."""
    __tablename__ = "embryo_transfers"

    cycle_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("ivf_cycles.id"), nullable=False, index=True)
    embryo_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("embryos.id"), nullable=False)
    procedure_doctor_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    embryologist_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    transfer_date: Mapped[date] = mapped_column(Date, nullable=False)
    completed: Mapped[bool] = mapped_column(Boolean, default=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    checklist: Mapped[list["TransferChecklistItem"]] = relationship(back_populates="transfer", lazy="selectin")


class TransferChecklistItem(Base, UUIDPrimaryKeyMixin):
    """The 6 fixed checklist items from the frontend's TRANSFER_CHECKLIST —
    patient identity, couple info, embryo identity, consent, clinical team,
    procedure documentation. All 6 must be checked before `completed` can
    be set True (enforced in service.py, not just the frontend)."""
    __tablename__ = "transfer_checklist_items"

    transfer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("embryo_transfers.id"), nullable=False)
    transfer: Mapped["EmbryoTransfer"] = relationship(back_populates="checklist")

    item_code: Mapped[str] = mapped_column(String(64), nullable=False)  # "patient_identity", "couple_info", ...
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    checked: Mapped[bool] = mapped_column(Boolean, default=False)
    checked_by_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


TRANSFER_CHECKLIST_ITEMS = [
    ("patient_identity", "Patient identity verified"),
    ("couple_info", "Couple information verified"),
    ("embryo_identity", "Embryo identity verified"),
    ("consent", "Consent confirmed"),
    ("clinical_team", "Clinical team verified"),
    ("documentation", "Procedure documentation completed"),
]
