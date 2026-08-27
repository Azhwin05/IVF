"""
Seeds roles, permissions, demo staff accounts, and (optionally) the
demo patient/couple/cycle data matching the existing frontend's mock
data — so a fresh environment is immediately demoable end-to-end with
the same Priya Raman / Arjun Kumar story the prototype already tells.

Run: python -m scripts.seed_db [--with-demo-data]
"""
import asyncio
import sys
from datetime import date

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
    from app.embryology.models import Embryo, EmbryoStatus, OocyteAssessment
    from app.ivf.models import CycleStage, IVFCycle, MonitoringVisit
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
    print(f"Seeded demo couple: Priya Raman ({priya.uhid}) & Arjun Kumar ({arjun.uhid}), cycle {cycle.cycle_number}")


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
