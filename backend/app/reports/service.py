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
from app.clinical.models import Consultation
from app.core.exceptions import NotFoundError
from app.cryostorage.models import CryoLocation, EmbryoTransfer
from app.embryology.models import Embryo, OocyteAssessment
from app.ivf.models import (
    InjectionAdministration,
    IVFCycle,
    MonitoringVisit,
    PregnancyOutcome,
    PregnancyRecord,
)
from app.laboratory.models import LabOrder
from app.patients.models import Couple, Patient
from app.prescription.models import Prescription


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


async def discharge_summary(session: AsyncSession, patient_id) -> dict:
    """New requirement (source doc §21) — consolidates a patient's record
    across every module for discharge, pulling exclusively from data that
    already exists elsewhere in the system (registration, consultations,
    investigations, cycle/treatment, prescriptions, injections, egg
    collection, embryology, storage, ET, monitoring observations,
    outcome). Nothing here is generated or inferred — every field is a
    direct read of an existing record, per the source doc's rule against
    inventing clinical content. Printing this (once a print template
    exists) should call printing.service.record_print_event, same as
    every other printable document."""
    patient = await session.get(Patient, patient_id)
    if not patient:
        raise NotFoundError("Patient not found")

    couple_result = await session.execute(
        select(Couple).where((Couple.female_patient_id == patient_id) | (Couple.male_patient_id == patient_id))
    )
    couple = couple_result.scalar_one_or_none()

    cycles: list[IVFCycle] = []
    if couple:
        cycle_result = await session.execute(select(IVFCycle).where(IVFCycle.couple_id == couple.id))
        cycles = list(cycle_result.scalars().all())
    cycle_ids = [c.id for c in cycles]

    consultations_result = await session.execute(
        select(Consultation).where(Consultation.patient_id == patient_id).order_by(Consultation.created_at)
    )
    investigations_result = await session.execute(
        select(LabOrder).where(LabOrder.patient_id == patient_id).order_by(LabOrder.created_at)
    )
    prescriptions_result = await session.execute(
        select(Prescription).where(Prescription.patient_id == patient_id).order_by(Prescription.created_at)
    )

    monitoring, injections, oocyte_assessments, embryos, transfers, storage, pregnancies = [], [], [], [], [], [], []
    if cycle_ids:
        monitoring = (await session.execute(
            select(MonitoringVisit).where(MonitoringVisit.cycle_id.in_(cycle_ids)).order_by(MonitoringVisit.visit_date)
        )).scalars().all()
        injections = (await session.execute(
            select(InjectionAdministration).where(InjectionAdministration.cycle_id.in_(cycle_ids)).order_by(InjectionAdministration.scheduled_at)
        )).scalars().all()
        oocyte_assessments = (await session.execute(
            select(OocyteAssessment).where(OocyteAssessment.cycle_id.in_(cycle_ids))
        )).scalars().all()
        embryos = (await session.execute(
            select(Embryo).where(Embryo.cycle_id.in_(cycle_ids)).order_by(Embryo.label)
        )).scalars().all()
        transfers = (await session.execute(
            select(EmbryoTransfer).where(EmbryoTransfer.cycle_id.in_(cycle_ids))
        )).scalars().all()
        embryo_ids = [e.id for e in embryos]
        if embryo_ids:
            storage = (await session.execute(
                select(CryoLocation).where(CryoLocation.embryo_id.in_(embryo_ids), CryoLocation.is_active.is_(True))
            )).scalars().all()
        pregnancies = (await session.execute(
            select(PregnancyRecord).where(PregnancyRecord.cycle_id.in_(cycle_ids))
        )).scalars().all()

    return {
        "patient": {"id": str(patient.id), "uhid": patient.uhid, "full_name": patient.full_name, "date_of_birth": patient.date_of_birth},
        "couple": {"id": str(couple.id), "partner_name": (couple.male_patient if couple.female_patient_id == patient.id else couple.female_patient).full_name} if couple else None,
        "cycles": [{"id": str(c.id), "cycle_number": c.cycle_number, "protocol": c.protocol, "treatment": c.treatment, "stage": c.stage.value, "started_at": c.started_at} for c in cycles],
        "consultations": [{"id": str(c.id), "type": c.consultation_type, "notes": c.notes, "date": c.created_at} for c in consultations_result.scalars().all()],
        "investigations": [{"id": str(o.id), "test_name": o.test_name, "status": o.status.value, "date": o.created_at} for o in investigations_result.scalars().all()],
        "prescriptions": [{"id": str(p.id), "category": p.category, "line_count": len(p.lines), "date": p.created_at} for p in prescriptions_result.scalars().all()],
        "monitoring_visits": [{"id": str(m.id), "cycle_day": m.cycle_day, "date": m.visit_date, "endometrium_mm": float(m.endometrium_mm), "doctor_note": m.doctor_note} for m in monitoring],
        "injections": [{"id": str(i.id), "medicine_name": i.medicine_name, "dose": i.dose, "status": i.status.value, "administered_at": i.administered_at} for i in injections],
        "oocyte_assessments": [{"id": str(o.id), "retrieval_date": o.retrieval_date, "oocytes_retrieved": o.oocytes_retrieved, "mature_oocytes": o.mature_oocytes, "normally_fertilised": o.normally_fertilised} for o in oocyte_assessments],
        "embryos": [{"id": str(e.id), "label": e.label, "day": e.day, "grade": e.grade, "status": e.status.value} for e in embryos],
        "embryo_transfers": [{"id": str(t.id), "transfer_date": t.transfer_date, "completed": t.completed} for t in transfers],
        "current_storage": [{"id": str(s.id), "address": f"{s.tank}/{s.canister}/{s.cane}/{s.goblet}/{s.straw}", "embryo_id": str(s.embryo_id)} for s in storage],
        "pregnancy_outcomes": [{"id": str(p.id), "outcome": p.outcome.value, "transfer_date": p.transfer_date, "estimated_due_date": p.estimated_due_date} for p in pregnancies],
    }
