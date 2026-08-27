import uuid
from datetime import date

from pydantic import BaseModel, ConfigDict

from app.ivf.models import CycleStage, PregnancyOutcome


class CycleCreate(BaseModel):
    couple_id: uuid.UUID
    primary_doctor_id: uuid.UUID
    protocol: str
    treatment: str
    started_at: date


class CycleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    cycle_number: str
    couple_id: uuid.UUID
    protocol: str
    treatment: str
    stage: CycleStage
    started_at: date


class CycleStageUpdate(BaseModel):
    stage: CycleStage


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
