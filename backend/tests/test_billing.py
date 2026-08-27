"""
Billing tests — idempotent payments (spec §34/§35) and overpayment
rejection are the two guarantees that matter most here.
"""
import uuid

from httpx import AsyncClient

from app.patients.models import Patient


async def _create_invoice(client: AsyncClient, headers: dict, patient_id: str) -> dict:
    resp = await client.post(
        "/api/v1/billing/invoices", headers=headers,
        json={"patient_id": patient_id, "charges": [{"service_code": "CONSULT", "description": "Consultation", "amount_paise": 150000}]},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


async def test_create_invoice_and_pay_in_full(client: AsyncClient, admin_headers: dict, sample_patient: Patient):
    invoice = await _create_invoice(client, admin_headers, str(sample_patient.id))
    assert invoice["outstanding_paise"] == 150000

    pay_resp = await client.post(
        "/api/v1/billing/payments", headers={**admin_headers, "Idempotency-Key": str(uuid.uuid4())},
        json={"invoice_id": invoice["id"], "amount_paise": 150000, "method": "cash"},
    )
    assert pay_resp.status_code == 201

    check = await client.get(f"/api/v1/billing/invoices/{invoice['id']}", headers=admin_headers)
    assert check.json()["status"] == "paid"
    assert check.json()["outstanding_paise"] == 0


async def test_overpayment_is_rejected(client: AsyncClient, admin_headers: dict, sample_patient: Patient):
    invoice = await _create_invoice(client, admin_headers, str(sample_patient.id))

    resp = await client.post(
        "/api/v1/billing/payments", headers={**admin_headers, "Idempotency-Key": str(uuid.uuid4())},
        json={"invoice_id": invoice["id"], "amount_paise": 999999, "method": "cash"},
    )
    assert resp.status_code == 422
    assert resp.json()["error_code"] == "overpayment_rejected"


async def test_duplicate_payment_request_is_idempotent(client: AsyncClient, admin_headers: dict, sample_patient: Patient):
    """The exact scenario spec §35 warns about: a double-click or client
    retry with the same Idempotency-Key must produce ONE payment, not two."""
    invoice = await _create_invoice(client, admin_headers, str(sample_patient.id))
    key = str(uuid.uuid4())
    payload = {"invoice_id": invoice["id"], "amount_paise": 50000, "method": "upi"}

    first = await client.post("/api/v1/billing/payments", headers={**admin_headers, "Idempotency-Key": key}, json=payload)
    second = await client.post("/api/v1/billing/payments", headers={**admin_headers, "Idempotency-Key": key}, json=payload)

    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["receipt_number"] == second.json()["receipt_number"]  # same payment, not two

    check = await client.get(f"/api/v1/billing/invoices/{invoice['id']}", headers=admin_headers)
    assert check.json()["paid_amount_paise"] == 50000  # NOT 100000 — proves no double-charge


async def test_refund_cannot_exceed_amount_paid(client: AsyncClient, admin_headers: dict, sample_patient: Patient):
    invoice = await _create_invoice(client, admin_headers, str(sample_patient.id))
    await client.post(
        "/api/v1/billing/payments", headers={**admin_headers, "Idempotency-Key": str(uuid.uuid4())},
        json={"invoice_id": invoice["id"], "amount_paise": 50000, "method": "cash"},
    )

    resp = await client.post(
        "/api/v1/billing/refunds", headers={**admin_headers, "Idempotency-Key": str(uuid.uuid4())},
        json={"invoice_id": invoice["id"], "amount_paise": 100000, "reason": "Test refund exceeding payment"},
    )
    assert resp.status_code == 422
