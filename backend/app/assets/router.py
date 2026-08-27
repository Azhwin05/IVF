from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.assets import service
from app.assets.schemas import AssetCreate, AssetMovementOut, AssetMoveRequest, AssetOut
from app.core.database import get_db
from app.core.deps import require_permission
from app.users.models import User

router = APIRouter(prefix="/assets", tags=["assets"])


@router.post("", response_model=AssetOut, status_code=201)
async def create_asset(
    body: AssetCreate,
    session: AsyncSession = Depends(get_db),
    current: User = Depends(require_permission("assets.read")),
) -> AssetOut:
    return await service.create_asset(session, body, actor_id=current.id, actor_role=current.role.code)


@router.get("/by-code/{asset_code}", response_model=AssetOut)
async def get_by_code(
    asset_code: str,
    session: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("assets.read")),
) -> AssetOut:
    return await service.get_asset_by_code(session, asset_code)


@router.post("/{asset_id}/move", response_model=AssetOut)
async def move_asset(
    asset_id: str,
    body: AssetMoveRequest,
    session: AsyncSession = Depends(get_db),
    current: User = Depends(require_permission("assets.move")),
) -> AssetOut:
    return await service.move_asset(session, asset_id, body.to_location, body.notes, actor_id=current.id, actor_role=current.role.code)


@router.get("/{asset_id}/history", response_model=list[AssetMovementOut])
async def get_history(
    asset_id: str,
    session: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("assets.read")),
) -> list[AssetMovementOut]:
    return await service.get_movement_history(session, asset_id)
