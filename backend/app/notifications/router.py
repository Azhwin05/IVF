from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.notifications import service
from app.notifications.schemas import NotificationOut, TaskCreate, TaskOut, TaskResolve
from app.users.models import User

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=list[NotificationOut])
async def list_my_notifications(
    unread_only: bool = False,
    session: AsyncSession = Depends(get_db),
    current: User = Depends(get_current_user),
) -> list[NotificationOut]:
    return await service.list_notifications(session, current.id, unread_only=unread_only)


@router.post("/{notification_id}/read", status_code=204)
async def mark_read(
    notification_id: str,
    session: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> None:
    await service.mark_read(session, notification_id)


@router.post("/tasks", response_model=TaskOut, status_code=201)
async def create_task(
    body: TaskCreate,
    session: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> TaskOut:
    return await service.create_task(session, body)


@router.post("/tasks/{task_id}/resolve", response_model=TaskOut)
async def resolve_task(
    task_id: str,
    body: TaskResolve,
    session: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> TaskOut:
    return await service.resolve_task(session, task_id, body.resolution)
