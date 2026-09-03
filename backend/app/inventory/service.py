import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.service import record_audit_event
from app.core.exceptions import NotFoundError, ValidationFailedError
from app.events.bus import EventType, emit
from app.inventory.models import InventoryItem, ReservationStatus, StockMovement, StockMovementType, StockReservation
from app.inventory.schemas import InventoryItemCreate, StockAdjustment, StockReservationCreate


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


async def reserve_stock(
    session: AsyncSession, data: StockReservationCreate, *, actor_id: uuid.UUID, actor_role: str
) -> StockReservation:
    """New requirement (source doc §13) — hold stock against an upcoming
    procedure. Row-locked like adjust_stock so concurrent reservations
    can't both succeed against the same limited stock."""
    result = await session.execute(select(InventoryItem).where(InventoryItem.id == data.item_id).with_for_update())
    item = result.scalar_one_or_none()
    if not item:
        raise NotFoundError("Inventory item not found")

    if item.available_qty < data.quantity:
        raise ValidationFailedError(
            f"Only {item.available_qty} {item.unit} of {item.name} available (requested {data.quantity}).",
            error_code="insufficient_stock",
        )

    item.reserved_qty += data.quantity
    reservation = StockReservation(reserved_by_id=actor_id, **data.model_dump())
    session.add(reservation)
    await session.flush()

    await record_audit_event(
        session, actor_id=actor_id, actor_role=actor_role,
        action="inventory.stock_reserved", entity_type="StockReservation", entity_id=str(reservation.id),
        after_state={"item_id": str(item.id), "quantity": data.quantity, "procedure": f"{data.procedure_entity_type}:{data.procedure_entity_id}"},
    )
    return reservation


async def release_reservation(
    session: AsyncSession, reservation_id: uuid.UUID, *, consumed: bool, actor_id: uuid.UUID, actor_role: str
) -> StockReservation:
    """Called when a procedure is cancelled (consumed=False, stock freed
    back up) or completed (consumed=True, stock is permanently deducted
    via a normal StockMovement so the ledger stays the single source of
    truth for what actually left the shelf)."""
    reservation = await session.get(StockReservation, reservation_id)
    if not reservation:
        raise NotFoundError("Reservation not found")
    if reservation.status != ReservationStatus.HELD:
        raise ValidationFailedError("This reservation is no longer held.", error_code="reservation_not_held")

    result = await session.execute(select(InventoryItem).where(InventoryItem.id == reservation.item_id).with_for_update())
    item = result.scalar_one()
    item.reserved_qty -= reservation.quantity

    if consumed:
        reservation.status = ReservationStatus.CONSUMED
        item.stock -= reservation.quantity
        session.add(StockMovement(
            item_id=item.id, movement_type=StockMovementType.CONSUMED, quantity_delta=-reservation.quantity,
            reason=f"Consumed for {reservation.procedure_entity_type}:{reservation.procedure_entity_id}",
            performed_by_id=actor_id,
        ))
    else:
        reservation.status = ReservationStatus.RELEASED
    await session.flush()

    await record_audit_event(
        session, actor_id=actor_id, actor_role=actor_role,
        action="inventory.reservation_consumed" if consumed else "inventory.reservation_released",
        entity_type="StockReservation", entity_id=str(reservation.id),
    )
    return reservation


async def check_procedure_readiness(
    session: AsyncSession, requirements: list[tuple[uuid.UUID, int]]
) -> tuple[bool, list[dict]]:
    """requirements: [(item_id, required_quantity), ...]. Returns
    (ready, shortages) — reused by whatever module calls it (OT, IVF
    retrieval scheduling) so there's exactly one readiness-check
    implementation, not one per caller."""
    shortages: list[dict] = []
    for item_id, required in requirements:
        item = await session.get(InventoryItem, item_id)
        if not item or item.available_qty < required:
            shortages.append({
                "item_id": str(item_id),
                "name": item.name if item else "Unknown item",
                "required": required,
                "available": item.available_qty if item else 0,
            })
    return (len(shortages) == 0, shortages)
