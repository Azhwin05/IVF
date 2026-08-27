import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.service import record_audit_event
from app.clinical.models import ClinicalTimelineEvent, Consultation, TimelineEventType
from app.clinical.schemas import ConsultationCorrection, ConsultationCreate
from app.core.exceptions import NotFoundError


async def add_timeline_event(
    session: AsyncSession, *, patient_id: uuid.UUID, couple_id: uuid.UUID | None,
    event_type: TimelineEventType, title: str, summary: str | None,
    source_entity_type: str, source_entity_id: str, occurred_at: datetime | None = None,
) -> ClinicalTimelineEvent:
    """Called by other modules' services whenever something timeline-worthy
    happens (embryology grading, transfer completed, monitoring recorded,
    etc.) — see docstring in clinical/models.py."""
    event = ClinicalTimelineEvent(
        patient_id=patient_id, couple_id=couple_id,
        occurred_at=occurred_at or datetime.now(timezone.utc),
        event_type=event_type, title=title, summary=summary,
        source_entity_type=source_entity_type, source_entity_id=source_entity_id,
    )
    session.add(event)
    await session.flush()
    return event


async def get_patient_timeline(session: AsyncSession, patient_id: uuid.UUID) -> list[ClinicalTimelineEvent]:
    result = await session.execute(
        select(ClinicalTimelineEvent)
        .where(ClinicalTimelineEvent.patient_id == patient_id)
        .order_by(ClinicalTimelineEvent.occurred_at.desc())
    )
    return list(result.scalars().all())


async def create_consultation(
    session: AsyncSession, data: ConsultationCreate, *, actor_id: uuid.UUID, actor_role: str
) -> Consultation:
    consult = Consultation(doctor_id=actor_id, **data.model_dump())
    session.add(consult)
    await session.flush()

    await add_timeline_event(
        session, patient_id=data.patient_id, couple_id=None,
        event_type=TimelineEventType.CONSULTATION, title=data.consultation_type,
        summary=data.notes[:280], source_entity_type="Consultation", source_entity_id=str(consult.id),
    )
    await record_audit_event(
        session, actor_id=actor_id, actor_role=actor_role,
        action="clinical.consultation_created", entity_type="Consultation", entity_id=str(consult.id),
    )
    return consult


async def correct_consultation(
    session: AsyncSession, data: ConsultationCorrection, *, actor_id: uuid.UUID, actor_role: str
) -> Consultation:
    """Per spec §7: never overwrite; create a new linked correction record.
    Requires clinical.correct permission at the router (elevated vs. plain
    clinical.write)."""
    original = await session.get(Consultation, data.corrects_consultation_id)
    if not original:
        raise NotFoundError("Original consultation not found")

    correction = Consultation(
        patient_id=original.patient_id, doctor_id=actor_id,
        consultation_type=original.consultation_type, notes=data.notes,
        corrects_consultation_id=original.id, correction_reason=data.correction_reason,
    )
    session.add(correction)
    await session.flush()

    await record_audit_event(
        session, actor_id=actor_id, actor_role=actor_role,
        action="clinical.consultation_corrected", entity_type="Consultation", entity_id=str(correction.id),
        before_state={"original_id": str(original.id), "original_notes": original.notes},
        after_state={"notes": data.notes}, reason=data.correction_reason,
    )
    return correction
