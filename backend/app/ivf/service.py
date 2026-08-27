import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.service import record_audit_event
from app.clinical.models import TimelineEventType
from app.clinical.service import add_timeline_event
from app.core.exceptions import NotFoundError
from app.ivf.models import (
    BetaHcgResult,
    CycleStage,
    IVFCycle,
    MonitoringVisit,
    PregnancyMilestone,
    PregnancyRecord,
    TreatmentPlan,
)
from app.ivf.schemas import BetaHcgCreate, CycleCreate, MilestoneCreate, MonitoringVisitCreate, TreatmentPlanUpsert
from app.patients.models import Couple


async def _next_cycle_number(session: AsyncSession) -> str:
    year = datetime.now(timezone.utc).year
    prefix = f"IVF-{year}-"
    result = await session.execute(
        select(IVFCycle.cycle_number).where(IVFCycle.cycle_number.like(f"{prefix}%"))
        .order_by(IVFCycle.cycle_number.desc()).limit(1).with_for_update()
    )
    last = result.scalar_one_or_none()
    next_seq = int(last.split("-")[-1]) + 1 if last else 1
    return f"{prefix}{next_seq:05d}"


async def create_cycle(session: AsyncSession, data: CycleCreate, *, actor_id: uuid.UUID, actor_role: str) -> IVFCycle:
    cycle = IVFCycle(cycle_number=await _next_cycle_number(session), **data.model_dump())
    session.add(cycle)
    await session.flush()

    couple = await session.get(Couple, data.couple_id)
    await add_timeline_event(
        session, patient_id=couple.female_patient_id, couple_id=couple.id,
        event_type=TimelineEventType.STIMULATION_START, title=f"{data.treatment} — {data.protocol}",
        summary=None, source_entity_type="IVFCycle", source_entity_id=str(cycle.id),
    )
    await record_audit_event(
        session, actor_id=actor_id, actor_role=actor_role,
        action="ivf.cycle_created", entity_type="IVFCycle", entity_id=str(cycle.id),
        after_state={"cycle_number": cycle.cycle_number, "protocol": data.protocol},
    )
    return cycle


async def get_cycle(session: AsyncSession, cycle_id: uuid.UUID) -> IVFCycle:
    cycle = await session.get(IVFCycle, cycle_id)
    if not cycle:
        raise NotFoundError("IVF cycle not found", error_code="cycle_not_found")
    return cycle


async def get_active_cycle_for_couple(session: AsyncSession, couple_id: uuid.UUID) -> IVFCycle | None:
    result = await session.execute(
        select(IVFCycle)
        .where(IVFCycle.couple_id == couple_id, IVFCycle.stage != CycleStage.COMPLETED)
        .order_by(IVFCycle.started_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def advance_stage(
    session: AsyncSession, cycle_id: uuid.UUID, new_stage: CycleStage, *, actor_id: uuid.UUID, actor_role: str
) -> IVFCycle:
    cycle = await get_cycle(session, cycle_id)
    before = cycle.stage
    cycle.stage = new_stage
    await session.flush()

    await record_audit_event(
        session, actor_id=actor_id, actor_role=actor_role,
        action="ivf.cycle_stage_advanced", entity_type="IVFCycle", entity_id=str(cycle.id),
        before_state={"stage": before.value}, after_state={"stage": new_stage.value},
    )
    return cycle


async def record_monitoring_visit(
    session: AsyncSession, data: MonitoringVisitCreate, *, actor_id: uuid.UUID, actor_role: str
) -> MonitoringVisit:
    cycle = await get_cycle(session, data.cycle_id)
    visit = MonitoringVisit(**data.model_dump())
    session.add(visit)
    await session.flush()

    lead_follicle = max([*data.right_follicles_mm, *data.left_follicles_mm], default=0)
    couple_result = await session.execute(select(Couple).where(Couple.id == cycle.couple_id))
    couple = couple_result.scalar_one()

    await add_timeline_event(
        session, patient_id=couple.female_patient_id, couple_id=couple.id,
        event_type=TimelineEventType.MONITORING_VISIT,
        title=f"Monitoring — Day {data.cycle_day}",
        summary=f"Lead follicle {lead_follicle} mm, endometrium {data.endometrium_mm} mm",
        source_entity_type="MonitoringVisit", source_entity_id=str(visit.id),
    )
    await record_audit_event(
        session, actor_id=actor_id, actor_role=actor_role,
        action="ivf.monitoring_recorded", entity_type="MonitoringVisit", entity_id=str(visit.id),
    )
    return visit


async def review_monitoring_visit(
    session: AsyncSession, visit_id: uuid.UUID, doctor_note: str, *, actor_id: uuid.UUID, actor_role: str
) -> MonitoringVisit:
    """The doctor's clinical sign-off — a critical action (spec §6:
    'clinical record correction' class) that must be permission-gated
    and audited, matching the existing frontend's 'Save Clinical Review'
    button on the Monitoring screen."""
    visit = await session.get(MonitoringVisit, visit_id)
    if not visit:
        raise NotFoundError("Monitoring visit not found")

    visit.doctor_note = doctor_note
    visit.reviewed_by_id = actor_id
    visit.reviewed_at = datetime.now(timezone.utc)
    await session.flush()

    await record_audit_event(
        session, actor_id=actor_id, actor_role=actor_role,
        action="ivf.monitoring_reviewed", entity_type="MonitoringVisit", entity_id=str(visit.id),
        after_state={"doctor_note": doctor_note},
    )
    return visit


async def upsert_treatment_plan(
    session: AsyncSession, cycle_id: uuid.UUID, data: TreatmentPlanUpsert, *, actor_id: uuid.UUID, actor_role: str
) -> TreatmentPlan:
    """One editable plan per cycle — the Treatment Plan screen is a single
    form the doctor updates over time, not a history of past plans, so
    this updates the existing row in place rather than creating a new one
    on every save."""
    await get_cycle(session, cycle_id)  # 404s if the cycle doesn't exist
    result = await session.execute(select(TreatmentPlan).where(TreatmentPlan.cycle_id == cycle_id))
    plan = result.scalar_one_or_none()

    before = None
    if plan is None:
        plan = TreatmentPlan(cycle_id=cycle_id, **data.model_dump())
        session.add(plan)
    else:
        before = {"objective": plan.objective, "medication_plan": plan.medication_plan, "notes": plan.notes}
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(plan, field, value)
    await session.flush()

    await record_audit_event(
        session, actor_id=actor_id, actor_role=actor_role,
        action="ivf.treatment_plan_saved", entity_type="TreatmentPlan", entity_id=str(plan.id),
        before_state=before, after_state=data.model_dump(exclude_unset=True, mode="json"),
    )
    return plan


async def get_or_create_pregnancy(session: AsyncSession, cycle_id: uuid.UUID) -> PregnancyRecord:
    result = await session.execute(select(PregnancyRecord).where(PregnancyRecord.cycle_id == cycle_id))
    record = result.scalar_one_or_none()
    if record:
        return record
    record = PregnancyRecord(cycle_id=cycle_id)
    session.add(record)
    await session.flush()
    return record


async def record_beta_hcg(
    session: AsyncSession, data: BetaHcgCreate, *, actor_id: uuid.UUID, actor_role: str
) -> BetaHcgResult:
    pregnancy = await get_or_create_pregnancy(session, data.cycle_id)
    if pregnancy.outcome == "pending" and data.value_miu_ml > 5:
        pregnancy.outcome = "positive"

    result = BetaHcgResult(
        pregnancy_id=pregnancy.id, day_label=data.day_label, value_miu_ml=data.value_miu_ml,
        recorded_at=data.recorded_at, interpretation=data.interpretation,
    )
    session.add(result)
    await session.flush()

    cycle = await get_cycle(session, data.cycle_id)
    couple_result = await session.execute(select(Couple).where(Couple.id == cycle.couple_id))
    couple = couple_result.scalar_one()
    await add_timeline_event(
        session, patient_id=couple.female_patient_id, couple_id=couple.id,
        event_type=TimelineEventType.PREGNANCY_MILESTONE, title=f"Beta-hCG {data.day_label}",
        summary=f"{data.value_miu_ml} mIU/mL — {data.interpretation or ''}",
        source_entity_type="BetaHcgResult", source_entity_id=str(result.id),
    )
    await record_audit_event(
        session, actor_id=actor_id, actor_role=actor_role,
        action="ivf.beta_hcg_recorded", entity_type="BetaHcgResult", entity_id=str(result.id),
    )
    return result


async def record_pregnancy_milestone(
    session: AsyncSession, data: MilestoneCreate, *, actor_id: uuid.UUID, actor_role: str
) -> PregnancyMilestone:
    pregnancy = await get_or_create_pregnancy(session, data.cycle_id)
    milestone = PregnancyMilestone(
        pregnancy_id=pregnancy.id, label=data.label, milestone_date=data.milestone_date, detail=data.detail,
    )
    session.add(milestone)
    await session.flush()

    cycle = await get_cycle(session, data.cycle_id)
    couple_result = await session.execute(select(Couple).where(Couple.id == cycle.couple_id))
    couple = couple_result.scalar_one()
    await add_timeline_event(
        session, patient_id=couple.female_patient_id, couple_id=couple.id,
        event_type=TimelineEventType.PREGNANCY_MILESTONE, title=data.label,
        summary=data.detail, source_entity_type="PregnancyMilestone", source_entity_id=str(milestone.id),
    )
    await record_audit_event(
        session, actor_id=actor_id, actor_role=actor_role,
        action="ivf.pregnancy_milestone_recorded", entity_type="PregnancyMilestone", entity_id=str(milestone.id),
    )
    return milestone
