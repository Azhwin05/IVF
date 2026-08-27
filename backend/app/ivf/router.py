from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import require_permission
from app.ivf import service
from app.ivf.schemas import (
    BetaHcgCreate,
    BetaHcgOut,
    CycleCreate,
    CycleOut,
    CycleStageUpdate,
    MilestoneCreate,
    MilestoneOut,
    MonitoringReview,
    MonitoringVisitCreate,
    MonitoringVisitOut,
    PregnancyOut,
)
from app.users.models import User

router = APIRouter(prefix="/ivf", tags=["ivf"])


@router.post("/cycles", response_model=CycleOut, status_code=201)
async def create_cycle(
    body: CycleCreate,
    session: AsyncSession = Depends(get_db),
    current: User = Depends(require_permission("ivf.write")),
) -> CycleOut:
    return await service.create_cycle(session, body, actor_id=current.id, actor_role=current.role.code)


@router.get("/cycles/{cycle_id}", response_model=CycleOut)
async def get_cycle(
    cycle_id: str,
    session: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("ivf.read")),
) -> CycleOut:
    return await service.get_cycle(session, cycle_id)


@router.get("/cycles/by-couple/{couple_id}/active", response_model=CycleOut | None)
async def get_active_cycle(
    couple_id: str,
    session: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("ivf.read")),
) -> CycleOut | None:
    return await service.get_active_cycle_for_couple(session, couple_id)


@router.post("/cycles/{cycle_id}/stage", response_model=CycleOut)
async def advance_stage(
    cycle_id: str,
    body: CycleStageUpdate,
    session: AsyncSession = Depends(get_db),
    current: User = Depends(require_permission("ivf.write")),
) -> CycleOut:
    return await service.advance_stage(session, cycle_id, body.stage, actor_id=current.id, actor_role=current.role.code)


@router.post("/monitoring", response_model=MonitoringVisitOut, status_code=201)
async def record_monitoring(
    body: MonitoringVisitCreate,
    session: AsyncSession = Depends(get_db),
    current: User = Depends(require_permission("ivf.monitoring.write")),
) -> MonitoringVisitOut:
    return await service.record_monitoring_visit(session, body, actor_id=current.id, actor_role=current.role.code)


@router.post("/monitoring/{visit_id}/review", response_model=MonitoringVisitOut)
async def review_monitoring(
    visit_id: str,
    body: MonitoringReview,
    session: AsyncSession = Depends(get_db),
    current: User = Depends(require_permission("ivf.monitoring.write")),
) -> MonitoringVisitOut:
    return await service.review_monitoring_visit(session, visit_id, body.doctor_note, actor_id=current.id, actor_role=current.role.code)


@router.get("/pregnancy/by-cycle/{cycle_id}", response_model=PregnancyOut)
async def get_pregnancy(
    cycle_id: str,
    session: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("ivf.read")),
) -> PregnancyOut:
    return await service.get_or_create_pregnancy(session, cycle_id)


@router.post("/pregnancy/beta-hcg", response_model=BetaHcgOut, status_code=201)
async def record_beta_hcg(
    body: BetaHcgCreate,
    session: AsyncSession = Depends(get_db),
    current: User = Depends(require_permission("ivf.write")),
) -> BetaHcgOut:
    return await service.record_beta_hcg(session, body, actor_id=current.id, actor_role=current.role.code)


@router.post("/pregnancy/milestones", response_model=MilestoneOut, status_code=201)
async def record_milestone(
    body: MilestoneCreate,
    session: AsyncSession = Depends(get_db),
    current: User = Depends(require_permission("ivf.write")),
) -> MilestoneOut:
    return await service.record_pregnancy_milestone(session, body, actor_id=current.id, actor_role=current.role.code)
