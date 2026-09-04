"""End-to-end concurrent report generation through a REAL broker + worker.

Skipped unless RUN_REPORTS_CONCURRENCY=1, because it needs a live stack: a
Celery worker consuming Redis, plus PostgreSQL. The in-process concurrency proof
that DOES run in CI (no broker required) lives in
``test_report_jobs.py::TestConcurrency``.

This test publishes real tasks and lets the running worker execute them, so the
worker and this test must share one database. ``conftest.py`` forces
``DATABASE_URL`` to the throwaway ``*_test`` database, which the worker is NOT
connected to - so point the test at the worker's database explicitly:

  RUN_REPORTS_CONCURRENCY=1 \
  RUN_REPORTS_CONCURRENCY_DB=postgresql+asyncpg://archana:...@postgres:5432/archana_hmis \
  pytest tests/test_report_jobs_concurrency.py -s

with a worker already running against the same broker/db, e.g. (inside the stack):

  docker compose ... exec worker celery -A app.workers.celery_app \
      worker --concurrency=10 --loglevel=info

The worker's broker/result-backend come from CELERY_BROKER_URL /
CELERY_RESULT_BACKEND (never REDIS_URL) - the same settings the API process
reads, so both sides talk to the same Redis.
"""

import asyncio
import os
import time

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

pytestmark = pytest.mark.skipif(
    os.environ.get("RUN_REPORTS_CONCURRENCY") != "1",
    reason="needs a live Celery worker + Redis + Postgres; set RUN_REPORTS_CONCURRENCY=1",
)

N = 10


def _target_db_url() -> str:
    explicit = os.environ.get("RUN_REPORTS_CONCURRENCY_DB")
    if explicit:
        return explicit
    # Fall back to conftest's DATABASE_URL with a trailing "_test" stripped, so
    # the rows this test writes land in the database the worker actually reads.
    from app.core.config import get_settings

    url = get_settings().DATABASE_URL
    head, _, tail = url.rpartition("/")
    db = tail.split("?")[0]
    return f"{head}/{db[:-5]}" if db.endswith("_test") else url


async def _run() -> None:
    from app.core.security import hash_password
    from app.patients.models import Patient
    from app.reports.job_models import ReportJob, ReportStatus
    from app.reports.job_tasks import generate_report_task
    from app.roles.models import Role
    from app.roles.seed import seed_roles_and_permissions
    from app.users.models import User

    engine = create_async_engine(_target_db_url(), future=True)
    Session = async_sessionmaker(engine, expire_on_commit=False)
    marker = f"CONC-{int(time.time())}"
    user_id = patient_id = None
    job_ids: list = []

    try:
        async with Session() as s:
            role_id = (
                await s.execute(select(Role.id).where(Role.code == "administrator"))
            ).scalar_one_or_none()
            if role_id is None:
                await seed_roles_and_permissions(s)
                await s.commit()
                role_id = (
                    await s.execute(select(Role.id).where(Role.code == "administrator"))
                ).scalar_one()

            user = User(
                employee_code=marker, full_name="Concurrency Test",
                email=f"{marker.lower()}@example.com", role_id=role_id,
                password_hash=hash_password("TestPass123!"),
            )
            patient = Patient(uhid=marker, full_name="Conc Patient", gender="female")
            s.add_all([user, patient])
            await s.flush()
            user_id, patient_id = user.id, patient.id

            jobs = [
                ReportJob(
                    report_type="patient_summary",
                    parameters={"patient_id": str(patient_id)},
                    options={"simulate_work_seconds": 3},
                    status=ReportStatus.queued,
                    requested_by_id=user_id,
                    queued_at=__import__("datetime").datetime.now(__import__("datetime").timezone.utc),
                )
                for _ in range(N)
            ]
            s.add_all(jobs)
            await s.commit()
            job_ids = [j.id for j in jobs]

        started = time.monotonic()
        for jid in job_ids:
            generate_report_task.apply_async(args=[str(jid)])

        deadline = started + 180
        rows = []
        while time.monotonic() < deadline:
            async with Session() as s:
                rows = (
                    await s.execute(select(ReportJob).where(ReportJob.id.in_(job_ids)))
                ).scalars().all()
            if rows and all(
                r.status in (ReportStatus.succeeded, ReportStatus.failed) for r in rows
            ):
                break
            await asyncio.sleep(1)
        wall = time.monotonic() - started

        succeeded = [r for r in rows if r.status is ReportStatus.succeeded]
        windows = sorted((r.started_at, r.finished_at) for r in succeeded)
        max_overlap = max(
            (sum(1 for s0, f0 in windows if s0 <= start < f0) for start, _ in windows),
            default=0,
        )

        assert len(succeeded) == N, f"{len(succeeded)}/{N} succeeded; statuses={[r.status.value for r in rows]}"
        # Serial lower bound is N * simulate_seconds (each job sleeps 3s). A
        # prefork worker with concurrency C finishes in ~ceil(N/C)*3 + overhead;
        # staying well under the serial bound is the wall-time signal, and the
        # overlapping [started_at, finished_at] windows are the direct proof.
        serial_lower_bound = 3 * N
        assert wall < serial_lower_bound * 0.85, (
            f"wall {wall:.1f}s is not clearly below the {serial_lower_bound}s serial bound"
        )
        assert max_overlap >= 2, "worker [started_at, finished_at] windows never overlapped"
    finally:
        async with Session() as s:
            from sqlalchemy import delete

            if job_ids:
                await s.execute(delete(ReportJob).where(ReportJob.id.in_(job_ids)))
            if patient_id is not None:
                await s.execute(delete(Patient).where(Patient.id == patient_id))
            if user_id is not None:
                await s.execute(delete(User).where(User.id == user_id))
            await s.commit()
        await engine.dispose()


def test_ten_concurrent_report_generations() -> None:
    asyncio.run(_run())
