"""
Donor matching — the critical, non-negotiable rule from the source doc
(§22/§35): a donor cannot be actively matched to more than one patient at
once, and this must be enforced by the database, not just the API layer.
"""
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.patients.models import Patient


async def _seed_two_patients(db_session: AsyncSession):
    p1 = Patient(uhid="TEST-DNR-00001", full_name="Recipient One", gender="female")
    p2 = Patient(uhid="TEST-DNR-00002", full_name="Recipient Two", gender="female")
    db_session.add_all([p1, p2])
    await db_session.commit()
    return p1, p2


async def test_donor_cannot_be_actively_matched_to_two_patients(
    client: AsyncClient, admin_headers: dict, db_session: AsyncSession
):
    patient_a, patient_b = await _seed_two_patients(db_session)

    create_resp = await client.post(
        "/api/v1/donors", headers=admin_headers,
        json={"category": "donor", "full_name": "Test Donor"},
    )
    assert create_resp.status_code == 201
    donor = create_resp.json()

    first_match = await client.post(
        "/api/v1/donors/matches", headers=admin_headers,
        json={"donor_id": donor["id"], "patient_id": str(patient_a.id)},
    )
    assert first_match.status_code == 201
    assert first_match.json()["is_active"] is True

    # Attempting a second ACTIVE match for the same donor must fail —
    # this is the database constraint firing, not application logic that
    # a race condition could slip past.
    second_match = await client.post(
        "/api/v1/donors/matches", headers=admin_headers,
        json={"donor_id": donor["id"], "patient_id": str(patient_b.id)},
    )
    assert second_match.status_code == 409
    assert second_match.json()["error_code"] == "donor_already_matched"


async def test_donor_can_be_rematched_after_ending_previous_match(
    client: AsyncClient, admin_headers: dict, db_session: AsyncSession
):
    patient_a, patient_b = await _seed_two_patients(db_session)

    create_resp = await client.post(
        "/api/v1/donors", headers=admin_headers,
        json={"category": "donor", "full_name": "Test Donor 2"},
    )
    donor = create_resp.json()

    first_match = await client.post(
        "/api/v1/donors/matches", headers=admin_headers,
        json={"donor_id": donor["id"], "patient_id": str(patient_a.id)},
    )
    match_id = first_match.json()["id"]

    end_resp = await client.post(
        f"/api/v1/donors/matches/{match_id}/end", headers=admin_headers,
        json={"reason": "Cycle cancelled by patient"},
    )
    assert end_resp.status_code == 200
    assert end_resp.json()["is_active"] is False

    # Now that the previous match has ended, a new active match is allowed.
    second_match = await client.post(
        "/api/v1/donors/matches", headers=admin_headers,
        json={"donor_id": donor["id"], "patient_id": str(patient_b.id)},
    )
    assert second_match.status_code == 201
    assert second_match.json()["is_active"] is True

    history = await client.get(f"/api/v1/donors/{donor['id']}/matches", headers=admin_headers)
    assert len(history.json()) == 2


async def test_donor_benchmark_flags_underperformance_by_configured_threshold(
    client: AsyncClient, admin_headers: dict, db_session: AsyncSession
):
    """Confirms the threshold is whatever the caller passes — never a
    hardcoded percentage (source doc §23 explicitly forbids assuming the
    ~30% figure mentioned in the client meeting is a universal rule)."""
    create_resp = await client.post(
        "/api/v1/donors", headers=admin_headers,
        json={"category": "donor", "full_name": "Test Donor 3"},
    )
    donor = create_resp.json()

    # 50% deviation, but threshold set high (60%) -> not flagged.
    ok_resp = await client.post(
        "/api/v1/donors/benchmarks", headers=admin_headers,
        json={
            "donor_id": donor["id"], "metric_name": "Fertilization Rate",
            "expected_value": 80, "actual_value": 40, "threshold_percent": 60,
        },
    )
    assert ok_resp.status_code == 201
    assert ok_resp.json()["is_underperforming"] is False

    # Same 50% deviation, threshold set low (10%) -> flagged.
    flagged_resp = await client.post(
        "/api/v1/donors/benchmarks", headers=admin_headers,
        json={
            "donor_id": donor["id"], "metric_name": "Blastocyst Rate",
            "expected_value": 80, "actual_value": 40, "threshold_percent": 10,
        },
    )
    assert flagged_resp.status_code == 201
    assert flagged_resp.json()["is_underperforming"] is True
