"""
Discharge summary — proves the aggregation is real (pulls actual rows
from actual tables across modules), not a stub returning empty lists
regardless of what exists (source doc §21).
"""
from datetime import date

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.embryology.models import Embryo
from app.ivf.models import IVFCycle
from app.patients.models import Couple, Patient


async def test_discharge_summary_aggregates_across_modules(
    client: AsyncClient, admin_headers: dict, db_session: AsyncSession, admin_user
):
    female = Patient(uhid="TEST-DS-00001", full_name="Discharge Test Patient", gender="female")
    male = Patient(uhid="TEST-DS-00002", full_name="Discharge Test Partner", gender="male")
    db_session.add_all([female, male])
    await db_session.flush()

    couple = Couple(female_patient_id=female.id, male_patient_id=male.id)
    db_session.add(couple)
    await db_session.flush()

    cycle = IVFCycle(
        cycle_number="TEST-DS-IVF-00001", couple_id=couple.id,
        primary_doctor_id=admin_user.id,
        protocol="Test Protocol", treatment="IVF", started_at=date.today(),
    )
    db_session.add(cycle)
    await db_session.flush()

    embryo = Embryo(cycle_id=cycle.id, label="E-01", day=5, grade="4AA")
    db_session.add(embryo)
    await db_session.commit()

    # Add a prescription through the real endpoint, so this test also
    # exercises the new prescription module end-to-end.
    presc_resp = await client.post(
        "/api/v1/prescriptions", headers=admin_headers,
        json={
            "patient_id": str(female.id), "cycle_id": str(cycle.id), "category": "green",
            "lines": [{"medicine_name": "Folic Acid", "dosage": "5mg", "frequency": "once daily"}],
        },
    )
    assert presc_resp.status_code == 201

    summary_resp = await client.get(f"/api/v1/reports/discharge-summary/{female.id}", headers=admin_headers)
    assert summary_resp.status_code == 200
    summary = summary_resp.json()

    assert summary["patient"]["uhid"] == "TEST-DS-00001"
    assert summary["couple"]["partner_name"] == "Discharge Test Partner"
    assert len(summary["cycles"]) == 1
    assert summary["cycles"][0]["cycle_number"] == "TEST-DS-IVF-00001"
    assert len(summary["embryos"]) == 1
    assert summary["embryos"][0]["label"] == "E-01"
    assert len(summary["prescriptions"]) == 1
    assert summary["prescriptions"][0]["category"] == "green"


async def test_discharge_summary_404s_for_unknown_patient(client: AsyncClient, admin_headers: dict):
    resp = await client.get(
        "/api/v1/reports/discharge-summary/00000000-0000-0000-0000-000000000000", headers=admin_headers
    )
    assert resp.status_code == 404
