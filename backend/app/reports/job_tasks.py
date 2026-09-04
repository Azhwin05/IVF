"""Celery task for asynchronous report generation.

Registered on the project's existing Celery app (``app.workers.celery_app``) -
this module adds no new broker/result-backend configuration. The one task is a
thin sync wrapper that drives the async
:func:`app.reports.job_service.run_report_job`; all state lives on the
``report_jobs`` row, so the task takes only the job id and is safe to retry.
"""

from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Any
from uuid import UUID

from app.workers.celery_app import celery_app

# Test seam: the unit-test suite (eager mode, test database) sets these to an
# async_sessionmaker bound to the test engine + an in-memory artifact store so
# the task writes where the test reads. The real worker leaves them None and the
# service builds its own engine from settings.
session_factory_override: Any | None = None
storage_override: Any | None = None


def _run_coro(coro) -> Any:
    """Run ``coro`` to completion from a sync context.

    A real Celery worker has no running event loop, so ``asyncio.run`` is fine.
    Under pytest (eager mode) there *is* a running loop and ``asyncio.run`` would
    raise - so the coroutine is run in a dedicated thread with its own loop.
    """
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)
    with ThreadPoolExecutor(max_workers=1) as pool:
        return pool.submit(asyncio.run, coro).result()


@celery_app.task(
    name="reports.generate_report_job",
    bind=True,
    max_retries=1,
    default_retry_delay=2,
)
def generate_report_task(self, report_job_id: str) -> str:  # noqa: ANN001
    from app.reports.job_service import run_report_job

    status = _run_coro(
        run_report_job(
            UUID(report_job_id),
            session_factory=session_factory_override,
            storage=storage_override,
        )
    )
    return status.value
