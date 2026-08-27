import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.service import record_audit_event
from app.clinical.models import TimelineEventType
from app.clinical.service import add_timeline_event
from app.core.exceptions import NotFoundError
from app.embryology.models import Embryo, OocyteAssessment
from app.embryology.schemas import EmbryoCreate, OocyteAssessmentCreate
from app.ivf.service import get_cycle
from app.patients.models import Couple


async def create_oocyte_assessment(
    session: AsyncSession, data: OocyteAssessmentCreate, *, actor_id: uuid.UUID, actor_role: str
) -> OocyteAssessment:
    assessment = OocyteAssessment(**data.model_dump())
    session.add(assessment)
    await session.flush()

    await record_audit_event(
        session, actor_id=actor_id, actor_role=actor_role,
        action="embryology.oocyte_assessment_recorded", entity_type="OocyteAssessment", entity_id=str(assessment.id),
    )
    return assessment


async def grade_embryo(
    session: AsyncSession, data: EmbryoCreate, *, actor_id: uuid.UUID, actor_role: str
) -> Embryo:
    embryo = Embryo(graded_by_id=actor_id, **data.model_dump())
    session.add(embryo)
    await session.flush()

    cycle = await get_cycle(session, data.cycle_id)
    couple_result = await session.execute(select(Couple).where(Couple.id == cycle.couple_id))
    couple = couple_result.scalar_one()
    await add_timeline_event(
        session, patient_id=couple.female_patient_id, couple_id=couple.id,
        event_type=TimelineEventType.EMBRYOLOGY_UPDATE, title=f"Embryo {data.label} graded — {data.grade}",
        summary=data.embryologist_notes, source_entity_type="Embryo", source_entity_id=str(embryo.id),
    )
    await record_audit_event(
        session, actor_id=actor_id, actor_role=actor_role,
        action="embryology.embryo_graded", entity_type="Embryo", entity_id=str(embryo.id),
        after_state={"label": data.label, "grade": data.grade, "score": data.quality_score},
    )
    return embryo


async def list_embryos_for_cycle(session: AsyncSession, cycle_id: uuid.UUID) -> list[Embryo]:
    result = await session.execute(select(Embryo).where(Embryo.cycle_id == cycle_id).order_by(Embryo.label))
    return list(result.scalars().all())


async def update_embryo_status(
    session: AsyncSession, embryo_id: uuid.UUID, status, notes: str | None, *, actor_id: uuid.UUID, actor_role: str
) -> Embryo:
    embryo = await session.get(Embryo, embryo_id)
    if not embryo:
        raise NotFoundError("Embryo not found")

    before = embryo.status.value
    embryo.status = status
    if notes:
        embryo.embryologist_notes = notes
    await session.flush()

    await record_audit_event(
        session, actor_id=actor_id, actor_role=actor_role,
        action="embryology.embryo_status_changed", entity_type="Embryo", entity_id=str(embryo.id),
        before_state={"status": before}, after_state={"status": status.value}, reason=notes,
    )
    return embryo
