from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import require_permission
from app.prescription import service
from app.prescription.schemas import PrescriptionCreate, PrescriptionOut
from app.users.models import User

router = APIRouter(prefix="/prescriptions", tags=["prescriptions"])


@router.post("", response_model=PrescriptionOut, status_code=201)
async def create_prescription(
    body: PrescriptionCreate,
    session: AsyncSession = Depends(get_db),
    current: User = Depends(require_permission("clinical.write")),
) -> PrescriptionOut:
    return await service.create_prescription(session, body, actor_id=current.id, actor_role=current.role.code)


@router.get("/{prescription_id}", response_model=PrescriptionOut)
async def get_prescription(
    prescription_id: str,
    session: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("clinical.read")),
) -> PrescriptionOut:
    return await service.get_prescription(session, prescription_id)


@router.get("/by-patient/{patient_id}", response_model=list[PrescriptionOut])
async def list_prescriptions(
    patient_id: str,
    session: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("clinical.read")),
) -> list[PrescriptionOut]:
    return await service.list_prescriptions_for_patient(session, patient_id)
