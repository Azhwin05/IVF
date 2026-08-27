from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import require_permission
from app.inventory import service
from app.inventory.models import InventoryCategory
from app.inventory.schemas import InventoryItemCreate, InventoryItemOut, StockAdjustment
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
