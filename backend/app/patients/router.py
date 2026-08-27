from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import require_permission
from app.patients import service
from app.patients.schemas import (
    CoupleCreate,
    CoupleOut,
    PatientListRow,
    PatientSummary,
    PatientUpdate,
)
from app.users.models import User

router = APIRouter(prefix="/patients", tags=["patients"])


@router.get("", response_model=list[PatientListRow])
async def list_patients(
    search: str | None = Query(default=None),
    session: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("patients.read")),
) -> list[PatientListRow]:
    return await service.list_patients(session, search=search)


@router.get("/{patient_id}/summary", response_model=PatientSummary)
async def get_patient_summary(
    patient_id: str,
    session: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("patients.read")),
) -> PatientSummary:
    return await service.get_patient(session, patient_id)


@router.patch("/{patient_id}", response_model=PatientSummary)
async def update_patient(
    patient_id: str,
    body: PatientUpdate,
    session: AsyncSession = Depends(get_db),
    current: User = Depends(require_permission("patients.update")),
) -> PatientSummary:
    return await service.update_patient(session, patient_id, body, actor_id=current.id, actor_role=current.role.code)


@router.post("/couples", response_model=CoupleOut, status_code=201)
async def create_couple(
    body: CoupleCreate,
    session: AsyncSession = Depends(get_db),
    current: User = Depends(require_permission("patients.create")),
) -> CoupleOut:
    return await service.create_couple(session, body, actor_id=current.id, actor_role=current.role.code)


@router.get("/couples/by-patient/{patient_id}", response_model=CoupleOut | None)
async def get_couple_for_patient(
    patient_id: str,
    session: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("patients.read")),
) -> CoupleOut | None:
    return await service.get_couple_for_patient(session, patient_id)
