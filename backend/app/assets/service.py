import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.assets.models import Asset, AssetMovement
from app.assets.schemas import AssetCreate
from app.audit.service import record_audit_event
from app.core.exceptions import NotFoundError
from app.events.bus import EventType, emit


async def _next_asset_code(session: AsyncSession) -> str:
    result = await session.execute(
        select(Asset.asset_code).order_by(Asset.created_at.desc()).limit(1).with_for_update()
    )
    last = result.scalar_one_or_none()
    next_seq = int(last.split("-")[-1]) + 1 if last else 1
    return f"AST-{next_seq:06d}"


async def create_asset(session: AsyncSession, data: AssetCreate, *, actor_id: uuid.UUID, actor_role: str) -> Asset:
    asset = Asset(asset_code=await _next_asset_code(session), **data.model_dump())
    session.add(asset)
    await session.flush()

    await record_audit_event(
        session, actor_id=actor_id, actor_role=actor_role,
        action="assets.created", entity_type="Asset", entity_id=str(asset.id),
    )
    return asset


async def get_asset_by_code(session: AsyncSession, asset_code: str) -> Asset:
    """Powers the QR-scan lookup flow (spec §20: 'Scan QR -> View Asset')."""
    result = await session.execute(select(Asset).where(Asset.asset_code == asset_code))
    asset = result.scalar_one_or_none()
    if not asset:
        raise NotFoundError("Asset not found for this QR code", error_code="asset_not_found")
    return asset


async def move_asset(
    session: AsyncSession, asset_id: uuid.UUID, to_location: str, notes: str | None, *, actor_id: uuid.UUID, actor_role: str
) -> Asset:
    asset = await session.get(Asset, asset_id)
    if not asset:
        raise NotFoundError("Asset not found")

    from_location = asset.current_location
    asset.current_location = to_location
    session.add(AssetMovement(
        asset_id=asset.id, event_type="move", from_location=from_location, to_location=to_location,
        notes=notes, performed_by_id=actor_id, occurred_at=datetime.now(timezone.utc),
    ))
    await session.flush()

    await record_audit_event(
        session, actor_id=actor_id, actor_role=actor_role,
        action="assets.moved", entity_type="Asset", entity_id=str(asset.id),
        before_state={"location": from_location}, after_state={"location": to_location},
    )
    await emit(
        session, event_type=EventType.ASSET_MOVED, entity_type="Asset", entity_id=str(asset.id),
        payload={"to_location": to_location},
    )
    return asset


async def get_movement_history(session: AsyncSession, asset_id: uuid.UUID) -> list[AssetMovement]:
    result = await session.execute(
        select(AssetMovement).where(AssetMovement.asset_id == asset_id).order_by(AssetMovement.occurred_at)
    )
    return list(result.scalars().all())
