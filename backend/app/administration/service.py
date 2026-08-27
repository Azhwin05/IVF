"""
System Administration — master-data management, spec §4: 'An
administration panel to manage users, roles, doctors, medicines, lab
tests, procedure charges, packages, and all master settings — without
needing ClickFieldAI for routine changes.'

User/role management already lives in app/users and app/roles (which
this screen also surfaces via those routers). This module owns the
remaining master-data tables: procedure charges, packages, lab test
catalogue.
"""
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.administration.schemas import LabTestCreate, PackageCreate, ProcedureChargeCreate
from app.audit.service import record_audit_event
from app.billing.models import Package, ProcedureCharge
from app.laboratory.models import LabTestCatalogueItem


async def list_procedure_charges(session: AsyncSession) -> list[ProcedureCharge]:
    result = await session.execute(select(ProcedureCharge).where(ProcedureCharge.is_active.is_(True)).order_by(ProcedureCharge.procedure_name))
    return list(result.scalars().all())


async def create_procedure_charge(
    session: AsyncSession, data: ProcedureChargeCreate, *, actor_id: uuid.UUID, actor_role: str
) -> ProcedureCharge:
    charge = ProcedureCharge(**data.model_dump())
    session.add(charge)
    await session.flush()

    await record_audit_event(
        session, actor_id=actor_id, actor_role=actor_role,
        action="admin.procedure_charge_created", entity_type="ProcedureCharge", entity_id=str(charge.id),
        after_state=data.model_dump(),
    )
    return charge


async def update_procedure_charge_amount(
    session: AsyncSession, charge_id: uuid.UUID, new_amount_paise: int, *, actor_id: uuid.UUID, actor_role: str
) -> ProcedureCharge:
    charge = await session.get(ProcedureCharge, charge_id)
    before = charge.charge_paise
    charge.charge_paise = new_amount_paise
    await session.flush()

    await record_audit_event(
        session, actor_id=actor_id, actor_role=actor_role,
        action="admin.procedure_charge_updated", entity_type="ProcedureCharge", entity_id=str(charge.id),
        before_state={"charge_paise": before}, after_state={"charge_paise": new_amount_paise},
    )
    return charge


async def list_packages(session: AsyncSession) -> list[Package]:
    result = await session.execute(select(Package).where(Package.is_active.is_(True)).order_by(Package.name))
    return list(result.scalars().all())


async def create_package(session: AsyncSession, data: PackageCreate, *, actor_id: uuid.UUID, actor_role: str) -> Package:
    package = Package(**data.model_dump())
    session.add(package)
    await session.flush()

    await record_audit_event(
        session, actor_id=actor_id, actor_role=actor_role,
        action="admin.package_created", entity_type="Package", entity_id=str(package.id),
    )
    return package


async def list_lab_tests(session: AsyncSession) -> list[LabTestCatalogueItem]:
    result = await session.execute(select(LabTestCatalogueItem).where(LabTestCatalogueItem.is_active.is_(True)))
    return list(result.scalars().all())


async def create_lab_test(session: AsyncSession, data: LabTestCreate, *, actor_id: uuid.UUID, actor_role: str) -> LabTestCatalogueItem:
    test = LabTestCatalogueItem(**data.model_dump())
    session.add(test)
    await session.flush()

    await record_audit_event(
        session, actor_id=actor_id, actor_role=actor_role,
        action="admin.lab_test_created", entity_type="LabTestCatalogueItem", entity_id=str(test.id),
    )
    return test
