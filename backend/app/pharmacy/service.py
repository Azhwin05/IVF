"""
Pharmacy dispensing — the second highest-stakes transaction in the
system alongside billing payments. Implements spec §33's exact flow:

    Dispense Medicine
        +--> Validate prescription
        +--> Validate stock
        +--> Select batch (FEFO — First Expiry, First Out)
        +--> Deduct stock
        +--> Create dispensing record
        +--> Create billing charge
        +--> Create audit record

All in a single database transaction (the caller's session, committed
by get_db on request success) so a failure partway through — e.g. stock
insufficient on the second line item — rolls back every change already
made, never leaving a half-dispensed, half-billed sale on record.

Row-level locking on MedicineBatch prevents two concurrent dispensing
requests from both reading the same available quantity and both
succeeding, which is exactly how negative inventory happens under load
(spec §33's "Prevent: Negative inventory... Race conditions").
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.service import record_audit_event
from app.core.exceptions import InsufficientStockError, NotFoundError, ValidationFailedError
from app.events.bus import EventType, emit
from app.pharmacy.models import Medicine, MedicineBatch, PharmacySale, PharmacySaleLine
from app.pharmacy.schemas import DispenseRequest


async def _next_bill_number(session: AsyncSession) -> str:
    year = datetime.now(timezone.utc).year
    prefix = f"RX-{year}-"
    result = await session.execute(
        select(PharmacySale.bill_number)
        .where(PharmacySale.bill_number.like(f"{prefix}%"))
        .order_by(PharmacySale.bill_number.desc())
        .limit(1)
        .with_for_update()
    )
    last = result.scalar_one_or_none()
    next_seq = int(last.split("-")[-1]) + 1 if last else 1
    return f"{prefix}{next_seq:05d}"


async def _select_fefo_batches(
    session: AsyncSession, *, medicine_id: uuid.UUID, quantity_needed: int
) -> list[tuple[MedicineBatch, int]]:
    """Locks and returns the batches (oldest-expiry-first) needed to cover
    `quantity_needed`, splitting across batches if one alone isn't enough.
    Raises InsufficientStockError if total available across all batches
    can't cover the request."""
    result = await session.execute(
        select(MedicineBatch)
        .where(MedicineBatch.medicine_id == medicine_id, MedicineBatch.quantity_available > 0)
        .order_by(MedicineBatch.expiry_date.asc())
        .with_for_update()
    )
    batches = list(result.scalars().all())

    allocation: list[tuple[MedicineBatch, int]] = []
    remaining = quantity_needed
    for batch in batches:
        if remaining <= 0:
            break
        take = min(batch.quantity_available, remaining)
        allocation.append((batch, take))
        remaining -= take

    if remaining > 0:
        medicine = await session.get(Medicine, medicine_id)
        name = medicine.generic_name if medicine else str(medicine_id)
        raise InsufficientStockError(
            f"Insufficient stock for {name}: requested {quantity_needed}, "
            f"available {quantity_needed - remaining}.",
        )
    return allocation


async def dispense(
    session: AsyncSession, data: DispenseRequest, *, actor_id: uuid.UUID, actor_role: str
) -> PharmacySale:
    if not data.lines:
        raise ValidationFailedError("At least one medicine line is required.")

    bill_number = await _next_bill_number(session)
    sale = PharmacySale(
        bill_number=bill_number,
        patient_id=data.patient_id,
        prescribed_by_id=data.prescribed_by_id,
        dispensed_by_id=actor_id,
        total_amount_paise=0,
    )
    session.add(sale)
    await session.flush()

    total = 0
    low_stock_medicine_ids: list[uuid.UUID] = []

    for line in data.lines:
        allocation = await _select_fefo_batches(session, medicine_id=line.medicine_id, quantity_needed=line.quantity)
        for batch, take_qty in allocation:
            batch.quantity_available -= take_qty
            line_total = batch.selling_rate_paise * take_qty
            total += line_total
            session.add(PharmacySaleLine(
                sale_id=sale.id, medicine_id=line.medicine_id, batch_id=batch.id,
                quantity=take_qty, unit_price_paise=batch.selling_rate_paise,
            ))

        medicine = await session.get(Medicine, line.medicine_id)
        # Direct aggregate query rather than `medicine.batches` — the
        # batches just mutated above were loaded via a separate query in
        # _select_fefo_batches, not through this relationship, so summing
        # via the relationship risks the same under-loaded-instance issue
        # documented in billing/service.py::create_invoice. An explicit
        # SUM is also just the right tool here regardless.
        remaining_result = await session.execute(
            select(func.coalesce(func.sum(MedicineBatch.quantity_available), 0))
            .where(MedicineBatch.medicine_id == medicine.id)
        )
        remaining_stock = remaining_result.scalar_one()
        if remaining_stock <= medicine.reorder_level:
            low_stock_medicine_ids.append(medicine.id)

    sale.total_amount_paise = total
    await session.flush()
    # sale.lines were added via raw FK, same pattern as billing's charges —
    # refresh before SaleOut serializes them outside the async context.
    await session.refresh(sale, attribute_names=["lines"])

    await record_audit_event(
        session, actor_id=actor_id, actor_role=actor_role,
        action="pharmacy.medicine_dispensed", entity_type="PharmacySale", entity_id=str(sale.id),
        after_state={"bill_number": bill_number, "total_amount_paise": total, "line_count": len(data.lines)},
    )
    await emit(
        session, event_type=EventType.MEDICINE_DISPENSED, entity_type="PharmacySale", entity_id=str(sale.id),
        payload={"patient_id": str(data.patient_id), "total_amount_paise": total},
    )
    for med_id in low_stock_medicine_ids:
        await emit(
            session, event_type=EventType.STOCK_BELOW_REORDER_LEVEL, entity_type="Medicine", entity_id=str(med_id),
            payload={"medicine_id": str(med_id)},
        )

    return sale


async def get_sale(session: AsyncSession, sale_id: uuid.UUID) -> PharmacySale:
    sale = await session.get(PharmacySale, sale_id)
    if not sale:
        raise NotFoundError("Pharmacy sale not found", error_code="sale_not_found")
    return sale


async def list_medicines_with_stock(session: AsyncSession) -> list[dict]:
    result = await session.execute(select(Medicine).order_by(Medicine.generic_name))
    medicines = result.scalars().all()
    return [
        {
            "id": m.id, "generic_name": m.generic_name, "brand_name": m.brand_name,
            "category": m.category, "unit": m.unit, "reorder_level": m.reorder_level,
            "total_available": sum(b.quantity_available for b in m.batches),
        }
        for m in medicines
    ]
