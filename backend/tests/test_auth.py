"""
Auth flow tests — login, lockout, and the refresh-token reuse-detection
guarantee (spec §6). These are the highest-stakes tests in the suite:
if login throttling or reuse detection silently breaks, every other
security control downstream is moot.
"""
from httpx import AsyncClient

from app.users.models import User


async def test_login_success_returns_token_pair(client: AsyncClient, doctor_user: User):
    resp = await client.post("/api/v1/auth/login", json={"email": "doctor@example.com", "password": "TestPass123!"})
    assert resp.status_code == 200
    body = resp.json()
    assert "access_token" in body
    assert "refresh_token" in body


async def test_login_wrong_password_fails(client: AsyncClient, doctor_user: User):
    resp = await client.post("/api/v1/auth/login", json={"email": "doctor@example.com", "password": "WrongPassword"})
    assert resp.status_code == 401


async def test_login_locks_account_after_max_attempts(client: AsyncClient, doctor_user: User):
    for _ in range(5):
        await client.post("/api/v1/auth/login", json={"email": "doctor@example.com", "password": "wrong"})

    # 6th attempt, even with the CORRECT password, must be blocked while locked
    resp = await client.post("/api/v1/auth/login", json={"email": "doctor@example.com", "password": "TestPass123!"})
    assert resp.status_code == 401
    assert "locked" in resp.json()["message"].lower()


async def test_me_requires_valid_token(client: AsyncClient):
    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code == 401


async def test_me_returns_current_user(client: AsyncClient, auth_headers: dict):
    resp = await client.get("/api/v1/auth/me", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["email"] == "doctor@example.com"


async def test_refresh_token_reuse_revokes_session(client: AsyncClient, doctor_user: User):
    """The core reuse-detection guarantee: rotating a refresh token once
    is fine; presenting the SAME (now-superseded) token a second time
    must invalidate the whole session, not just fail quietly."""
    login = await client.post("/api/v1/auth/login", json={"email": "doctor@example.com", "password": "TestPass123!"})
    original_refresh = login.json()["refresh_token"]

    first_refresh = await client.post("/api/v1/auth/refresh", json={"refresh_token": original_refresh})
    assert first_refresh.status_code == 200

    # Replaying the original (already-rotated) token must fail...
    replay = await client.post("/api/v1/auth/refresh", json={"refresh_token": original_refresh})
    assert replay.status_code == 401

    # ...and the NEW token issued by the legitimate first refresh must
    # ALSO now be dead, because reuse detection revokes the whole session.
    new_refresh = first_refresh.json()["refresh_token"]
    after_revocation = await client.post("/api/v1/auth/refresh", json={"refresh_token": new_refresh})
    assert after_revocation.status_code == 401
