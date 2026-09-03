import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict

from app.ivf.models import CycleStage, InjectionStatus, PregnancyOutcome


class CycleCreate(BaseModel):
    couple_id: uuid.UUID
    primary_doctor_id: uuid.UUID
    protocol: str
    treatment: str
    started_at: date


class TreatmentPlanUpsert(BaseModel):
    objective: str | None = None
    medication_plan: list[dict] | None = None  # [{name, dose, route, status}]
    consent_status: dict | None = None
    notes: str | None = None


class TreatmentPlanOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    cycle_id: uuid.UUID
    objective: str | None
    medication_plan: list[dict] | None
    consent_status: dict | None
    notes: str | None


class CycleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    cycle_number: str
    couple_id: uuid.UUID
    protocol: str
    treatment: str
    stage: CycleStage
    started_at: date
    # Both relationships are already eagerly loaded (lazy="selectin" on
    # IVFCycle, see app/ivf/models.py) so embedding them here is free —
    # the frontend's Monitoring/Plan screens need the full history in one
    # request rather than N+1 round trips per visit.
    monitoring_visits: list["MonitoringVisitOut"] = []
    treatment_plans: list["TreatmentPlanOut"] = []


class CycleStageUpdate(BaseModel):
    stage: CycleStage


class InjectionScheduleCreate(BaseModel):
    cycle_id: uuid.UUID
    medicine_name: str
    dose: str
    scheduled_at: datetime


class InjectionAdminister(BaseModel):
    notes: str | None = None


class InjectionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    cycle_id: uuid.UUID
    medicine_name: str
    dose: str
    scheduled_at: datetime
    status: InjectionStatus
    administered_at: datetime | None
    administered_by_id: uuid.UUID | None
    notes: str | None


class TreatmentProtocolUpsert(BaseModel):
    content: str
    fields: dict | None = None


class TreatmentProtocolOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    cycle_id: uuid.UUID
    content: str
    fields: dict | None
    created_by_id: uuid.UUID
    updated_by_id: uuid.UUID | None


class MonitoringVisitCreate(BaseModel):
    cycle_id: uuid.UUID
    cycle_day: int
    visit_date: date
    right_follicles_mm: list[float]
    left_follicles_mm: list[float]
    endometrium_mm: float
    estradiol_pg_ml: float | None = None
    lh_miu_ml: float | None = None
    progesterone_ng_ml: float | None = None
    doctor_note: str | None = None


class MonitoringVisitOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    cycle_id: uuid.UUID
    cycle_day: int
    visit_date: date
    right_follicles_mm: list
    left_follicles_mm: list
    endometrium_mm: float
    estradiol_pg_ml: float | None
    lh_miu_ml: float | None
    progesterone_ng_ml: float | None
    doctor_note: str | None
    reviewed_by_id: uuid.UUID | None


class MonitoringReview(BaseModel):
    doctor_note: str


class BetaHcgCreate(BaseModel):
    cycle_id: uuid.UUID
    day_label: str
    value_miu_ml: float
    recorded_at: date
    interpretation: str | None = None


class BetaHcgOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    day_label: str
    value_miu_ml: float
    recorded_at: date
    interpretation: str | None


class MilestoneCreate(BaseModel):
    cycle_id: uuid.UUID
    label: str
    milestone_date: date
    detail: str | None = None


class MilestoneOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    label: str
    milestone_date: date
    detail: str | None
    is_completed: bool


class PregnancyOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    cycle_id: uuid.UUID
    outcome: PregnancyOutcome
    estimated_due_date: date | None
    beta_hcg_results: list[BetaHcgOut]
    milestones: list[MilestoneOut]


# CycleOut references MonitoringVisitOut/TreatmentPlanOut by forward
# reference (both are defined further down this file) — resolve them now
# that every class in the module has been declared.
CycleOut.model_rebuild()
