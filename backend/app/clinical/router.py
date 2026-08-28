from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.clinical import service
from app.clinical.schemas import (
    ConsultationCorrection,
    ConsultationCreate,
    ConsultationOut,
    TimelineEventOut,
)
from app.core.database import get_db
from app.core.deps import require_permission
from app.users.models import User

router = APIRouter(prefix="/clinical", tags=["clinical"])


@router.get("/patients/{patient_id}/timeline", response_model=list[TimelineEventOut])
async def get_timeline(
    patient_id: str,
    session: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("patients.read")),
) -> list[TimelineEventOut]:
    return await service.get_patient_timeline(session, patient_id)


@router.get("/patients/{patient_id}/consultations", response_model=list[ConsultationOut])
async def get_consultations(
    patient_id: str,
    session: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("patients.read")),
) -> list[ConsultationOut]:
    return await service.list_consultations(session, patient_id)


@router.post("/consultations", response_model=ConsultationOut, status_code=201)
async def create_consultation(
    body: ConsultationCreate,
    session: AsyncSession = Depends(get_db),
    current: User = Depends(require_permission("clinical.write")),
) -> ConsultationOut:
    return await service.create_consultation(session, body, actor_id=current.id, actor_role=current.role.code)


@router.post("/consultations/correct", response_model=ConsultationOut, status_code=201)
async def correct_consultation(
    body: ConsultationCorrection,
    session: AsyncSession = Depends(get_db),
    current: User = Depends(require_permission("clinical.correct")),
) -> ConsultationOut:
    return await service.correct_consultation(session, body, actor_id=current.id, actor_role=current.role.code)
