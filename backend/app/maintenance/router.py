from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import require_permission
from app.maintenance import service
from app.maintenance.schemas import MaintenanceComplete, MaintenanceTaskCreate, MaintenanceTaskOut
from app.users.models import User

router = APIRouter(prefix="/maintenance", tags=["maintenance"])


@router.get("/tasks", response_model=list[MaintenanceTaskOut])
async def list_due(
    session: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("maintenance.read")),
) -> list[MaintenanceTaskOut]:
    return await service.list_due_tasks(session)


@router.post("/tasks", response_model=MaintenanceTaskOut, status_code=201)
async def create_task(
    body: MaintenanceTaskCreate,
    session: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("maintenance.read")),
) -> MaintenanceTaskOut:
    return await service.create_task(session, body)


@router.post("/tasks/{task_id}/complete", response_model=MaintenanceTaskOut)
async def complete_task(
    task_id: str,
    body: MaintenanceComplete,
    session: AsyncSession = Depends(get_db),
    current: User = Depends(require_permission("maintenance.complete")),
) -> MaintenanceTaskOut:
    return await service.complete_task(session, task_id, body.notes, actor_id=current.id, actor_role=current.role.code)
