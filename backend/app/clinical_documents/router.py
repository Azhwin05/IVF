from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.clinical_documents import service
from app.clinical_documents.schemas import (
    ConsentFormCreate,
    ConsentFormOut,
    MRDRecordCreate,
    MRDRecordOut,
)
from app.core.database import get_db
from app.core.deps import require_permission
from app.users.models import User

router = APIRouter(prefix="/clinical-documents", tags=["clinical-documents"])


@router.post("/consent-forms", response_model=ConsentFormOut, status_code=201)
async def create_consent_form(
    body: ConsentFormCreate,
    session: AsyncSession = Depends(get_db),
    current: User = Depends(require_permission("clinical.write")),
) -> ConsentFormOut:
    return await service.create_consent_form(session, body, actor_id=current.id, actor_role=current.role.code)


@router.post("/consent-forms/{form_id}/sign", response_model=ConsentFormOut)
async def sign_consent_form(
    form_id: str,
    session: AsyncSession = Depends(get_db),
    current: User = Depends(require_permission("clinical.write")),
) -> ConsentFormOut:
    return await service.sign_consent_form(session, form_id, actor_id=current.id, actor_role=current.role.code)


@router.get("/consent-forms/by-patient/{patient_id}", response_model=list[ConsentFormOut])
async def list_consent_forms(
    patient_id: str,
    session: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("clinical.read")),
) -> list[ConsentFormOut]:
    return await service.list_consent_forms(session, patient_id)


@router.post("/mrd-records", response_model=MRDRecordOut, status_code=201)
async def create_mrd_record(
    body: MRDRecordCreate,
    session: AsyncSession = Depends(get_db),
    current: User = Depends(require_permission("clinical.write")),
) -> MRDRecordOut:
    return await service.create_mrd_record(session, body, actor_id=current.id, actor_role=current.role.code)


@router.get("/mrd-records/by-patient/{patient_id}", response_model=list[MRDRecordOut])
async def list_mrd_records(
    patient_id: str,
    session: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("clinical.read")),
) -> list[MRDRecordOut]:
    return await service.list_mrd_records(session, patient_id)
