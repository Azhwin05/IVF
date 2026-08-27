from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import require_permission
from app.hr import service
from app.hr.schemas import EmployeeCreate, EmployeeOut, LeaveRequestCreate, LeaveRequestOut
from app.users.models import User

router = APIRouter(prefix="/hr", tags=["hr"])


@router.get("/employees", response_model=list[EmployeeOut])
async def list_employees(
    session: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("hr.read")),
) -> list[EmployeeOut]:
    return await service.list_employees(session)


@router.post("/employees", response_model=EmployeeOut, status_code=201)
async def create_employee(
    body: EmployeeCreate,
    session: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("hr.write")),
) -> EmployeeOut:
    return await service.create_employee(session, body)


@router.post("/leave-requests", response_model=LeaveRequestOut, status_code=201)
async def submit_leave(
    body: LeaveRequestCreate,
    session: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("hr.read")),
) -> LeaveRequestOut:
    return await service.submit_leave_request(session, body)


@router.post("/leave-requests/{leave_id}/decide", response_model=LeaveRequestOut)
async def decide_leave(
    leave_id: str,
    approve: bool,
    session: AsyncSession = Depends(get_db),
    current: User = Depends(require_permission("hr.approve_leave")),
) -> LeaveRequestOut:
    return await service.decide_leave_request(session, leave_id, approve, actor_id=current.id, actor_role=current.role.code)
