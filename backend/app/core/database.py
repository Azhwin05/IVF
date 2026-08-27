"""
SQLAlchemy 2.x async engine + session management.

Two engines are deliberately kept separate:

  - `engine` / `AsyncSessionLocal` — the pooled engine used by the FastAPI
    process. It's created once at import time and lives for the process's
    lifetime, all requests running on uvicorn's single long-lived event
    loop, so pooled connections are always reused within the loop that
    created them.

  - `worker_session_scope()` — used by Celery task bodies instead. Celery
    workers invoke each task via a fresh `asyncio.run(...)` call (see
    app/workers/tasks.py's `_run` helper), which spins up a brand-new
    event loop per task. asyncpg connections are bound to the loop that
    created them, so reusing the pooled `engine` across those separate
    loops throws "attached to a different loop" — a real bug this
    project's own test/verification pass caught. `worker_session_scope`
    sidesteps it by creating a disposable, unpooled (NullPool) engine
    scoped to exactly one task invocation.
"""
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool

from app.core.config import get_settings

settings = get_settings()

engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_pre_ping=True,
    echo=False,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    """Shared declarative base for every module's models."""
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency — one session per request, committed or rolled back automatically."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


@asynccontextmanager
async def worker_session_scope() -> AsyncGenerator[AsyncSession, None]:
    """For Celery task bodies only — see module docstring. Creates and
    disposes a standalone engine per call so nothing outlives the task's
    own asyncio.run() event loop."""
    worker_engine = create_async_engine(settings.DATABASE_URL, poolclass=NullPool, echo=False)
    session_factory = async_sessionmaker(bind=worker_engine, class_=AsyncSession, expire_on_commit=False)
    try:
        async with session_factory() as session:
            yield session
    finally:
        await worker_engine.dispose()
