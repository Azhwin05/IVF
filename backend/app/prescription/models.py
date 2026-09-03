"""
Prescription — new requirement (source doc §9). Previously the only
medicine-ordering concept in the system was PharmacySale (a completed
dispensing transaction), with no way to write a prescription that isn't
simultaneously a completed sale. This module is the doctor's order; a
PharmacySale still happens separately when pharmacy actually fulfils it
(the two are linked by patient/cycle, not merged into one entity, per
the source doc's own warning against conflating distinct workflow steps
into a single source of truth).

NEEDS HOSPITAL CONFIRMATION (NEW_FEATURES_GAP_ANALYSIS.md §6): the client
meeting described an existing colour/template format (Yellow/Green/
Orange) whose clinical meaning was never explained and must not be
guessed. `category` below is a configurable free-text field the hospital
can populate with whatever those categories actually mean once the real
paper template is available — nothing here assumes a mapping.
"""
import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base_model import TimestampMixin, UUIDPrimaryKeyMixin
from app.core.database import Base


class Prescription(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "prescriptions"

    patient_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False, index=True)
    cycle_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("ivf_cycles.id"), nullable=True, index=True)
    prescribed_by_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # NEEDS HOSPITAL CONFIRMATION — see module docstring. Left as a plain,
    # hospital-fillable string rather than an enum with guessed values.
    category: Mapped[str | None] = mapped_column(String(64), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    lines: Mapped[list["PrescriptionLine"]] = relationship(back_populates="prescription", lazy="selectin")


class PrescriptionLine(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "prescription_lines"

    prescription_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("prescriptions.id"), nullable=False, index=True)
    prescription: Mapped["Prescription"] = relationship(back_populates="lines")

    medicine_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("medicines.id"), nullable=True)
    medicine_name: Mapped[str] = mapped_column(String(255), nullable=False)  # kept even if medicine_id is set, for a stable historical record
    dosage: Mapped[str] = mapped_column(String(64), nullable=False)
    frequency: Mapped[str] = mapped_column(String(64), nullable=False)  # e.g. "twice daily"
    timing: Mapped[str | None] = mapped_column(String(64), nullable=True)  # e.g. "after food"
    duration: Mapped[str | None] = mapped_column(String(64), nullable=True)  # e.g. "10 days"
    instructions: Mapped[str | None] = mapped_column(Text, nullable=True)
