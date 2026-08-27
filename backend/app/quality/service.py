import uuid
from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.service import record_audit_event
from app.core.exceptions import NotFoundError
from app.quality.models import QATaskInstance, QATaskTemplate
from app.quality.schemas import QATemplateCreate


async def create_template(session: AsyncSession, data: QATemplateCreate) -> QATaskTemplate:
    template = QATaskTemplate(**data.model_dump())
    session.add(template)
    await session.flush()
    return template


async def generate_instance_for_template(session: AsyncSession, template_id: uuid.UUID, due_date: date) -> QATaskInstance:
    """Called by the scheduler per template's frequency — always a NEW
    instance, per spec §22."""
    instance = QATaskInstance(template_id=template_id, due_date=due_date)
    session.add(instance)
    await session.flush()
    return instance


async def list_open_instances(session: AsyncSession) -> list[QATaskInstance]:
    result = await session.execute(
        select(QATaskInstance).where(QATaskInstance.completed.is_(False)).order_by(QATaskInstance.due_date)
    )
    return list(result.scalars().all())


async def complete_instance(
    session: AsyncSession, instance_id: uuid.UUID, *, actor_id: uuid.UUID, actor_role: str
) -> QATaskInstance:
    instance = await session.get(QATaskInstance, instance_id)
    if not instance:
        raise NotFoundError("QA task instance not found")

    instance.completed = True
    instance.completed_by_id = actor_id
    await session.flush()

    await record_audit_event(
        session, actor_id=actor_id, actor_role=actor_role,
        action="quality.task_completed", entity_type="QATaskInstance", entity_id=str(instance.id),
    )
    return instance
