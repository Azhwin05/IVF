import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.service import record_audit_event
from app.core.exceptions import NotFoundError
from app.laboratory.models import LabOrder, LabOrderStatus
from app.laboratory.schemas import LabOrderCreate


async def _next_order_number(session: AsyncSession) -> str:
    year = datetime.now(timezone.utc).year
    prefix = f"LAB-{year}-"
    result = await session.execute(
        select(LabOrder.order_number).where(LabOrder.order_number.like(f"{prefix}%"))
        .order_by(LabOrder.order_number.desc()).limit(1).with_for_update()
    )
    last = result.scalar_one_or_none()
    next_seq = int(last.split("-")[-1]) + 1 if last else 1
    return f"{prefix}{next_seq:05d}"


async def create_order(
    session: AsyncSession, data: LabOrderCreate, *, actor_id: uuid.UUID, actor_role: str
) -> LabOrder:
    order = LabOrder(order_number=await _next_order_number(session), ordered_by_id=actor_id, **data.model_dump())
    session.add(order)
    await session.flush()

    await record_audit_event(
        session, actor_id=actor_id, actor_role=actor_role,
        action="laboratory.order_created", entity_type="LabOrder", entity_id=str(order.id),
    )
    return order


async def list_orders(session: AsyncSession, *, status: LabOrderStatus | None = None) -> list[LabOrder]:
    stmt = select(LabOrder).order_by(LabOrder.created_at.desc())
    if status:
        stmt = stmt.where(LabOrder.status == status)
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def update_order_status(
    session: AsyncSession, order_id: uuid.UUID, status: LabOrderStatus, *, actor_id: uuid.UUID, actor_role: str
) -> LabOrder:
    order = await session.get(LabOrder, order_id)
    if not order:
        raise NotFoundError("Lab order not found")

    before = order.status.value
    order.status = status
    if status == LabOrderStatus.REPORT_READY:
        order.result_verified_by_id = actor_id
        order.result_verified_at = datetime.now(timezone.utc)
    await session.flush()

    await record_audit_event(
        session, actor_id=actor_id, actor_role=actor_role,
        action="laboratory.order_status_changed", entity_type="LabOrder", entity_id=str(order.id),
        before_state={"status": before}, after_state={"status": status.value},
    )
    return order
