import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.service import record_audit_event
from app.core.exceptions import NotFoundError
from app.events.bus import EventType, emit
from app.patients.models import Couple, Patient
from app.patients.schemas import CoupleCreate, PatientCreate, PatientUpdate


async def generate_uhid(session: AsyncSession) -> str:
    """DAIVF-<year>-<sequence>, matching the existing frontend's UHID format
    (e.g. DAIVF-2026-00428). Sequence is derived from a row count within the
    year rather than a separate counter table, which is fine at this
    hospital's volume; revisit with a dedicated sequence if throughput grows."""
    year = datetime.now(timezone.utc).year
    prefix = f"DAIVF-{year}-"
    result = await session.execute(
        select(Patient.uhid).where(Patient.uhid.like(f"{prefix}%")).order_by(Patient.uhid.desc()).limit(1)
    )
    last = result.scalar_one_or_none()
    next_seq = int(last.split("-")[-1]) + 1 if last else 1
    return f"{prefix}{next_seq:05d}"


async def create_patient(session: AsyncSession, data: PatientCreate) -> Patient:
    patient = Patient(uhid=await generate_uhid(session), **data.model_dump())
    session.add(patient)
    await session.flush()
    return patient


async def get_patient(session: AsyncSession, patient_id: uuid.UUID) -> Patient:
    patient = await session.get(Patient, patient_id)
    if not patient:
        raise NotFoundError("Patient not found", error_code="patient_not_found")
    return patient


async def list_patients(session: AsyncSession, *, search: str | None = None, limit: int = 50) -> list[Patient]:
    stmt = select(Patient).order_by(Patient.created_at.desc()).limit(limit)
    if search:
        term = f"%{search.lower()}%"
        stmt = select(Patient).where(
            (Patient.full_name.ilike(term)) | (Patient.uhid.ilike(term)) | (Patient.phone.ilike(term))
        ).order_by(Patient.created_at.desc()).limit(limit)
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def update_patient(
    session: AsyncSession, patient_id: uuid.UUID, data: PatientUpdate, *, actor_id: uuid.UUID, actor_role: str
) -> Patient:
    patient = await get_patient(session, patient_id)
    before = {"full_name": patient.full_name, "phone": patient.phone, "email": patient.email}

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(patient, field, value)
    await session.flush()

    await record_audit_event(
        session, actor_id=actor_id, actor_role=actor_role,
        action="patient.updated", entity_type="Patient", entity_id=str(patient.id),
        before_state=before, after_state=data.model_dump(exclude_unset=True, mode="json"),
    )
    return patient


async def create_couple(
    session: AsyncSession, data: CoupleCreate, *, actor_id: uuid.UUID, actor_role: str
) -> Couple:
    female = await create_patient(session, data.female_patient)
    male = await create_patient(session, data.male_patient)

    couple = Couple(
        female_patient_id=female.id,
        male_patient_id=male.id,
        relationship_info=data.relationship_info,
        infertility_type=data.infertility_type,
        infertility_duration=data.infertility_duration,
        previous_iui_cycles=data.previous_iui_cycles,
        previous_ivf_cycles=data.previous_ivf_cycles,
        previous_treatment_notes=data.previous_treatment_notes,
    )
    session.add(couple)
    await session.flush()

    await record_audit_event(
        session, actor_id=actor_id, actor_role=actor_role,
        action="couple.created", entity_type="Couple", entity_id=str(couple.id),
        after_state={"female_uhid": female.uhid, "male_uhid": male.uhid},
    )
    await emit(
        session,
        event_type=EventType.PATIENT_REGISTERED,
        entity_type="Couple",
        entity_id=str(couple.id),
        payload={"female_patient_id": str(female.id), "male_patient_id": str(male.id)},
    )
    return couple


async def get_couple_for_patient(session: AsyncSession, patient_id: uuid.UUID) -> Couple | None:
    result = await session.execute(
        select(Couple).where(
            (Couple.female_patient_id == patient_id) | (Couple.male_patient_id == patient_id)
        )
    )
    return result.scalar_one_or_none()
