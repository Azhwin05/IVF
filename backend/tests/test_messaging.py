"""
WhatsApp/SMS opt-in gate — source doc §27: promotional messages must
respect consent; transactional ones (appointment/treatment reminders)
must not be blocked by it.
"""
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.patients.models import Patient


async def _seed_patient_with_phone(db_session: AsyncSession) -> Patient:
    patient = Patient(uhid="TEST-MSG-00001", full_name="Messaging Test Patient", gender="female", phone="+919876543210")
    db_session.add(patient)
    await db_session.commit()
    return patient


async def test_promotional_message_blocked_without_opt_in(client: AsyncClient, admin_headers: dict, db_session: AsyncSession):
    patient = await _seed_patient_with_phone(db_session)

    resp = await client.post(
        "/api/v1/messaging/send", headers=admin_headers,
        json={"patient_id": str(patient.id), "body": "New IVF package available!", "category": "promotional"},
    )
    assert resp.status_code == 422
    assert resp.json()["error_code"] == "promotional_opt_out"


async def test_promotional_message_sends_after_opt_in(client: AsyncClient, admin_headers: dict, db_session: AsyncSession):
    patient = await _seed_patient_with_phone(db_session)

    await client.put(f"/api/v1/messaging/preferences/{patient.id}", headers=admin_headers, json={"promotional_opt_in": True})

    resp = await client.post(
        "/api/v1/messaging/send", headers=admin_headers,
        json={"patient_id": str(patient.id), "body": "New IVF package available!", "category": "promotional"},
    )
    assert resp.status_code == 201
    assert resp.json()["status"] == "sent"


async def test_transactional_message_never_gated_on_opt_in(client: AsyncClient, admin_headers: dict, db_session: AsyncSession):
    patient = await _seed_patient_with_phone(db_session)  # no opt-in recorded

    resp = await client.post(
        "/api/v1/messaging/send", headers=admin_headers,
        json={"patient_id": str(patient.id), "body": "Your appointment is tomorrow at 10am.", "category": "transactional"},
    )
    assert resp.status_code == 201
    assert resp.json()["status"] == "sent"

    history = await client.get(f"/api/v1/messaging/history/{patient.id}", headers=admin_headers)
    assert len(history.json()) == 1
