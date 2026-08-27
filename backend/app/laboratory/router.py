from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import require_permission
from app.laboratory import service
from app.laboratory.models import LabOrderStatus
from app.laboratory.schemas import LabOrderCreate, LabOrderOut, LabOrderStatusUpdate
from app.users.models import User

router = APIRouter(prefix="/laboratory", tags=["laboratory"])


@router.get("/orders", response_model=list[LabOrderOut])
async def list_orders(
    status: LabOrderStatus | None = None,
    session: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("laboratory.read")),
) -> list[LabOrderOut]:
    return await service.list_orders(session, status=status)


@router.post("/orders", response_model=LabOrderOut, status_code=201)
async def create_order(
    body: LabOrderCreate,
    session: AsyncSession = Depends(get_db),
    current: User = Depends(require_permission("laboratory.order")),
) -> LabOrderOut:
    return await service.create_order(session, body, actor_id=current.id, actor_role=current.role.code)


@router.post("/orders/{order_id}/status", response_model=LabOrderOut)
async def update_status(
    order_id: str,
    body: LabOrderStatusUpdate,
    session: AsyncSession = Depends(get_db),
    current: User = Depends(require_permission("laboratory.result")),
) -> LabOrderOut:
    return await service.update_order_status(session, order_id, body.status, actor_id=current.id, actor_role=current.role.code)
