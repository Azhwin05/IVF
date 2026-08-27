"""
IVF cycle, treatment plan, and stimulation monitoring — from the
frontend's Plan.tsx stage tracker and MonitoringVisit shape (follicle
arrays + hormone panel powering the FollicleMap component unchanged).
"""
import enum
import uuid
from datetime import date, datetime

from sqlalchemy import JSON, Date, DateTime, Enum, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base_model import TimestampMixin, UUIDPrimaryKeyMixin
from app.core.database import Base


class CycleStage(str, enum.Enum):
    ASSESSMENT = "assessment"
    STIMULATION = "stimulation"
    TRIGGER = "trigger"
    RETRIEVAL = "retrieval"
    EMBRYOLOGY = "embryology"
    TRANSFER = "transfer"
    PREGNANCY_FOLLOWUP = "pregnancy_followup"
    COMPLETED = "completed"


class IVFCycle(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "ivf_cycles"

    cycle_number: Mapped[str] = mapped_column(String(32), unique=True, nullable=False, index=True)  # IVF-2026-00428
    couple_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("couples.id"), nullable=False, index=True)
    primary_doctor_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    protocol: Mapped[str] = mapped_column(String(128), nullable=False)  # "GnRH Antagonist Protocol"
    treatment: Mapped[str] = mapped_column(String(128), nullable=False)  # "IVF with ICSI"
    stage: Mapped[CycleStage] = mapped_column(Enum(CycleStage), default=CycleStage.ASSESSMENT, index=True)
    started_at: Mapped[date] = mapped_column(Date, nullable=False)

    treatment_plans: Mapped[list["TreatmentPlan"]] = relationship(back_populates="cycle", lazy="selectin")
    monitoring_visits: Mapped[list["MonitoringVisit"]] = relationship(back_populates="cycle", lazy="selectin")


class TreatmentPlan(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "treatment_plans"

    cycle_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("ivf_cycles.id"), nullable=False, index=True)
    cycle: Mapped["IVFCycle"] = relationship(back_populates="treatment_plans")

    objective: Mapped[str | None] = mapped_column(Text, nullable=True)
    medication_plan: Mapped[dict | None] = mapped_column(JSON, nullable=True)  # list of {name, dose, route, status}
    consent_status: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


class MonitoringVisit(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Follicle sizes stored as JSON arrays (mm) — matches the frontend's
    MonitoringVisit.right/left shape exactly, so the FollicleMap SVG
    component needs zero changes when wired to real data."""
    __tablename__ = "monitoring_visits"

    cycle_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("ivf_cycles.id"), nullable=False, index=True)
    cycle: Mapped["IVFCycle"] = relationship(back_populates="monitoring_visits")

    cycle_day: Mapped[int] = mapped_column(nullable=False)
    visit_date: Mapped[date] = mapped_column(Date, nullable=False)

    right_follicles_mm: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    left_follicles_mm: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    endometrium_mm: Mapped[float] = mapped_column(Numeric(4, 1), nullable=False)

    estradiol_pg_ml: Mapped[float | None] = mapped_column(Numeric(8, 2), nullable=True)
    lh_miu_ml: Mapped[float | None] = mapped_column(Numeric(6, 2), nullable=True)
    progesterone_ng_ml: Mapped[float | None] = mapped_column(Numeric(6, 2), nullable=True)

    doctor_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewed_by_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class PregnancyOutcome(str, enum.Enum):
    PENDING = "pending"
    POSITIVE = "positive"
    NEGATIVE = "negative"
    BIOCHEMICAL_ONLY = "biochemical_only"


class PregnancyRecord(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "pregnancy_records"

    cycle_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("ivf_cycles.id"), nullable=False, unique=True, index=True)
    transfer_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    outcome: Mapped[PregnancyOutcome] = mapped_column(Enum(PregnancyOutcome), default=PregnancyOutcome.PENDING)
    estimated_due_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    beta_hcg_results: Mapped[list["BetaHcgResult"]] = relationship(back_populates="pregnancy", lazy="selectin")
    milestones: Mapped[list["PregnancyMilestone"]] = relationship(back_populates="pregnancy", lazy="selectin")


class BetaHcgResult(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "beta_hcg_results"

    pregnancy_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("pregnancy_records.id"), nullable=False)
    pregnancy: Mapped["PregnancyRecord"] = relationship(back_populates="beta_hcg_results")

    day_label: Mapped[str] = mapped_column(String(32), nullable=False)  # "Day 14"
    value_miu_ml: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    recorded_at: Mapped[date] = mapped_column(Date, nullable=False)
    interpretation: Mapped[str | None] = mapped_column(String(255), nullable=True)


class PregnancyMilestone(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "pregnancy_milestones"

    pregnancy_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("pregnancy_records.id"), nullable=False)
    pregnancy: Mapped["PregnancyRecord"] = relationship(back_populates="milestones")

    label: Mapped[str] = mapped_column(String(128), nullable=False)  # "Gestational Sac", "Cardiac Activity"
    milestone_date: Mapped[date] = mapped_column(Date, nullable=False)
    detail: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_completed: Mapped[bool] = mapped_column(default=True)
