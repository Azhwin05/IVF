from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import require_permission
from app.reports import service
from app.users.models import User

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/dashboard")
async def dashboard(
    day: date = Query(default_factory=date.today),
    session: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("reports.read")),
) -> dict:
    return await service.clinical_dashboard_metrics(session, day=day)


@router.get("/cycle-distribution")
async def cycles(
    session: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("reports.read")),
) -> list[dict]:
    return await service.cycle_distribution(session)


@router.get("/outcomes")
async def outcomes(
    from_date: date = Query(...),
    to_date: date = Query(...),
    session: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("reports.read")),
) -> list[dict]:
    return await service.outcome_breakdown(session, from_date=from_date, to_date=to_date)


@router.get("/revenue-trend")
async def revenue(
    months: int = 6,
    session: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("reports.read")),
) -> list[dict]:
    return await service.revenue_trend(session, months=months)


@router.get("/doctor-performance")
async def performance(
    session: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("reports.read")),
) -> list[dict]:
    return await service.doctor_performance(session)


@router.get("/discharge-summary/{patient_id}")
async def discharge_summary(
    patient_id: str,
    session: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("clinical.read")),
) -> dict:
    """New requirement (source doc §21) — gated on clinical.read (not
    reports.read) since this is patient clinical data, not an operational
    report; doctors and nurses need it, not just management/accounting."""
    return await service.discharge_summary(session, patient_id)
