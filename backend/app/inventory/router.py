import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import require_permission
from app.inventory import service
from app.inventory.models import InventoryCategory
from app.inventory.schemas import (
    InventoryItemCreate,
    InventoryItemOut,
    ProcedureReadinessCheck,
    StockAdjustment,
    StockReservationCreate,
    StockReservationOut,
)
from app.users.models import User

router = APIRouter(prefix="/inventory", tags=["inventory"])


@router.get("/items", response_model=list[InventoryItemOut])
async def list_items(
    category: InventoryCategory | None = None,
    session: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("inventory.read")),
) -> list[InventoryItemOut]:
    return await service.list_items(session, category=category)


@router.post("/items", response_model=InventoryItemOut, status_code=201)
async def create_item(
    body: InventoryItemCreate,
    session: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("inventory.adjust")),
) -> InventoryItemOut:
    return await service.create_item(session, body)


@router.post("/adjust", response_model=InventoryItemOut)
async def adjust_stock(
    body: StockAdjustment,
    session: AsyncSession = Depends(get_db),
    current: User = Depends(require_permission("inventory.adjust")),
) -> InventoryItemOut:
    return await service.adjust_stock(session, body, actor_id=current.id, actor_role=current.role.code)


@router.post("/reservations", response_model=StockReservationOut, status_code=201)
async def reserve_stock(
    body: StockReservationCreate,
    session: AsyncSession = Depends(get_db),
    current: User = Depends(require_permission("inventory.adjust")),
) -> StockReservationOut:
    return await service.reserve_stock(session, body, actor_id=current.id, actor_role=current.role.code)


@router.post("/reservations/{reservation_id}/release", response_model=StockReservationOut)
async def release_reservation(
    reservation_id: str,
    consumed: bool = False,
    session: AsyncSession = Depends(get_db),
    current: User = Depends(require_permission("inventory.adjust")),
) -> StockReservationOut:
    return await service.release_reservation(session, reservation_id, consumed=consumed, actor_id=current.id, actor_role=current.role.code)


@router.post("/readiness-check", response_model=ProcedureReadinessCheck)
async def readiness_check(
    requirements: dict[str, int],
    session: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("inventory.read")),
) -> ProcedureReadinessCheck:
    """Body: {"<item_id>": required_quantity, ...}"""
    pairs = [(uuid.UUID(k), v) for k, v in requirements.items()]
    ready, shortages = await service.check_procedure_readiness(session, pairs)
    return ProcedureReadinessCheck(ready=ready, shortages=shortages)
