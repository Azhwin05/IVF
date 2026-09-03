import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.service import record_audit_event
from app.core.exceptions import ConflictError, NotFoundError
from app.donor.models import Donor, DonorBenchmark, DonorMatch
from app.donor.schemas import DonorBenchmarkCreate, DonorCreate, DonorMatchCreate


async def _next_donor_code(session: AsyncSession) -> str:
    year = datetime.now(timezone.utc).year
    prefix = f"DNR-{year}-"
    result = await session.execute(
        select(Donor.donor_code).where(Donor.donor_code.like(f"{prefix}%"))
        .order_by(Donor.donor_code.desc()).limit(1).with_for_update()
    )
    last = result.scalar_one_or_none()
    next_seq = int(last.split("-")[-1]) + 1 if last else 1
    return f"{prefix}{next_seq:05d}"


async def create_donor(session: AsyncSession, data: DonorCreate, *, actor_id: uuid.UUID, actor_role: str) -> Donor:
    donor = Donor(donor_code=await _next_donor_code(session), **data.model_dump())
    session.add(donor)
    await session.flush()

    await record_audit_event(
        session, actor_id=actor_id, actor_role=actor_role,
        action="donor.registered", entity_type="Donor", entity_id=str(donor.id),
        after_state={"donor_code": donor.donor_code, "category": data.category.value},
    )
    return donor


async def list_donors(session: AsyncSession, *, category=None) -> list[Donor]:
    stmt = select(Donor).order_by(Donor.created_at.desc())
    if category:
        stmt = stmt.where(Donor.category == category)
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_donor(session: AsyncSession, donor_id: uuid.UUID) -> Donor:
    donor = await session.get(Donor, donor_id)
    if not donor:
        raise NotFoundError("Donor not found")
    return donor


async def create_match(
    session: AsyncSession, data: DonorMatchCreate, *, actor_id: uuid.UUID, actor_role: str
) -> DonorMatch:
    """Critical rule (source doc §22, non-negotiable): once a donor is
    actively matched, a second active match is prohibited — enforced by
    the DB's partial unique index (uq_donor_one_active_match), not just
    this check. This pre-check exists purely to turn the raw
    IntegrityError into a clear message; the actual guarantee is the
    database constraint, so a race between two concurrent requests still
    cannot both succeed."""
    await get_donor(session, data.donor_id)  # 404s if missing

    match = DonorMatch(
        matched_by_id=actor_id, matched_at=datetime.now(timezone.utc), **data.model_dump()
    )
    session.add(match)
    try:
        await session.flush()
    except IntegrityError as exc:
        await session.rollback()
        if "uq_donor_one_active_match" in str(exc.orig):
            raise ConflictError(
                "This donor is already actively matched to another patient. "
                "End the existing match before creating a new one.",
                error_code="donor_already_matched",
            ) from exc
        raise

    await record_audit_event(
        session, actor_id=actor_id, actor_role=actor_role,
        action="donor.matched", entity_type="DonorMatch", entity_id=str(match.id),
        after_state={"donor_id": str(data.donor_id), "patient_id": str(data.patient_id)},
    )
    return match


async def end_match(
    session: AsyncSession, match_id: uuid.UUID, reason: str, *, actor_id: uuid.UUID, actor_role: str
) -> DonorMatch:
    match = await session.get(DonorMatch, match_id)
    if not match:
        raise NotFoundError("Donor match not found")
    if not match.is_active:
        raise ConflictError("This match has already ended.")

    match.is_active = False
    match.ended_at = datetime.now(timezone.utc)
    match.ended_reason = reason
    await session.flush()

    await record_audit_event(
        session, actor_id=actor_id, actor_role=actor_role,
        action="donor.match_ended", entity_type="DonorMatch", entity_id=str(match.id), reason=reason,
    )
    return match


async def list_matches_for_donor(session: AsyncSession, donor_id: uuid.UUID) -> list[DonorMatch]:
    result = await session.execute(
        select(DonorMatch).where(DonorMatch.donor_id == donor_id).order_by(DonorMatch.matched_at.desc())
    )
    return list(result.scalars().all())


async def record_benchmark(
    session: AsyncSession, data: DonorBenchmarkCreate, *, actor_id: uuid.UUID, actor_role: str
) -> DonorBenchmark:
    await get_donor(session, data.donor_id)
    deviation = 0.0
    if data.expected_value != 0:
        deviation = abs((data.actual_value - data.expected_value) / data.expected_value) * 100

    benchmark = DonorBenchmark(
        recorded_by_id=actor_id,
        is_underperforming=deviation > data.threshold_percent,
        **data.model_dump(),
    )
    session.add(benchmark)
    await session.flush()

    await record_audit_event(
        session, actor_id=actor_id, actor_role=actor_role,
        action="donor.benchmark_recorded", entity_type="DonorBenchmark", entity_id=str(benchmark.id),
        after_state={"metric_name": data.metric_name, "deviation_percent": round(deviation, 2), "is_underperforming": benchmark.is_underperforming},
    )
    return benchmark


async def list_benchmarks_for_donor(session: AsyncSession, donor_id: uuid.UUID) -> list[DonorBenchmark]:
    result = await session.execute(
        select(DonorBenchmark).where(DonorBenchmark.donor_id == donor_id).order_by(DonorBenchmark.created_at.desc())
    )
    return list(result.scalars().all())
