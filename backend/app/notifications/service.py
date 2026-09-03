import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.notifications.models import Notification, NotificationTask, NotificationTone, TaskStatus
from app.notifications.schemas import TaskCreate


async def push_notification(
    session: AsyncSession, *, user_id: uuid.UUID, title: str, body: str | None, tone: NotificationTone,
    link_entity_type: str | None = None, link_entity_id: str | None = None,
) -> Notification:
    """Called by other modules' event handlers (see app/events -- workers
    consume the outbox and call this to fan events out to relevant users)."""
    notif = Notification(
        user_id=user_id, title=title, body=body, tone=tone,
        link_entity_type=link_entity_type, link_entity_id=link_entity_id,
    )
    session.add(notif)
    await session.flush()
    return notif


async def list_notifications(session: AsyncSession, user_id: uuid.UUID, *, unread_only: bool = False) -> list[Notification]:
    stmt = select(Notification).where(Notification.user_id == user_id).order_by(Notification.created_at.desc())
    if unread_only:
        stmt = stmt.where(Notification.is_read.is_(False))
    result = await session.execute(stmt.limit(50))
    return list(result.scalars().all())


async def mark_read(session: AsyncSession, notification_id: uuid.UUID) -> None:
    notif = await session.get(Notification, notification_id)
    if notif:
        notif.is_read = True
        await session.flush()


async def create_task(session: AsyncSession, data: TaskCreate, *, created_by_id: uuid.UUID | None = None) -> NotificationTask:
    task = NotificationTask(created_by_id=created_by_id, **data.model_dump())
    session.add(task)
    await session.flush()
    return task


async def list_patient_alerts(session: AsyncSession, patient_id: uuid.UUID) -> list[NotificationTask]:
    """New requirement (source doc §8) — patient-linked alerts view."""
    stmt = (
        select(NotificationTask)
        .where(NotificationTask.patient_id == patient_id)
        .order_by(NotificationTask.due_at.asc())
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def resolve_task(session: AsyncSession, task_id: uuid.UUID, resolution: str) -> NotificationTask:
    task = await session.get(NotificationTask, task_id)
    if not task:
        raise NotFoundError("Task not found")
    if task.status != TaskStatus.OPEN:
        raise ConflictError("This task is not open.")

    task.status = TaskStatus.DONE
    task.resolution = resolution
    await session.flush()
    return task


async def escalate_overdue_tasks(session: AsyncSession, *, escalate_to_id: uuid.UUID) -> int:
    """Called by Celery Beat — per spec §19: 'If unresolved: Escalate,
    Notify supervisor, Keep visible.'"""
    now = datetime.now(timezone.utc)
    result = await session.execute(
        select(NotificationTask).where(NotificationTask.status == TaskStatus.OPEN, NotificationTask.due_at < now)
    )
    overdue = result.scalars().all()
    for task in overdue:
        task.status = TaskStatus.ESCALATED
        task.escalated_to_id = escalate_to_id
        await push_notification(
            session, user_id=escalate_to_id, title=f"Escalated: {task.title}",
            body=task.detail, tone=NotificationTone.ATTENTION,
        )
    return len(overdue)
