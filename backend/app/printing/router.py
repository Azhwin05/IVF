from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import require_permission
from app.patients.service import get_patient
from app.printing import service
from app.users.models import User

router = APIRouter(prefix="/printing", tags=["printing"])


@router.get("/patients/{patient_id}/qr")
async def patient_qr(
    patient_id: str,
    session: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("patients.read")),
) -> Response:
    patient = await get_patient(session, patient_id)
    png = service.generate_qr_png(patient.uhid)
    return Response(content=png, media_type="image/png")


@router.get("/patients/{patient_id}/id-card")
async def patient_id_card(
    patient_id: str,
    session: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("patients.read")),
) -> Response:
    patient = await get_patient(session, patient_id)
    pdf = service.generate_patient_id_card(
        uhid=patient.uhid, full_name=patient.full_name, blood_group=patient.blood_group
    )
    return Response(content=pdf, media_type="application/pdf")
