import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.service import record_audit_event
from app.core.exceptions import NotFoundError, ValidationFailedError
from app.events.bus import EventType, emit
from app.inventory.models import InventoryItem, StockMovement, StockMovementType
from app.inventory.schemas import InventoryItemCreate, StockAdjustment


async def create_item(session: AsyncSession, data: InventoryItemCreate) -> InventoryItem:
    item = InventoryItem(**data.model_dump())
    session.add(item)
    await session.flush()
    return item


async def list_items(session: AsyncSession, *, category=None) -> list[InventoryItem]:
    stmt = select(InventoryItem).order_by(InventoryItem.name)
    if category:
        stmt = stmt.where(InventoryItem.category == category)
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def adjust_stock(
    session: AsyncSession, data: StockAdjustment, *, actor_id: uuid.UUID, actor_role: str
) -> InventoryItem:
    """Every stock change — restock, consumption, adjustment, write-off —
    goes through here so the movement ledger stays the single source of
    truth. Row-locked to prevent concurrent adjustments from producing a
    negative stock count (spec §33)."""
    result = await session.execute(select(InventoryItem).where(InventoryItem.id == data.item_id).with_for_update())
    item = result.scalar_one_or_none()
    if not item:
        raise NotFoundError("Inventory item not found")

    new_stock = item.stock + data.quantity_delta
    if new_stock < 0:
        raise ValidationFailedError(
            f"This adjustment would leave stock at {new_stock}, which is not allowed.",
            error_code="negative_stock_rejected",
        )

    item.stock = new_stock
    if data.movement_type == StockMovementType.RESTOCK:
        item.last_restocked = datetime.now(timezone.utc).date()

    session.add(StockMovement(
        item_id=item.id, movement_type=data.movement_type, quantity_delta=data.quantity_delta,
        reason=data.reason, performed_by_id=actor_id,
    ))
    await session.flush()

    await record_audit_event(
        session, actor_id=actor_id, actor_role=actor_role,
        action=f"inventory.stock_{data.movement_type.value}", entity_type="InventoryItem", entity_id=str(item.id),
        after_state={"new_stock": new_stock, "delta": data.quantity_delta}, reason=data.reason,
    )

    if item.stock <= item.reorder_level:
        await emit(
            session, event_type=EventType.STOCK_BELOW_REORDER_LEVEL, entity_type="InventoryItem", entity_id=str(item.id),
            payload={"item_id": str(item.id), "stock": item.stock, "reorder_level": item.reorder_level},
        )
    return item
