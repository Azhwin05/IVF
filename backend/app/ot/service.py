import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.service import record_audit_event
from app.core.exceptions import ConflictError, NotFoundError, ValidationFailedError
from app.events.bus import EventType, emit
from app.ot.models import Procedure, ProcedureStatus, ReadinessChecklist
from app.ot.schemas import ChecklistCreate, ProcedureCreate


async def schedule_procedure(
    session: AsyncSession, data: ProcedureCreate, *, actor_id: uuid.UUID, actor_role: str
) -> Procedure:
    procedure = Procedure(**data.model_dump())
    session.add(procedure)
    await session.flush()

    await record_audit_event(
        session, actor_id=actor_id, actor_role=actor_role,
        action="ot.procedure_scheduled", entity_type="Procedure", entity_id=str(procedure.id),
    )
    return procedure


async def update_procedure_status(
    session: AsyncSession, procedure_id: uuid.UUID, status: ProcedureStatus, *, actor_id: uuid.UUID, actor_role: str
) -> Procedure:
    procedure = await session.get(Procedure, procedure_id)
    if not procedure:
        raise NotFoundError("Procedure not found")

    if status == ProcedureStatus.IN_PROGRESS and not procedure.consent_verified:
        raise ValidationFailedError("Cannot start a procedure without verified consent.")

    before = procedure.status.value
    procedure.status = status
    await session.flush()

    await record_audit_event(
        session, actor_id=actor_id, actor_role=actor_role,
        action="ot.procedure_status_changed", entity_type="Procedure", entity_id=str(procedure.id),
        before_state={"status": before}, after_state={"status": status.value},
    )
    return procedure


async def create_daily_checklist(session: AsyncSession, data: ChecklistCreate) -> ReadinessChecklist:
    """Called by the daily Celery Beat job per department — always creates
    a NEW instance, never reuses yesterday's row (spec §22: 'Do not simply
    mark recurring tasks complete. Generate a new scheduled instance.')."""
    checklist = ReadinessChecklist(
        department=data.department, checklist_date=data.checklist_date,
        items=[item.model_dump() for item in data.items],
    )
    session.add(checklist)
    await session.flush()
    return checklist


async def update_checklist_item(
    session: AsyncSession, checklist_id: uuid.UUID, item_index: int, status: str, issue: str | None,
    *, actor_id: uuid.UUID, actor_role: str,
) -> ReadinessChecklist:
    checklist = await session.get(ReadinessChecklist, checklist_id)
    if not checklist:
        raise NotFoundError("Checklist not found")
    if item_index >= len(checklist.items):
        raise ConflictError("Invalid checklist item index.")

    items = list(checklist.items)
    items[item_index] = {**items[item_index], "status": status, "issue": issue, "checked_by": str(actor_id)}
    checklist.items = items
    await session.flush()

    if status == "issue":
        await emit(
            session, event_type=EventType.OT_CHECKLIST_INCOMPLETE, entity_type="ReadinessChecklist",
            entity_id=str(checklist.id), payload={"item": items[item_index]["item"], "issue": issue},
        )
    return checklist
