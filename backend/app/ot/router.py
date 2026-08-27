from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import require_permission
from app.ot import service
from app.ot.schemas import ChecklistCreate, ChecklistOut, ProcedureCreate, ProcedureOut, ProcedureStatusUpdate
from app.users.models import User

router = APIRouter(prefix="/ot", tags=["ot"])


@router.post("/procedures", response_model=ProcedureOut, status_code=201)
async def schedule_procedure(
    body: ProcedureCreate,
    session: AsyncSession = Depends(get_db),
    current: User = Depends(require_permission("ot.schedule")),
) -> ProcedureOut:
    return await service.schedule_procedure(session, body, actor_id=current.id, actor_role=current.role.code)


@router.post("/procedures/{procedure_id}/status", response_model=ProcedureOut)
async def update_status(
    procedure_id: str,
    body: ProcedureStatusUpdate,
    session: AsyncSession = Depends(get_db),
    current: User = Depends(require_permission("ot.schedule")),
) -> ProcedureOut:
    return await service.update_procedure_status(session, procedure_id, body.status, actor_id=current.id, actor_role=current.role.code)


@router.post("/checklists", response_model=ChecklistOut, status_code=201)
async def create_checklist(
    body: ChecklistCreate,
    session: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("ot.checklist")),
) -> ChecklistOut:
    return await service.create_daily_checklist(session, body)


@router.post("/checklists/{checklist_id}/items/{item_index}", response_model=ChecklistOut)
async def update_checklist_item(
    checklist_id: str,
    item_index: int,
    status: str,
    issue: str | None = None,
    session: AsyncSession = Depends(get_db),
    current: User = Depends(require_permission("ot.checklist")),
) -> ChecklistOut:
    return await service.update_checklist_item(
        session, checklist_id, item_index, status, issue, actor_id=current.id, actor_role=current.role.code
    )
