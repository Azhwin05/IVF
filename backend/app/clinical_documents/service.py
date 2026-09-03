import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.service import record_audit_event
from app.clinical_documents.models import ConsentForm, ConsentFormStatus, MRDRecord
from app.clinical_documents.schemas import ConsentFormCreate, MRDRecordCreate
from app.core.exceptions import ConflictError, NotFoundError


async def create_consent_form(
    session: AsyncSession, data: ConsentFormCreate, *, actor_id: uuid.UUID, actor_role: str
) -> ConsentForm:
    form = ConsentForm(created_by_id=actor_id, **data.model_dump())
    session.add(form)
    await session.flush()

    await record_audit_event(
        session, actor_id=actor_id, actor_role=actor_role,
        action="clinical_documents.consent_form_created", entity_type="ConsentForm", entity_id=str(form.id),
        after_state={"form_type": data.form_type},
    )
    return form


async def sign_consent_form(session: AsyncSession, form_id: uuid.UUID, *, actor_id: uuid.UUID, actor_role: str) -> ConsentForm:
    form = await session.get(ConsentForm, form_id)
    if not form:
        raise NotFoundError("Consent form not found")
    if form.status != ConsentFormStatus.DRAFT:
        raise ConflictError("This consent form is not in a signable state.")

    form.status = ConsentFormStatus.SIGNED
    form.signed_at = datetime.now(timezone.utc)
    await session.flush()

    await record_audit_event(
        session, actor_id=actor_id, actor_role=actor_role,
        action="clinical_documents.consent_form_signed", entity_type="ConsentForm", entity_id=str(form.id),
    )
    return form


async def list_consent_forms(session: AsyncSession, patient_id: uuid.UUID) -> list[ConsentForm]:
    result = await session.execute(
        select(ConsentForm).where(ConsentForm.patient_id == patient_id).order_by(ConsentForm.created_at.desc())
    )
    return list(result.scalars().all())


async def create_mrd_record(
    session: AsyncSession, data: MRDRecordCreate, *, actor_id: uuid.UUID, actor_role: str
) -> MRDRecord:
    record = MRDRecord(created_by_id=actor_id, **data.model_dump())
    session.add(record)
    await session.flush()

    await record_audit_event(
        session, actor_id=actor_id, actor_role=actor_role,
        action="clinical_documents.mrd_record_created", entity_type="MRDRecord", entity_id=str(record.id),
        after_state={"record_type": data.record_type},
    )
    return record


async def list_mrd_records(session: AsyncSession, patient_id: uuid.UUID) -> list[MRDRecord]:
    result = await session.execute(
        select(MRDRecord).where(MRDRecord.patient_id == patient_id).order_by(MRDRecord.created_at.desc())
    )
    return list(result.scalars().all())
