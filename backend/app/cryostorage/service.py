import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.service import record_audit_event
from app.clinical.models import TimelineEventType
from app.clinical.service import add_timeline_event
from app.core.exceptions import ConflictError, NotFoundError, ValidationFailedError
from app.cryostorage.models import (
    TRANSFER_CHECKLIST_ITEMS,
    CryoCustodyEvent,
    CryoLocation,
    EmbryoTransfer,
    TransferChecklistItem,
)
from app.cryostorage.schemas import CryoLocationCreate, CryoMoveRequest, TransferCreate
from app.embryology.models import Embryo, EmbryoStatus
from app.events.bus import EventType, emit
from app.ivf.service import get_cycle
from app.patients.models import Couple


async def store_embryo(
    session: AsyncSession, data: CryoLocationCreate, *, actor_id: uuid.UUID, actor_role: str
) -> CryoLocation:
    location = CryoLocation(**data.model_dump())
    session.add(location)
    await session.flush()

    embryo = await session.get(Embryo, data.embryo_id)
    embryo.status = EmbryoStatus.CRYOPRESERVED

    session.add(CryoCustodyEvent(
        location_id=location.id, embryo_id=data.embryo_id, event_type="vitrified",
        performed_by_id=actor_id, occurred_at=datetime.now(timezone.utc),
    ))
    await session.flush()

    await record_audit_event(
        session, actor_id=actor_id, actor_role=actor_role,
        action="cryostorage.embryo_stored", entity_type="CryoLocation", entity_id=str(location.id),
        after_state={"address": f"{data.tank}/{data.canister}/{data.cane}/{data.goblet}/{data.straw}"},
    )
    return location


async def move_embryo(
    session: AsyncSession, data: CryoMoveRequest, *, actor_id: uuid.UUID, actor_role: str
) -> CryoLocation:
    """Critical action — requires cryostorage.move permission at the router.
    Deactivates the old location row and creates a new one rather than
    mutating the address in place, so the full physical history stays
    queryable (per spec §20: 'Movement history must be immutable')."""
    old_location = await session.get(CryoLocation, data.location_id)
    if not old_location or not old_location.is_active:
        raise NotFoundError("Active cryostorage location not found")

    old_location.is_active = False

    new_location = CryoLocation(
        tank=data.new_tank, canister=data.new_canister, cane=data.new_cane,
        goblet=data.new_goblet, straw=data.new_straw,
        embryo_id=old_location.embryo_id, frozen_at=old_location.frozen_at,
        consent_verified=old_location.consent_verified, renewal_due=old_location.renewal_due,
    )
    session.add(new_location)
    await session.flush()

    session.add(CryoCustodyEvent(
        location_id=new_location.id, embryo_id=old_location.embryo_id, event_type="moved",
        performed_by_id=actor_id, witnessed_by_id=data.witnessed_by_id,
        occurred_at=datetime.now(timezone.utc), notes=data.notes,
    ))
    await session.flush()

    await record_audit_event(
        session, actor_id=actor_id, actor_role=actor_role,
        action="cryostorage.embryo_moved", entity_type="CryoLocation", entity_id=str(new_location.id),
        before_state={"from": str(old_location.id)}, after_state={"to": str(new_location.id)}, reason=data.notes,
    )
    await emit(
        session, event_type=EventType.CRYO_MOVEMENT_RECORDED, entity_type="CryoLocation", entity_id=str(new_location.id),
        payload={"embryo_id": str(old_location.embryo_id)},
    )
    return new_location


async def list_locations_for_cycle(session: AsyncSession, cycle_id: uuid.UUID) -> list[CryoLocation]:
    """Powers the Cryostorage tank view and the per-embryo storage address
    shown on the Embryology screen — both need "where is this cycle's
    embryo cohort actually stored" without a separate lookup per embryo."""
    result = await session.execute(
        select(CryoLocation).join(Embryo, CryoLocation.embryo_id == Embryo.id).where(Embryo.cycle_id == cycle_id)
    )
    return list(result.scalars().all())


async def get_custody_history(session: AsyncSession, embryo_id: uuid.UUID) -> list[CryoCustodyEvent]:
    result = await session.execute(
        select(CryoCustodyEvent).where(CryoCustodyEvent.embryo_id == embryo_id).order_by(CryoCustodyEvent.occurred_at)
    )
    return list(result.scalars().all())


# ---------------------------------------------------------------------------
# Embryo Transfer — 6-point checklist workflow
# ---------------------------------------------------------------------------

async def initiate_transfer(
    session: AsyncSession, data: TransferCreate, *, actor_id: uuid.UUID, actor_role: str
) -> EmbryoTransfer:
    transfer = EmbryoTransfer(**data.model_dump())
    session.add(transfer)
    await session.flush()

    for code, label in TRANSFER_CHECKLIST_ITEMS:
        session.add(TransferChecklistItem(transfer_id=transfer.id, item_code=code, label=label))
    await session.flush()
    # See billing/service.py::create_invoice's comment on the same pattern —
    # checklist items were added via raw FK, so the relationship needs an
    # explicit refresh before TransferOut can serialize it safely.
    await session.refresh(transfer, attribute_names=["checklist"])

    await record_audit_event(
        session, actor_id=actor_id, actor_role=actor_role,
        action="cryostorage.transfer_initiated", entity_type="EmbryoTransfer", entity_id=str(transfer.id),
    )
    return transfer


async def check_transfer_item(
    session: AsyncSession, transfer_id: uuid.UUID, item_code: str, *, actor_id: uuid.UUID, actor_role: str
) -> TransferChecklistItem:
    result = await session.execute(
        select(TransferChecklistItem).where(
            TransferChecklistItem.transfer_id == transfer_id, TransferChecklistItem.item_code == item_code
        )
    )
    item = result.scalar_one_or_none()
    if not item:
        raise NotFoundError("Checklist item not found")

    item.checked = True
    item.checked_by_id = actor_id
    item.checked_at = datetime.now(timezone.utc)
    await session.flush()
    return item


async def complete_transfer(
    session: AsyncSession, transfer_id: uuid.UUID, *, actor_id: uuid.UUID, actor_role: str
) -> EmbryoTransfer:
    """Server-side enforced gate: ALL 6 checklist items must be checked
    before this succeeds — this is the load-bearing guarantee behind the
    frontend's checklist UI (spec §6: 'Critical actions... must not be
    silently editable'). Requires embryology.transfer permission."""
    result = await session.execute(
        select(EmbryoTransfer).where(EmbryoTransfer.id == transfer_id)
    )
    transfer = result.scalar_one_or_none()
    if not transfer:
        raise NotFoundError("Transfer not found")
    if transfer.completed:
        raise ConflictError("This transfer has already been completed.")

    unchecked = [item for item in transfer.checklist if not item.checked]
    if unchecked:
        raise ValidationFailedError(
            f"Cannot complete transfer — unchecked items: {', '.join(i.label for i in unchecked)}",
            error_code="checklist_incomplete",
        )

    transfer.completed = True
    transfer.completed_at = datetime.now(timezone.utc)

    embryo = await session.get(Embryo, transfer.embryo_id)
    embryo.status = EmbryoStatus.TRANSFERRED
    await session.flush()

    cycle = await get_cycle(session, transfer.cycle_id)
    couple_result = await session.execute(select(Couple).where(Couple.id == cycle.couple_id))
    couple = couple_result.scalar_one()
    await add_timeline_event(
        session, patient_id=couple.female_patient_id, couple_id=couple.id,
        event_type=TimelineEventType.EMBRYO_TRANSFER, title="Embryo Transfer Completed",
        summary=f"Embryo {embryo.label} transferred", source_entity_type="EmbryoTransfer", source_entity_id=str(transfer.id),
    )
    await record_audit_event(
        session, actor_id=actor_id, actor_role=actor_role,
        action="cryostorage.transfer_completed", entity_type="EmbryoTransfer", entity_id=str(transfer.id),
    )
    await emit(
        session, event_type=EventType.EMBRYO_TRANSFER_COMPLETED, entity_type="EmbryoTransfer", entity_id=str(transfer.id),
        payload={"cycle_id": str(transfer.cycle_id), "embryo_id": str(transfer.embryo_id)},
    )
    return transfer
