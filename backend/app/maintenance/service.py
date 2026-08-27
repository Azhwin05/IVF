import uuid
from datetime import date, datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.service import record_audit_event
from app.core.exceptions import NotFoundError
from app.events.bus import EventType, emit
from app.maintenance.models import MaintenanceStatus, MaintenanceTask
from app.maintenance.schemas import MaintenanceTaskCreate


async def create_task(session: AsyncSession, data: MaintenanceTaskCreate) -> MaintenanceTask:
    task = MaintenanceTask(**data.model_dump())
    session.add(task)
    await session.flush()
    return task


async def list_due_tasks(session: AsyncSession, *, within_days: int = 30) -> list[MaintenanceTask]:
    from datetime import timedelta
    cutoff = date.today() + timedelta(days=within_days)
    result = await session.execute(
        select(MaintenanceTask)
        .where(MaintenanceTask.due_date <= cutoff, MaintenanceTask.status != MaintenanceStatus.COMPLETED)
        .order_by(MaintenanceTask.due_date)
    )
    return list(result.scalars().all())


async def complete_task(
    session: AsyncSession, task_id: uuid.UUID, notes: str | None, *, actor_id: uuid.UUID, actor_role: str
) -> MaintenanceTask:
    task = await session.get(MaintenanceTask, task_id)
    if not task:
        raise NotFoundError("Maintenance task not found")

    task.status = MaintenanceStatus.COMPLETED
    task.completed_by_id = actor_id
    task.completed_date = date.today()
    task.notes = notes
    await session.flush()

    await record_audit_event(
        session, actor_id=actor_id, actor_role=actor_role,
        action="maintenance.task_completed", entity_type="MaintenanceTask", entity_id=str(task.id),
    )
    return task


async def flag_overdue_tasks(session: AsyncSession) -> int:
    """Called by Celery Beat daily — flips SCHEDULED/DUE tasks past their
    due_date to OVERDUE and emits a MaintenanceDue event for each."""
    result = await session.execute(
        select(MaintenanceTask).where(
            MaintenanceTask.due_date < date.today(), MaintenanceTask.status != MaintenanceStatus.COMPLETED
        )
    )
    tasks = result.scalars().all()
    for task in tasks:
        task.status = MaintenanceStatus.OVERDUE
        await emit(
            session, event_type=EventType.MAINTENANCE_DUE, entity_type="MaintenanceTask", entity_id=str(task.id),
            payload={"equipment_name": task.equipment_name, "due_date": task.due_date.isoformat()},
        )
    return len(tasks)
