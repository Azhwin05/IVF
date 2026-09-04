"""
Couple registration — regression coverage for the "Could not create the
couple. Please try again." failure.

The bug: create_couple returned a freshly-added Couple whose female_patient
/ male_patient relationships had never been through a SELECT, so
lazy="selectin" never fired. FastAPI then lazy-loaded them while
serialising CoupleOut, on the async session, outside a greenlet context —
raising MissingGreenlet and turning a successful create into a 500.
"""
from httpx import AsyncClient


async def test_create_couple_returns_201_with_both_partner_records(
    client: AsyncClient, admin_headers: dict
):
    resp = await client.post(
        "/api/v1/patients/couples",
        headers=admin_headers,
        json={
            "female_patient": {
                "full_name": "Asha Menon",
                "date_of_birth": "1991-04-12",
                "gender": "female",
                "blood_group": "B Positive",
                "is_international": False,
                "phone": "9000000001",
            },
            "male_patient": {
                "full_name": "Rahul Menon",
                "gender": "male",
                "blood_group": "O Positive",
                "phone": "9000000002",
                "occupation": "Engineer",
            },
            "infertility_type": "Primary Infertility",
            "infertility_duration": "2 years",
            "previous_iui_cycles": 1,
            "previous_ivf_cycles": 0,
        },
    )

    assert resp.status_code == 201, resp.text
    body = resp.json()

    # The relationships that used to blow up serialisation must be present
    # and correctly separated.
    assert body["female_patient"]["full_name"] == "Asha Menon"
    assert body["female_patient"]["gender"] == "female"
    assert body["male_patient"]["full_name"] == "Rahul Menon"
    assert body["male_patient"]["gender"] == "male"
    assert body["female_patient"]["id"] != body["male_patient"]["id"]
    assert body["female_patient"]["uhid"].startswith("DAIVF-")
    assert body["male_patient"]["uhid"].startswith("DAIVF-")
    assert body["female_patient"]["uhid"] != body["male_patient"]["uhid"]


async def test_created_couple_is_retrievable_by_either_partner(
    client: AsyncClient, admin_headers: dict
):
    created = (
        await client.post(
            "/api/v1/patients/couples",
            headers=admin_headers,
            json={
                "female_patient": {"full_name": "Lena Roy", "gender": "female"},
                "male_patient": {"full_name": "Sam Roy", "gender": "male"},
                "infertility_type": "Primary Infertility",
            },
        )
    ).json()

    for partner_key in ("female_patient", "male_patient"):
        pid = created[partner_key]["id"]
        resp = await client.get(
            f"/api/v1/patients/couples/by-patient/{pid}", headers=admin_headers
        )
        assert resp.status_code == 200, resp.text
        fetched = resp.json()
        assert fetched["id"] == created["id"]
        assert fetched["female_patient"]["full_name"] == "Lena Roy"
        assert fetched["male_patient"]["full_name"] == "Sam Roy"


async def test_photo_document_attaches_to_the_correct_partner(
    client: AsyncClient, admin_headers: dict
):
    created = (
        await client.post(
            "/api/v1/patients/couples",
            headers=admin_headers,
            json={
                "female_patient": {"full_name": "Photo Wife", "gender": "female"},
                "male_patient": {"full_name": "Photo Husband", "gender": "male"},
                "infertility_type": "Primary Infertility",
            },
        )
    ).json()
    female_id = created["female_patient"]["id"]
    male_id = created["male_patient"]["id"]

    # 1x1 PNG
    png = bytes.fromhex(
        "89504e470d0a1a0a0000000d49484452000000010000000108020000009077053a"
        "0000000a49444154789c6360000002000154a24f2d0000000049454e44ae426082"
    )

    up = await client.post(
        f"/api/v1/patients/{female_id}/documents?document_type=photo",
        headers=admin_headers,
        files={"file": ("wife.png", png, "image/png")},
    )
    assert up.status_code == 201, up.text

    # The female patient now has a photo; the male patient still does not —
    # the two photo controls never cross-attach. Read it back off the couple
    # projection, whose PatientSummary carries photo_document_id.
    couple = (
        await client.get(
            f"/api/v1/patients/couples/by-patient/{female_id}", headers=admin_headers
        )
    ).json()
    assert couple["female_patient"]["photo_document_id"] is not None
    assert couple["male_patient"]["photo_document_id"] is None
