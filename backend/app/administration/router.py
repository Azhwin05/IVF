from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.administration import service
from app.administration.schemas import (
    LabTestCreate,
    LabTestOut,
    PackageCreate,
    PackageOut,
    ProcedureChargeCreate,
    ProcedureChargeOut,
)
from app.core.database import get_db
from app.core.deps import require_permission
from app.users.models import User

router = APIRouter(prefix="/administration", tags=["administration"])


@router.get("/procedure-charges", response_model=list[ProcedureChargeOut])
async def list_charges(
    session: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("admin.manage_settings")),
) -> list[ProcedureChargeOut]:
    return await service.list_procedure_charges(session)


@router.post("/procedure-charges", response_model=ProcedureChargeOut, status_code=201)
async def create_charge(
    body: ProcedureChargeCreate,
    session: AsyncSession = Depends(get_db),
    current: User = Depends(require_permission("admin.manage_settings")),
) -> ProcedureChargeOut:
    return await service.create_procedure_charge(session, body, actor_id=current.id, actor_role=current.role.code)


@router.get("/packages", response_model=list[PackageOut])
async def list_packages(
    session: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("admin.manage_settings")),
) -> list[PackageOut]:
    return await service.list_packages(session)


@router.post("/packages", response_model=PackageOut, status_code=201)
async def create_package(
    body: PackageCreate,
    session: AsyncSession = Depends(get_db),
    current: User = Depends(require_permission("admin.manage_settings")),
) -> PackageOut:
    return await service.create_package(session, body, actor_id=current.id, actor_role=current.role.code)


@router.get("/lab-tests", response_model=list[LabTestOut])
async def list_lab_tests(
    session: AsyncSession = Depends(get_db),
    # Deliberately laboratory.read, not admin.manage_settings — the
    # Laboratory screen (doctor/embryologist) needs to see the test
    # catalogue for ordering, while only admin.manage_settings can edit it.
    _: User = Depends(require_permission("laboratory.read")),
) -> list[LabTestOut]:
    return await service.list_lab_tests(session)


@router.post("/lab-tests", status_code=201)
async def create_lab_test(
    body: LabTestCreate,
    session: AsyncSession = Depends(get_db),
    current: User = Depends(require_permission("admin.manage_settings")),
) -> dict:
    test = await service.create_lab_test(session, body, actor_id=current.id, actor_role=current.role.code)
    return {"id": str(test.id)}
