"""
Real aggregation queries backing the Reports & Analytics screen —
replaces the frontend's static REVENUE_TREND / MANAGEMENT_KPIS /
OUTCOME_BREAKDOWN / DOCTOR_PERFORMANCE fixtures with actual SQL over
the transactional tables, per ARCHITECTURE.md Phase 7. Each function
returns a small, purpose-specific shape — never a raw dump of an
entire table (spec §9).
"""
from datetime import date

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.appointments.models import Appointment
from app.billing.models import Invoice, Payment
from app.ivf.models import IVFCycle, PregnancyOutcome, PregnancyRecord
from app.patients.models import Patient


async def clinical_dashboard_metrics(session: AsyncSession, *, day: date) -> dict:
    appt_count = await session.scalar(
        select(func.count()).select_from(Appointment).where(func.date(Appointment.scheduled_at) == day)
    )
    waiting_count = await session.scalar(
        select(func.count()).select_from(Appointment).where(Appointment.status == "waiting")
    )
    active_cycles = await session.scalar(
        select(func.count()).select_from(IVFCycle).where(IVFCycle.stage != "completed")
    )
    collection_paise = await session.scalar(
        select(func.coalesce(func.sum(Payment.amount_paise), 0))
        .where(func.date(Payment.created_at) == day, Payment.is_refund.is_(False))
    )
    return {
        "appointments_today": appt_count or 0,
        "patients_waiting": waiting_count or 0,
        "active_ivf_cycles": active_cycles or 0,
        "todays_collection_paise": int(collection_paise or 0),
    }


async def cycle_distribution(session: AsyncSession) -> list[dict]:
    result = await session.execute(
        select(IVFCycle.stage, func.count()).where(IVFCycle.stage != "completed").group_by(IVFCycle.stage)
    )
    return [{"stage": stage.value, "count": count} for stage, count in result.all()]


async def outcome_breakdown(session: AsyncSession, *, from_date: date, to_date: date) -> list[dict]:
    result = await session.execute(
        select(PregnancyRecord.outcome, func.count())
        .where(PregnancyRecord.created_at.between(from_date, to_date))
        .group_by(PregnancyRecord.outcome)
    )
    return [{"outcome": outcome.value, "count": count} for outcome, count in result.all()]


async def new_patients_this_month(session: AsyncSession, *, year: int, month: int) -> int:
    result = await session.scalar(
        select(func.count()).select_from(Patient).where(
            func.extract("year", Patient.created_at) == year,
            func.extract("month", Patient.created_at) == month,
        )
    )
    return result or 0


async def revenue_trend(session: AsyncSession, *, months: int = 6) -> list[dict]:
    result = await session.execute(
        select(
            func.date_trunc("month", Payment.created_at).label("month"),
            func.sum(Payment.amount_paise),
        )
        .where(Payment.is_refund.is_(False))
        .group_by("month")
        .order_by("month")
        .limit(months)
    )
    return [{"month": month.strftime("%b"), "revenue_paise": int(total)} for month, total in result.all()]


async def doctor_performance(session: AsyncSession) -> list[dict]:
    result = await session.execute(
        select(Appointment.doctor_id, func.count())
        .where(Appointment.status == "completed")
        .group_by(Appointment.doctor_id)
    )
    return [{"doctor_id": str(doctor_id), "consultations": count} for doctor_id, count in result.all()]
