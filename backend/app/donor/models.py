"""
Donor management — new requirement (source doc §22-23), previously
COMPLETELY absent from the codebase (confirmed by an exhaustive grep for
"donor" across the entire backend before this module was written — zero
matches). This is new construction, not a modification of anything.

NEEDS HOSPITAL CONFIRMATION (NEW_FEATURES_GAP_ANALYSIS.md §19): the exact
meaning of the five categories named in the client meeting, and the exact
reuse rule. DonorCategory below uses the client's own named categories
verbatim rather than inventing different ones — but nothing here assumes
what each category is allowed to do beyond the one explicit rule the
source doc states as non-negotiable: a donor cannot be actively matched
to more than one patient/couple at a time. That rule is enforced with a
real database constraint (a partial unique index), not just an
application-level check, per the source doc's own instruction ("Do not
rely only on a UI warning") and the general database-integrity
requirement (§32).
"""
import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Index, Numeric, String, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base_model import TimestampMixin, UUIDPrimaryKeyMixin
from app.core.database import Base


class DonorCategory(str, enum.Enum):
    SELF_DONOR = "self_donor"
    SELF_EMBRYO = "self_embryo"
    DONOR = "donor"
    BANK_STORAGE = "bank_storage"
    DONOR_EMBRYO = "donor_embryo"


class DonorStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    RETIRED = "retired"


class Donor(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "donors"

    donor_code: Mapped[str] = mapped_column(String(32), unique=True, nullable=False, index=True)  # controlled numbering, e.g. DNR-2026-00001
    category: Mapped[DonorCategory] = mapped_column(Enum(DonorCategory), nullable=False, index=True)
    status: Mapped[DonorStatus] = mapped_column(Enum(DonorStatus), default=DonorStatus.ACTIVE, index=True)

    # Deliberately minimal identifying/profile fields — the exact donor
    # registration form is one of the items needing hospital confirmation
    # (source doc §36). Anything beyond this is tracked as free-text
    # `screening_notes` rather than guessed structured fields.
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    contact_phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    screening_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    matches: Mapped[list["DonorMatch"]] = relationship(back_populates="donor", lazy="selectin")


class DonorMatch(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """A donor<->patient/couple pairing. `is_active` plus the partial
    unique index below is the actual enforcement mechanism — ending a
    match sets is_active=False (a new row is never allowed to violate the
    index while an active one exists for the same donor), so the full
    matching history stays queryable rather than being overwritten."""
    __tablename__ = "donor_matches"
    __table_args__ = (
        # Partial unique index: a given donor may have at most one row with
        # is_active=True at any time, across the whole table — this is the
        # actual mechanism preventing prohibited duplicate matching, not
        # just an application-level check that a race condition could slip
        # past. Ended/historical matches (is_active=False) are unaffected
        # and remain fully queryable.
        Index("uq_donor_one_active_match", "donor_id", unique=True, postgresql_where=text("is_active")),
    )

    donor_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("donors.id"), nullable=False, index=True)
    donor: Mapped["Donor"] = relationship(back_populates="matches")
    patient_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False, index=True)
    couple_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("couples.id"), nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    matched_by_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    matched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ended_reason: Mapped[str | None] = mapped_column(Text, nullable=True)


class DonorBenchmark(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """New requirement (source doc §23). `threshold_percent` is
    configurable PER METRIC, set by whoever records the benchmark — the
    client meeting mentioned "around 30% deviation" as an example, but the
    source doc explicitly says not to hard-code that as a universal rule,
    so there is no hardcoded default here. `is_underperforming` is a
    plain boolean the caller sets after comparing deviation to whatever
    threshold applies for that metric — never computed against a baked-in
    constant."""
    __tablename__ = "donor_benchmarks"

    donor_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("donors.id"), nullable=False, index=True)
    metric_name: Mapped[str] = mapped_column(String(128), nullable=False)  # e.g. "Fertilization Rate", "Blastocyst Rate"
    expected_value: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    actual_value: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    threshold_percent: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    is_underperforming: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)  # investigation of possible causes
    recorded_by_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    @property
    def deviation_percent(self) -> float:
        if self.expected_value == 0:
            return 0.0
        return round(((float(self.actual_value) - float(self.expected_value)) / float(self.expected_value)) * 100, 2)
