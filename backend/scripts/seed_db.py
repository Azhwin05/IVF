"""
Seeds roles, permissions, demo staff accounts, and (optionally) the
demo patient/couple/cycle data matching the existing frontend's mock
data — so a fresh environment is immediately demoable end-to-end with
the same Priya Raman / Arjun Kumar story the prototype already tells.

Run: python -m scripts.seed_db [--with-demo-data]
"""
import asyncio
import sys
from datetime import date, datetime, timezone

from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.core.security import hash_password
from app.roles.models import Role
from app.roles.seed import seed_roles_and_permissions
from app.users.models import User

DEMO_STAFF = [
    ("doctor", "DAIVF-STAFF-001", "Dr. Archana S. Ayyanathan", "archana@drarchanaivf.in", "Reproductive Medicine"),
    ("receptionist", "DAIVF-STAFF-014", "Lakshmi Narayanan", "lakshmi@drarchanaivf.in", "Patient Services"),
    ("embryologist", "DAIVF-STAFF-007", "Dr. Meera Kapoor", "meera@drarchanaivf.in", "Embryology Laboratory"),
    ("management", "DAIVF-STAFF-002", "Rajesh Venkatesan", "rajesh@drarchanaivf.in", "Operations & Finance"),
    ("administrator", "DAIVF-STAFF-000", "System Administrator", "admin@drarchanaivf.in", "IT"),
]

DEMO_PASSWORD = "ChangeMe123!"  # every seeded account must change this on first login (must_change_password=True)


async def seed_staff(session) -> dict[str, User]:
    roles = {r.code: r for r in (await session.execute(select(Role))).scalars().all()}
    created = {}
    for role_code, employee_code, full_name, email, department in DEMO_STAFF:
        existing = (await session.execute(select(User).where(User.email == email))).scalar_one_or_none()
        if existing:
            created[role_code] = existing
            continue
        user = User(
            employee_code=employee_code, full_name=full_name, email=email, department=department,
            role_id=roles[role_code].id, password_hash=hash_password(DEMO_PASSWORD), must_change_password=True,
        )
        session.add(user)
        await session.flush()
        created[role_code] = user
    return created


async def seed_demo_clinical_data(session, staff: dict[str, User]) -> None:
    """Recreates the frontend's Priya Raman / Arjun Kumar demo story as
    real database rows, so the reconnected UI shows a believable, complete
    journey on day one — not an empty database."""
    from app.cryostorage.models import CryoCustodyEvent, CryoLocation
    from app.embryology.models import Embryo, EmbryoStatus, OocyteAssessment
    from app.ivf.models import (
        BetaHcgResult,
        CycleStage,
        IVFCycle,
        MonitoringVisit,
        PregnancyMilestone,
        PregnancyOutcome,
        PregnancyRecord,
    )
    from app.patients.models import Couple, Patient

    existing = (await session.execute(select(Patient).where(Patient.uhid == "DAIVF-2026-00428"))).scalar_one_or_none()
    if existing:
        print("Demo clinical data already present — skipping.")
        return

    priya = Patient(
        uhid="DAIVF-2026-00428", full_name="Priya Raman", date_of_birth=date(1994, 9, 18),
        gender="female", blood_group="B Positive", phone="+91 98407 21894",
        email="priya.raman@gmail.com", address="T-4, Anandam Apartments, Alwarpet, Chennai 600018",
        occupation="Architect", allergies="No known drug allergies",
        primary_doctor_id=staff["doctor"].id,
    )
    arjun = Patient(
        uhid="DAIVF-2026-00429", full_name="Arjun Kumar", date_of_birth=date(1992, 5, 22),
        gender="male", blood_group="O Positive", phone="+91 98410 33127",
        email="arjun.kumar@gmail.com", occupation="Senior Software Engineer",
    )
    session.add_all([priya, arjun])
    await session.flush()

    couple = Couple(
        female_patient_id=priya.id, male_patient_id=arjun.id, relationship_info="Married — 6 Years",
        infertility_type="Primary Infertility", infertility_duration="6 Years",
        previous_iui_cycles=2, previous_ivf_cycles=0,
        previous_treatment_notes="Two failed IUI cycles at another centre (2024, 2025). No surgical history.",
    )
    session.add(couple)
    await session.flush()

    cycle = IVFCycle(
        cycle_number="IVF-2026-00428", couple_id=couple.id, primary_doctor_id=staff["doctor"].id,
        protocol="GnRH Antagonist Protocol", treatment="IVF with ICSI",
        stage=CycleStage.STIMULATION, started_at=date(2026, 7, 22),
    )
    session.add(cycle)
    await session.flush()

    session.add_all([
        MonitoringVisit(
            cycle_id=cycle.id, cycle_day=2, visit_date=date(2026, 7, 23),
            right_follicles_mm=[6, 5, 5, 4], left_follicles_mm=[6, 5, 4, 4],
            endometrium_mm=4.1, estradiol_pg_ml=186, lh_miu_ml=3.1, progesterone_ng_ml=0.3,
            doctor_note="Baseline scan satisfactory. No residual cysts. Commence Gonal-F 225 IU.",
            reviewed_by_id=staff["doctor"].id,
        ),
        MonitoringVisit(
            cycle_id=cycle.id, cycle_day=8, visit_date=date(2026, 7, 29),
            right_follicles_mm=[17, 15, 14, 12], left_follicles_mm=[16, 15, 13, 11],
            endometrium_mm=8.2, estradiol_pg_ml=1420, lh_miu_ml=4.8, progesterone_ng_ml=0.7,
            doctor_note="Follicular response is progressing appropriately.",
        ),
    ])
    session.add(OocyteAssessment(
        cycle_id=cycle.id, retrieval_date=date(2026, 8, 2),
        oocytes_retrieved=14, mature_oocytes=11, normally_fertilised=8, fertilisation_method="ICSI",
    ))

    embryos = [
        Embryo(cycle_id=cycle.id, label="E-01", day=5, grade="4AA", expansion="Expanded blastocyst",
               icm_grade="A — tightly packed, many cells", trophectoderm_grade="A — cohesive epithelium",
               quality_score=96, status=EmbryoStatus.SELECTED_FOR_TRANSFER, graded_by_id=staff["embryologist"].id,
               embryologist_notes="Top quality blastocyst. Even expansion, no fragmentation. Recommended for fresh transfer."),
        Embryo(cycle_id=cycle.id, label="E-02", day=5, grade="4AB", expansion="Expanded blastocyst",
               icm_grade="A — prominent inner cell mass", trophectoderm_grade="B — few larger cells",
               quality_score=88, status=EmbryoStatus.UNDER_REVIEW, graded_by_id=staff["embryologist"].id,
               embryologist_notes="Excellent morphology. Selected for vitrification for future frozen transfer."),
        Embryo(cycle_id=cycle.id, label="E-03", day=6, grade="3BB", expansion="Full blastocyst",
               icm_grade="B — loosely grouped cells", trophectoderm_grade="B — moderate cell number",
               quality_score=74, status=EmbryoStatus.UNDER_REVIEW, graded_by_id=staff["embryologist"].id,
               embryologist_notes="Good quality Day 6 blastocyst. Delayed expansion but viable."),
        Embryo(cycle_id=cycle.id, label="E-04", day=5, grade="3BC", expansion="Full blastocyst",
               icm_grade="B — moderate quality", trophectoderm_grade="C — sparse, irregular cells",
               quality_score=58, status=EmbryoStatus.UNDER_REVIEW, graded_by_id=staff["embryologist"].id,
               embryologist_notes="Fair quality. Trophectoderm grading borderline. Awaiting joint review."),
        Embryo(cycle_id=cycle.id, label="E-05", day=6, grade="3CC", expansion="Full blastocyst",
               icm_grade="C — few cells", trophectoderm_grade="C — sparse cells",
               quality_score=31, status=EmbryoStatus.NOT_SUITABLE, graded_by_id=staff["embryologist"].id,
               embryologist_notes="Poor morphology on Day 6. Discussed with couple — not recommended for cryopreservation."),
    ]
    session.add_all(embryos)
    await session.flush()

    # E-02 and E-03 are vitrified and stored — matches the frontend's original
    # CRYO_HIERARCHY fixture (Tank A / Canister 04 / Cane 02, Straws 03/04).
    e02, e03 = embryos[1], embryos[2]
    e02.status = EmbryoStatus.CRYOPRESERVED
    e03.status = EmbryoStatus.CRYOPRESERVED
    loc_e02 = CryoLocation(
        tank="Tank A", canister="Canister 04", cane="Cane 02", goblet="Goblet 05", straw="Straw 03",
        embryo_id=e02.id, frozen_at=date(2026, 8, 4), consent_verified=True, renewal_due=date(2027, 8, 4),
    )
    loc_e03 = CryoLocation(
        tank="Tank A", canister="Canister 04", cane="Cane 02", goblet="Goblet 05", straw="Straw 04",
        embryo_id=e03.id, frozen_at=date(2026, 8, 5), consent_verified=True, renewal_due=date(2027, 8, 5),
    )
    session.add_all([loc_e02, loc_e03])
    await session.flush()

    session.add_all([
        CryoCustodyEvent(location_id=loc_e02.id, embryo_id=e02.id, event_type="vitrified",
                          performed_by_id=staff["embryologist"].id,
                          occurred_at=datetime(2026, 8, 4, 11, 42, tzinfo=timezone.utc),
                          notes="Vitrification completed — E-02 loaded to Straw 03"),
        CryoCustodyEvent(location_id=loc_e03.id, embryo_id=e03.id, event_type="vitrified",
                          performed_by_id=staff["embryologist"].id,
                          occurred_at=datetime(2026, 8, 5, 10, 20, tzinfo=timezone.utc),
                          notes="E-03 vitrified and stored in Straw 04"),
    ])

    pregnancy = PregnancyRecord(
        cycle_id=cycle.id, transfer_date=date(2026, 8, 7),
        outcome=PregnancyOutcome.POSITIVE, estimated_due_date=date(2027, 5, 15),
    )
    session.add(pregnancy)
    await session.flush()

    session.add_all([
        BetaHcgResult(pregnancy_id=pregnancy.id, day_label="Day 14", value_miu_ml=612, recorded_at=date(2026, 8, 21), interpretation="Positive"),
        BetaHcgResult(pregnancy_id=pregnancy.id, day_label="Day 16", value_miu_ml=1248, recorded_at=date(2026, 8, 23), interpretation="Appropriate rise"),
        BetaHcgResult(pregnancy_id=pregnancy.id, day_label="Day 21", value_miu_ml=5840, recorded_at=date(2026, 8, 28), interpretation="Strong progression"),
        PregnancyMilestone(pregnancy_id=pregnancy.id, label="Embryo Transfer", milestone_date=date(2026, 8, 7),
                            detail="Single blastocyst E-01 transferred", is_completed=True),
        PregnancyMilestone(pregnancy_id=pregnancy.id, label="Positive Beta-hCG", milestone_date=date(2026, 8, 21),
                            detail="612 mIU/mL — biochemical pregnancy confirmed", is_completed=True),
        PregnancyMilestone(pregnancy_id=pregnancy.id, label="Gestational Sac", milestone_date=date(2026, 9, 4),
                            detail="6 weeks — single intrauterine sac visualised", is_completed=True),
        PregnancyMilestone(pregnancy_id=pregnancy.id, label="Cardiac Activity", milestone_date=date(2026, 9, 11),
                            detail="7 weeks — fetal heart rate 128 bpm", is_completed=True),
        PregnancyMilestone(pregnancy_id=pregnancy.id, label="First Trimester Scan", milestone_date=date(2026, 10, 9),
                            detail="11-13 weeks NT scan scheduled", is_completed=False),
        PregnancyMilestone(pregnancy_id=pregnancy.id, label="Delivery Outcome", milestone_date=date(2027, 5, 15),
                            detail="Estimated due date", is_completed=False),
    ])

    print(f"Seeded demo couple: Priya Raman ({priya.uhid}) & Arjun Kumar ({arjun.uhid}), cycle {cycle.cycle_number}")
    print(f"Seeded {len(embryos)} embryos (2 cryopreserved) for cycle {cycle.cycle_number}")
    print("Seeded pregnancy record with 3 beta-hCG results and 6 milestones")


async def main() -> None:
    with_demo = "--with-demo-data" in sys.argv
    async with AsyncSessionLocal() as session:
        await seed_roles_and_permissions(session)
        staff = await seed_staff(session)
        if with_demo:
            await seed_demo_clinical_data(session, staff)
        await session.commit()

    print(f"\nSeeded {len(DEMO_STAFF)} staff accounts. Default password for all: {DEMO_PASSWORD}")
    print("Every account has must_change_password=True — the first login must rotate this immediately.")


if __name__ == "__main__":
    asyncio.run(main())
