"""API + DB tests for outside-lab report ingestion.

Covers the end-to-end flow the feature exists for: upload -> extract -> review
-> correct, with the safety guarantees intact (extracted snapshot preserved,
corrections append-only, unreadable fields flagged not guessed, permissions
enforced). Uses the project's real Postgres test database and real login-issued
tokens via the shared conftest fixtures.
"""

from pathlib import Path

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.laboratory.extraction.ocr import ocr_available
from app.patients.models import Patient
from app.roles.models import Role
from app.users.models import User

FIXTURES = Path(__file__).parent / "fixtures" / "lab_reports" / "reports"
BASE = "/api/v1/laboratory/reports"


@pytest.fixture
async def receptionist_headers(client: AsyncClient, db_session: AsyncSession, seeded_roles) -> dict:
    """A signed-in user whose role holds no laboratory.* permissions."""
    role = (await db_session.execute(select(Role).where(Role.code == "receptionist"))).scalar_one()
    user = User(
        employee_code="TEST-RCP-001", full_name="Front Desk", email="reception@example.com",
        role_id=role.id, password_hash=hash_password("TestPass123!"),
    )
    db_session.add(user)
    await db_session.commit()
    resp = await client.post(
        "/api/v1/auth/login", json={"email": "reception@example.com", "password": "TestPass123!"}
    )
    assert resp.status_code == 200, resp.text
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


async def _upload(client: AsyncClient, headers: dict, patient_id: str, filename: str) -> dict:
    data = (FIXTURES / filename).read_bytes()
    ctype = "application/pdf" if filename.endswith(".pdf") else "image/png"
    resp = await client.post(
        BASE,
        headers=headers,
        data={"patient_id": patient_id},
        files={"file": (filename, data, ctype)},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


class TestUploadAndList:
    async def test_upload_then_appears_in_list(
        self, client: AsyncClient, admin_headers: dict, sample_patient: Patient
    ):
        body = await _upload(client, admin_headers, str(sample_patient.id), "report_A_clean_table.pdf")
        assert body["extraction_status"] == "pending"
        assert body["extraction_method"] == "none"
        assert body["patient"]["id"] == str(sample_patient.id)
        assert body["results"] == []

        page = (await client.get(BASE, headers=admin_headers)).json()
        assert body["id"] in [r["id"] for r in page["items"]]
        assert {"items", "next_cursor", "has_more"} <= set(page)

    async def test_duplicate_upload_is_rejected(
        self, client: AsyncClient, admin_headers: dict, sample_patient: Patient
    ):
        await _upload(client, admin_headers, str(sample_patient.id), "report_A_clean_table.pdf")
        data = (FIXTURES / "report_A_clean_table.pdf").read_bytes()
        resp = await client.post(
            BASE, headers=admin_headers,
            data={"patient_id": str(sample_patient.id)},
            files={"file": ("report_A_clean_table.pdf", data, "application/pdf")},
        )
        assert resp.status_code == 409
        assert resp.json()["error_code"] == "conflict"

    async def test_upload_requires_permission(
        self, client: AsyncClient, receptionist_headers: dict, sample_patient: Patient
    ):
        data = (FIXTURES / "report_A_clean_table.pdf").read_bytes()
        resp = await client.post(
            BASE, headers=receptionist_headers,
            data={"patient_id": str(sample_patient.id)},
            files={"file": ("r.pdf", data, "application/pdf")},
        )
        assert resp.status_code == 403

    async def test_upload_requires_authentication(
        self, client: AsyncClient, sample_patient: Patient
    ):
        data = (FIXTURES / "report_A_clean_table.pdf").read_bytes()
        resp = await client.post(
            BASE, data={"patient_id": str(sample_patient.id)},
            files={"file": ("r.pdf", data, "application/pdf")},
        )
        assert resp.status_code == 401

    async def test_upload_unknown_patient_is_422(self, client: AsyncClient, admin_headers: dict):
        data = (FIXTURES / "report_A_clean_table.pdf").read_bytes()
        resp = await client.post(
            BASE, headers=admin_headers,
            data={"patient_id": "00000000-0000-0000-0000-000000000000"},
            files={"file": ("r.pdf", data, "application/pdf")},
        )
        assert resp.status_code == 422


class TestExtraction:
    async def test_digital_pdf_extracts_structured_rows(
        self, client: AsyncClient, admin_headers: dict, sample_patient: Patient
    ):
        report = await _upload(client, admin_headers, str(sample_patient.id), "report_A_clean_table.pdf")
        detail = (
            await client.post(f"{BASE}/{report['id']}/extraction", headers=admin_headers)
        ).json()

        assert detail["extraction_status"] == "completed"
        assert detail["extraction_method"] == "native_pdf_text"
        assert detail["document_kind"] == "digital_pdf"
        assert len(detail["results"]) >= 1

        for r in detail["results"]:
            # A saved result always has a name + value, or it is flagged
            # not_extracted with its fields left blank - never fabricated.
            if r["validation_status"] != "not_extracted":
                assert (r["test_name"] or "").strip()
                assert (r["value"] or "").strip()
            # Field lengths respect the DB column ceilings (Postgres enforces).
            assert len(r["test_name"] or "") <= 200
            assert len(r["value"] or "") <= 120
            assert len(r["unit"] or "") <= 60
            assert len(r["reference_range"] or "") <= 120
            # The extracted snapshot mirrors what extraction produced.
            assert r["extracted_test_name"] == r["test_name"]
            assert r["entry_origin"] == "extracted"

    async def test_document_download_streams_the_original(
        self, client: AsyncClient, admin_headers: dict, sample_patient: Patient
    ):
        report = await _upload(client, admin_headers, str(sample_patient.id), "report_A_clean_table.pdf")
        resp = await client.get(f"{BASE}/{report['id']}/document", headers=admin_headers)
        assert resp.status_code == 200
        assert resp.headers["content-type"].startswith("application/pdf")
        assert resp.content == (FIXTURES / "report_A_clean_table.pdf").read_bytes()

    @pytest.mark.skipif(not ocr_available(), reason="Tesseract OCR not installed")
    async def test_scanned_image_goes_through_ocr(
        self, client: AsyncClient, admin_headers: dict, sample_patient: Patient
    ):
        report = await _upload(client, admin_headers, str(sample_patient.id), "report_G_ocr_stress.png")
        detail = (
            await client.post(f"{BASE}/{report['id']}/extraction", headers=admin_headers)
        ).json()
        assert detail["extraction_status"] == "completed"
        assert detail["extraction_method"] == "ocr"
        assert detail["document_kind"] == "image"
        assert len(detail["results"]) >= 1


class TestCorrectionAndManualEntry:
    async def test_correction_preserves_snapshot_and_appends_history(
        self, client: AsyncClient, admin_headers: dict, sample_patient: Patient
    ):
        report = await _upload(client, admin_headers, str(sample_patient.id), "report_A_clean_table.pdf")
        detail = (
            await client.post(f"{BASE}/{report['id']}/extraction", headers=admin_headers)
        ).json()
        target = next(r for r in detail["results"] if r["value"])
        original_extracted_value = target["extracted_value"]

        patched = (
            await client.patch(
                f"{BASE}/results/{target['id']}",
                headers=admin_headers,
                json={"value": "CORRECTED-1", "reason": "typo in source"},
            )
        ).json()

        assert patched["value"] == "CORRECTED-1"
        # The immutable snapshot is untouched by the correction.
        assert patched["extracted_value"] == original_extracted_value
        assert patched["extracted_test_name"] == target["extracted_test_name"]

        history = (
            await client.get(f"{BASE}/results/{target['id']}/corrections", headers=admin_headers)
        ).json()
        assert len(history) == 1
        assert history[0]["field"] == "value"
        assert history[0]["previous_value"] == original_extracted_value
        assert history[0]["new_value"] == "CORRECTED-1"
        assert history[0]["reason"] == "typo in source"

        # A second correction appends; it never overwrites the first.
        await client.patch(
            f"{BASE}/results/{target['id']}", headers=admin_headers, json={"value": "CORRECTED-2"}
        )
        history2 = (
            await client.get(f"{BASE}/results/{target['id']}/corrections", headers=admin_headers)
        ).json()
        assert [h["new_value"] for h in history2] == ["CORRECTED-1", "CORRECTED-2"]
        assert [h["previous_value"] for h in history2] == [original_extracted_value, "CORRECTED-1"]

    async def test_no_op_correction_is_rejected(
        self, client: AsyncClient, admin_headers: dict, sample_patient: Patient
    ):
        report = await _upload(client, admin_headers, str(sample_patient.id), "report_A_clean_table.pdf")
        detail = (
            await client.post(f"{BASE}/{report['id']}/extraction", headers=admin_headers)
        ).json()
        target = next(r for r in detail["results"] if r["value"])
        resp = await client.patch(
            f"{BASE}/results/{target['id']}", headers=admin_headers, json={"value": target["value"]}
        )
        assert resp.status_code == 422

    async def test_manual_result_has_no_extracted_snapshot(
        self, client: AsyncClient, admin_headers: dict, sample_patient: Patient
    ):
        report = await _upload(client, admin_headers, str(sample_patient.id), "report_A_clean_table.pdf")
        created = (
            await client.post(
                f"{BASE}/{report['id']}/results",
                headers=admin_headers,
                json={"test_name": "Manual TSH", "value": "2.1", "unit": "mIU/L", "reference_range": "0.4-4.0"},
            )
        ).json()
        assert created["entry_origin"] == "manual"
        assert created["extracted_test_name"] is None
        assert created["extracted_value"] is None
        assert created["normalization_match"] == "manual"

    async def test_correction_requires_permission(
        self, client: AsyncClient, admin_headers: dict, receptionist_headers: dict, sample_patient: Patient
    ):
        report = await _upload(client, admin_headers, str(sample_patient.id), "report_A_clean_table.pdf")
        detail = (
            await client.post(f"{BASE}/{report['id']}/extraction", headers=admin_headers)
        ).json()
        target = detail["results"][0]
        resp = await client.patch(
            f"{BASE}/results/{target['id']}", headers=receptionist_headers, json={"value": "x"}
        )
        assert resp.status_code == 403
