from datetime import date
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import require_permission
from app.core.exceptions import NotFoundError
from app.reports import job_service, service
from app.reports.job_models import ReportStatus, ReportType
from app.reports.job_schemas import ReportJobPage, ReportJobRead, ReportRequest
from app.reports.job_storage import ReportArtifactStorage, get_report_storage
from app.reports.job_tasks import generate_report_task
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


# ===========================================================================
# Asynchronous report-generation jobs (Celery). Distinct from the live
# analytics endpoints above: a job is queued, a worker generates an artifact
# in the background, and the client polls for status then downloads.
#
#   reports.generate — submit a job
#   reports.read     — view job status and download a finished artifact
# ===========================================================================


@router.post("/jobs", response_model=ReportJobRead, status_code=202)
async def submit_report_job(
    payload: ReportRequest,
    session: AsyncSession = Depends(get_db),
    current: User = Depends(require_permission("reports.generate")),
) -> ReportJobRead:
    """Validate, persist a queued job, hand it to the worker, and return
    immediately. Poll ``GET /reports/jobs/{id}`` for progress."""
    task_id = str(uuid4())
    job = await job_service.create_report_job(
        session,
        payload,
        requested_by_id=current.id,
        celery_task_id=task_id,
        commit=True,
    )
    # Enqueue only after the row is durably committed, so the worker can never
    # look for a job that is not there yet.
    generate_report_task.apply_async(args=[str(job.id)], task_id=task_id)
    return ReportJobRead.model_validate(job)


@router.get("/jobs", response_model=ReportJobPage)
async def list_report_jobs(
    session: AsyncSession = Depends(get_db),
    limit: int = Query(default=25, ge=1, le=100),
    cursor: str | None = Query(default=None),
    job_status: ReportStatus | None = Query(default=None, alias="status"),
    report_type: ReportType | None = Query(default=None),
    _: User = Depends(require_permission("reports.read")),
) -> ReportJobPage:
    jobs, next_cursor, has_more = await job_service.list_report_jobs(
        session, limit=limit, cursor=cursor, status=job_status, report_type=report_type
    )
    return ReportJobPage(
        items=[ReportJobRead.model_validate(j) for j in jobs],
        next_cursor=next_cursor,
        has_more=has_more,
    )


@router.get("/jobs/{job_id}", response_model=ReportJobRead)
async def get_report_job(
    job_id: UUID,
    session: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("reports.read")),
) -> ReportJobRead:
    job = await job_service.get_report_job(session, job_id)
    if job is None:
        raise NotFoundError("Report job not found.")
    return ReportJobRead.model_validate(job)


@router.get("/jobs/{job_id}/result")
async def download_report_job_result(
    job_id: UUID,
    session: AsyncSession = Depends(get_db),
    storage: ReportArtifactStorage = Depends(get_report_storage),
    _: User = Depends(require_permission("reports.read")),
) -> StreamingResponse:
    found = await job_service.get_report_artifact(session, storage, job_id)
    if found is None:
        raise NotFoundError("Report job not found.")
    job, data = found

    def _iter():
        yield data

    suffix = {"application/json": ".json", "text/csv": ".csv", "application/pdf": ".pdf"}.get(
        job.content_type or "", ""
    )
    filename = f"{job.report_type.value.replace('_', '-')}-{job.id}{suffix}"
    return StreamingResponse(
        _iter(),
        media_type=job.content_type or "application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
