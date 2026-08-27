from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import require_permission
from app.cryostorage import service
from app.cryostorage.schemas import (
    CryoLocationCreate,
    CryoLocationOut,
    CryoMoveRequest,
    CustodyEventOut,
    TransferCreate,
    TransferOut,
)
from app.users.models import User

router = APIRouter(prefix="/cryostorage", tags=["cryostorage"])


@router.post("/locations", response_model=CryoLocationOut, status_code=201)
async def store_embryo(
    body: CryoLocationCreate,
    session: AsyncSession = Depends(get_db),
    current: User = Depends(require_permission("cryostorage.move")),
) -> CryoLocationOut:
    return await service.store_embryo(session, body, actor_id=current.id, actor_role=current.role.code)


@router.post("/locations/move", response_model=CryoLocationOut)
async def move_embryo(
    body: CryoMoveRequest,
    session: AsyncSession = Depends(get_db),
    current: User = Depends(require_permission("cryostorage.move")),
) -> CryoLocationOut:
    return await service.move_embryo(session, body, actor_id=current.id, actor_role=current.role.code)


@router.get("/locations/by-cycle/{cycle_id}", response_model=list[CryoLocationOut])
async def list_locations_for_cycle(
    cycle_id: str,
    session: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("cryostorage.read")),
) -> list[CryoLocationOut]:
    return await service.list_locations_for_cycle(session, cycle_id)


@router.get("/custody/{embryo_id}", response_model=list[CustodyEventOut])
async def get_custody_history(
    embryo_id: str,
    session: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("cryostorage.read")),
) -> list[CustodyEventOut]:
    return await service.get_custody_history(session, embryo_id)


@router.post("/transfers", response_model=TransferOut, status_code=201)
async def initiate_transfer(
    body: TransferCreate,
    session: AsyncSession = Depends(get_db),
    current: User = Depends(require_permission("embryology.transfer")),
) -> TransferOut:
    return await service.initiate_transfer(session, body, actor_id=current.id, actor_role=current.role.code)


@router.post("/transfers/{transfer_id}/checklist/{item_code}", status_code=204)
async def check_item(
    transfer_id: str,
    item_code: str,
    session: AsyncSession = Depends(get_db),
    current: User = Depends(require_permission("embryology.transfer")),
) -> None:
    await service.check_transfer_item(session, transfer_id, item_code, actor_id=current.id, actor_role=current.role.code)


@router.post("/transfers/{transfer_id}/complete", response_model=TransferOut)
async def complete_transfer(
    transfer_id: str,
    session: AsyncSession = Depends(get_db),
    current: User = Depends(require_permission("embryology.transfer")),
) -> TransferOut:
    return await service.complete_transfer(session, transfer_id, actor_id=current.id, actor_role=current.role.code)
