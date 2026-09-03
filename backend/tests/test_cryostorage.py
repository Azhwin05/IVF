"""
Embryo transfer checklist gate — the server-side enforcement behind the
frontend's 6-point safety checklist UI (spec §6/§20) — plus the ET
payment-clearance gate (source doc §19, new requirement).
"""
import uuid
from datetime import date

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.embryology.models import Embryo
from app.ivf.models import IVFCycle
from app.patients.models import Couple, Patient


async def _clear_et_charge(client: AsyncClient, admin_headers: dict, *, patient_id, cycle_id) -> None:
    """Completing a transfer is payment-gated (source doc §19) — raise and
    fully pay the tagged charge so tests can reach the gated behavior
    they're actually testing (the checklist), same as how the checklist
    itself has to be fully checked first."""
    invoice_resp = await client.post(
        "/api/v1/billing/invoices", headers=admin_headers,
        json={
            "patient_id": str(patient_id),
            "charges": [{
                "service_code": "ET",
                "description": "Embryo Transfer",
                "amount_paise": 2500000,
                "source_module": "embryo_transfer",
                "source_entity_id": str(cycle_id),
            }],
        },
    )
    invoice = invoice_resp.json()
    await client.post(
        "/api/v1/billing/payments", headers={**admin_headers, "Idempotency-Key": str(uuid.uuid4())},
        json={"invoice_id": invoice["id"], "amount_paise": 2500000, "method": "cash"},
    )


async def _seed_cycle_with_embryo(db_session: AsyncSession, *, doctor_id):
    female = Patient(uhid="TEST-2026-00010", full_name="Test Female", gender="female")
    male = Patient(uhid="TEST-2026-00011", full_name="Test Male", gender="male")
    db_session.add_all([female, male])
    await db_session.flush()

    couple = Couple(female_patient_id=female.id, male_patient_id=male.id)
    db_session.add(couple)
    await db_session.flush()

    cycle = IVFCycle(
        cycle_number="TEST-IVF-00001", couple_id=couple.id,
        primary_doctor_id=doctor_id,
        protocol="Test Protocol", treatment="IVF", started_at=date.today(),
    )
    db_session.add(cycle)
    await db_session.flush()

    embryo = Embryo(cycle_id=cycle.id, label="E-01", day=5, grade="4AA")
    db_session.add(embryo)
    await db_session.commit()
    return cycle, embryo


async def test_transfer_cannot_complete_with_unchecked_items(
    client: AsyncClient, admin_headers: dict, db_session: AsyncSession, admin_user
):
    cycle, embryo = await _seed_cycle_with_embryo(db_session, doctor_id=admin_user.id)

    create_resp = await client.post(
        "/api/v1/cryostorage/transfers", headers=admin_headers,
        json={
            "cycle_id": str(cycle.id), "embryo_id": str(embryo.id),
            "procedure_doctor_id": str(admin_user.id), "embryologist_id": str(admin_user.id),
            "transfer_date": date.today().isoformat(),
        },
    )
    assert create_resp.status_code == 201
    transfer = create_resp.json()
    assert len(transfer["checklist"]) == 6
    assert all(not item["checked"] for item in transfer["checklist"])

    # Attempting to complete with ZERO items checked must fail.
    complete_resp = await client.post(f"/api/v1/cryostorage/transfers/{transfer['id']}/complete", headers=admin_headers)
    assert complete_resp.status_code == 422
    assert complete_resp.json()["error_code"] == "checklist_incomplete"


async def test_transfer_completes_only_after_all_six_items_checked(
    client: AsyncClient, admin_headers: dict, db_session: AsyncSession, admin_user
):
    cycle, embryo = await _seed_cycle_with_embryo(db_session, doctor_id=admin_user.id)

    create_resp = await client.post(
        "/api/v1/cryostorage/transfers", headers=admin_headers,
        json={
            "cycle_id": str(cycle.id), "embryo_id": str(embryo.id),
            "procedure_doctor_id": str(admin_user.id), "embryologist_id": str(admin_user.id),
            "transfer_date": date.today().isoformat(),
        },
    )
    transfer = create_resp.json()

    for item in transfer["checklist"]:
        check_resp = await client.post(
            f"/api/v1/cryostorage/transfers/{transfer['id']}/checklist/{item['item_code']}", headers=admin_headers
        )
        assert check_resp.status_code == 204

    couple = await db_session.get(Couple, cycle.couple_id)
    await _clear_et_charge(client, admin_headers, patient_id=couple.female_patient_id, cycle_id=cycle.id)

    complete_resp = await client.post(f"/api/v1/cryostorage/transfers/{transfer['id']}/complete", headers=admin_headers)
    assert complete_resp.status_code == 200
    assert complete_resp.json()["completed"] is True


async def test_transfer_cannot_be_completed_twice(
    client: AsyncClient, admin_headers: dict, db_session: AsyncSession, admin_user
):
    cycle, embryo = await _seed_cycle_with_embryo(db_session, doctor_id=admin_user.id)
    create_resp = await client.post(
        "/api/v1/cryostorage/transfers", headers=admin_headers,
        json={
            "cycle_id": str(cycle.id), "embryo_id": str(embryo.id),
            "procedure_doctor_id": str(admin_user.id), "embryologist_id": str(admin_user.id),
            "transfer_date": date.today().isoformat(),
        },
    )
    transfer = create_resp.json()
    for item in transfer["checklist"]:
        await client.post(f"/api/v1/cryostorage/transfers/{transfer['id']}/checklist/{item['item_code']}", headers=admin_headers)

    couple = await db_session.get(Couple, cycle.couple_id)
    await _clear_et_charge(client, admin_headers, patient_id=couple.female_patient_id, cycle_id=cycle.id)

    first = await client.post(f"/api/v1/cryostorage/transfers/{transfer['id']}/complete", headers=admin_headers)
    assert first.status_code == 200

    second = await client.post(f"/api/v1/cryostorage/transfers/{transfer['id']}/complete", headers=admin_headers)
    assert second.status_code == 409
