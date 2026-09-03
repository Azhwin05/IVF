import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.service import record_audit_event
from app.core.exceptions import NotFoundError, ValidationFailedError
from app.messaging.models import (
    MessageCategory,
    MessageLog,
    MessageStatus,
    MessageTemplate,
    PatientCommsPreference,
)
from app.messaging.providers import get_provider
from app.messaging.schemas import CommsPreferenceUpdate, MessageTemplateCreate, SendMessageRequest
from app.patients.models import Patient


async def create_template(session: AsyncSession, data: MessageTemplateCreate) -> MessageTemplate:
    template = MessageTemplate(**data.model_dump())
    session.add(template)
    await session.flush()
    return template


async def list_templates(session: AsyncSession) -> list[MessageTemplate]:
    result = await session.execute(select(MessageTemplate).where(MessageTemplate.is_active.is_(True)))
    return list(result.scalars().all())


async def get_comms_preference(session: AsyncSession, patient_id: uuid.UUID) -> PatientCommsPreference:
    result = await session.execute(select(PatientCommsPreference).where(PatientCommsPreference.patient_id == patient_id))
    pref = result.scalar_one_or_none()
    if not pref:
        # Default is opt-out, per source doc §27's "consent/opt-in handling
        # where required" — a patient with no recorded preference has not
        # consented to promotional messaging.
        pref = PatientCommsPreference(patient_id=patient_id, promotional_opt_in=False)
        session.add(pref)
        await session.flush()
    return pref


async def update_comms_preference(
    session: AsyncSession, patient_id: uuid.UUID, data: CommsPreferenceUpdate, *, actor_id: uuid.UUID, actor_role: str
) -> PatientCommsPreference:
    pref = await get_comms_preference(session, patient_id)
    before = pref.promotional_opt_in
    pref.promotional_opt_in = data.promotional_opt_in
    pref.updated_by_id = actor_id
    await session.flush()

    await record_audit_event(
        session, actor_id=actor_id, actor_role=actor_role,
        action="messaging.comms_preference_updated", entity_type="PatientCommsPreference", entity_id=str(patient_id),
        before_state={"promotional_opt_in": before}, after_state={"promotional_opt_in": data.promotional_opt_in},
    )
    return pref


async def send_message(
    session: AsyncSession, data: SendMessageRequest, *, actor_id: uuid.UUID | None, actor_role: str | None
) -> MessageLog:
    """Transactional messages always send. Promotional messages are
    blocked unless the patient has opted in — source doc §27's consent
    requirement, enforced here so no future caller can accidentally skip
    the check by calling the provider directly (there is no other path to
    the provider — see providers.py)."""
    patient = await session.get(Patient, data.patient_id)
    if not patient or not patient.phone:
        raise NotFoundError("Patient not found or has no phone number on file")

    body = data.body
    template = None
    if data.template_id:
        template = await session.get(MessageTemplate, data.template_id)
        if not template:
            raise NotFoundError("Message template not found")
        body = template.body.replace("{{name}}", patient.full_name)
    if not body:
        raise ValidationFailedError("A message needs either a template_id or an explicit body.")

    if data.category == MessageCategory.PROMOTIONAL:
        pref = await get_comms_preference(session, data.patient_id)
        if not pref.promotional_opt_in:
            raise ValidationFailedError(
                "This patient has not opted in to promotional messages.",
                error_code="promotional_opt_out",
            )

    log = MessageLog(
        patient_id=data.patient_id, template_id=data.template_id, channel=data.channel,
        category=data.category, body=body, sent_by_id=actor_id,
    )
    session.add(log)
    await session.flush()

    provider = get_provider()
    success, provider_message_id, failure_reason = await provider.send(to_phone=patient.phone, body=body, channel=data.channel)
    log.status = MessageStatus.SENT if success else MessageStatus.FAILED
    log.provider_message_id = provider_message_id
    log.failure_reason = failure_reason
    if success:
        log.sent_at = datetime.now(timezone.utc)
    await session.flush()

    await record_audit_event(
        session, actor_id=actor_id, actor_role=actor_role or "system",
        action="messaging.message_sent" if success else "messaging.message_failed",
        entity_type="MessageLog", entity_id=str(log.id),
        after_state={"channel": data.channel.value, "category": data.category.value, "status": log.status.value},
    )
    return log


async def list_message_history(session: AsyncSession, patient_id: uuid.UUID) -> list[MessageLog]:
    result = await session.execute(
        select(MessageLog).where(MessageLog.patient_id == patient_id).order_by(MessageLog.created_at.desc())
    )
    return list(result.scalars().all())
