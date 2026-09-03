from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.service import record_audit_event
from app.core.database import get_db
from app.core.deps import require_permission
from app.patients.service import get_patient
from app.printing import service
from app.printing.schemas import PrintLogOut
from app.users.models import User

router = APIRouter(prefix="/printing", tags=["printing"])


@router.get("/patients/{patient_id}/qr")
async def patient_qr(
    patient_id: str,
    session: AsyncSession = Depends(get_db),
    current: User = Depends(require_permission("patients.read")),
) -> Response:
    patient = await get_patient(session, patient_id)
    png = service.generate_qr_png(patient.uhid)
    await service.record_print_event(
        session, document_type="qr", printed_by_id=current.id, patient_id=patient.id
    )
    await record_audit_event(
        session, actor_id=current.id, actor_role=current.role.code,
        action="printing.qr_printed", entity_type="Patient", entity_id=str(patient.id),
    )
    return Response(content=png, media_type="image/png")


@router.get("/patients/{patient_id}/id-card")
async def patient_id_card(
    patient_id: str,
    session: AsyncSession = Depends(get_db),
    current: User = Depends(require_permission("patients.read")),
) -> Response:
    patient = await get_patient(session, patient_id)
    pdf = service.generate_patient_id_card(
        uhid=patient.uhid, full_name=patient.full_name, blood_group=patient.blood_group
    )
    await service.record_print_event(
        session, document_type="patient_id_card", printed_by_id=current.id, patient_id=patient.id
    )
    await record_audit_event(
        session, actor_id=current.id, actor_role=current.role.code,
        action="printing.id_card_printed", entity_type="Patient", entity_id=str(patient.id),
    )
    return Response(content=pdf, media_type="application/pdf")


@router.get("/history", response_model=list[PrintLogOut])
async def print_history(
    patient_id: str | None = None,
    session: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("audit.read")),
) -> list[PrintLogOut]:
    """Consolidated 'who printed what, when' view — source doc §5."""
    return await service.list_print_history(session, patient_id=patient_id)
