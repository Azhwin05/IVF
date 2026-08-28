import uuid
from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.service import record_audit_event
from app.core.exceptions import ConflictError, NotFoundError
from app.events.bus import EventType, emit
from app.hr.models import Employee, LeaveRequest, LeaveStatus
from app.hr.schemas import EmployeeCreate, LeaveRequestCreate


async def create_employee(session: AsyncSession, data: EmployeeCreate) -> Employee:
    employee = Employee(**data.model_dump())
    session.add(employee)
    await session.flush()
    return employee


async def list_employees(session: AsyncSession) -> list[Employee]:
    result = await session.execute(select(Employee).order_by(Employee.full_name))
    return list(result.scalars().all())


async def list_leave_requests(session: AsyncSession) -> list[LeaveRequest]:
    result = await session.execute(select(LeaveRequest).order_by(LeaveRequest.created_at.desc()))
    return list(result.scalars().all())


async def submit_leave_request(session: AsyncSession, data: LeaveRequestCreate) -> LeaveRequest:
    days_requested = (data.to_date - data.from_date).days + 1
    employee = await session.get(Employee, data.employee_id)
    if not employee:
        raise NotFoundError("Employee not found")
    if days_requested > employee.leave_balance_days:
        raise ConflictError(
            f"Requested {days_requested} days but only {employee.leave_balance_days} remain.",
            error_code="insufficient_leave_balance",
        )

    leave = LeaveRequest(**data.model_dump())
    session.add(leave)
    await session.flush()

    await emit(
        session, event_type=EventType.LEAVE_REQUEST_SUBMITTED, entity_type="LeaveRequest", entity_id=str(leave.id),
        payload={"employee_id": str(data.employee_id), "days": days_requested},
    )
    return leave


async def decide_leave_request(
    session: AsyncSession, leave_id: uuid.UUID, approve: bool, *, actor_id: uuid.UUID, actor_role: str
) -> LeaveRequest:
    leave = await session.get(LeaveRequest, leave_id)
    if not leave:
        raise NotFoundError("Leave request not found")
    if leave.status != LeaveStatus.PENDING:
        raise ConflictError("This leave request has already been decided.")

    leave.status = LeaveStatus.APPROVED if approve else LeaveStatus.REJECTED
    leave.approved_by_id = actor_id

    if approve:
        employee = await session.get(Employee, leave.employee_id)
        days = (leave.to_date - leave.from_date).days + 1
        employee.leave_balance_days -= days

    await session.flush()
    await record_audit_event(
        session, actor_id=actor_id, actor_role=actor_role,
        action="hr.leave_decided", entity_type="LeaveRequest", entity_id=str(leave.id),
        after_state={"status": leave.status.value},
    )
    return leave
