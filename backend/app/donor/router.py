from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import require_permission
from app.donor import service
from app.donor.models import DonorCategory
from app.donor.schemas import (
    DonorBenchmarkCreate,
    DonorBenchmarkOut,
    DonorCreate,
    DonorMatchCreate,
    DonorMatchEnd,
    DonorMatchOut,
    DonorOut,
)
from app.users.models import User

router = APIRouter(prefix="/donors", tags=["donors"])


@router.get("", response_model=list[DonorOut])
async def list_donors(
    category: DonorCategory | None = None,
    session: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("donor.read")),
) -> list[DonorOut]:
    return await service.list_donors(session, category=category)


@router.post("", response_model=DonorOut, status_code=201)
async def create_donor(
    body: DonorCreate,
    session: AsyncSession = Depends(get_db),
    current: User = Depends(require_permission("donor.write")),
) -> DonorOut:
    return await service.create_donor(session, body, actor_id=current.id, actor_role=current.role.code)


@router.get("/{donor_id}", response_model=DonorOut)
async def get_donor(
    donor_id: str,
    session: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("donor.read")),
) -> DonorOut:
    return await service.get_donor(session, donor_id)


@router.post("/matches", response_model=DonorMatchOut, status_code=201)
async def create_match(
    body: DonorMatchCreate,
    session: AsyncSession = Depends(get_db),
    current: User = Depends(require_permission("donor.match")),
) -> DonorMatchOut:
    """Critical rule — source doc §22: prohibited duplicate donor matching
    is prevented by a real database constraint, not just this endpoint.
    Raises 409 donor_already_matched if the donor already has an active match."""
    return await service.create_match(session, body, actor_id=current.id, actor_role=current.role.code)


@router.post("/matches/{match_id}/end", response_model=DonorMatchOut)
async def end_match(
    match_id: str,
    body: DonorMatchEnd,
    session: AsyncSession = Depends(get_db),
    current: User = Depends(require_permission("donor.match")),
) -> DonorMatchOut:
    return await service.end_match(session, match_id, body.reason, actor_id=current.id, actor_role=current.role.code)


@router.get("/{donor_id}/matches", response_model=list[DonorMatchOut])
async def list_matches(
    donor_id: str,
    session: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("donor.read")),
) -> list[DonorMatchOut]:
    return await service.list_matches_for_donor(session, donor_id)


@router.post("/benchmarks", response_model=DonorBenchmarkOut, status_code=201)
async def record_benchmark(
    body: DonorBenchmarkCreate,
    session: AsyncSession = Depends(get_db),
    current: User = Depends(require_permission("donor.write")),
) -> DonorBenchmarkOut:
    return await service.record_benchmark(session, body, actor_id=current.id, actor_role=current.role.code)


@router.get("/{donor_id}/benchmarks", response_model=list[DonorBenchmarkOut])
async def list_benchmarks(
    donor_id: str,
    session: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("donor.read")),
) -> list[DonorBenchmarkOut]:
    return await service.list_benchmarks_for_donor(session, donor_id)
