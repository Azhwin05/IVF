"""
Login, refresh, and logout business logic.

Security behaviors implemented here (see docs/security/authentication.md
for the full write-up once drafted):
  - Login throttling: N failed attempts within the lockout window locks
    the account for LOGIN_LOCKOUT_MINUTES (spec §6 "account lockout rules")
  - Passwords never logged; only success/failure + user id is audited
  - Access tokens are short-lived JWTs; refresh tokens are opaque,
    hashed at rest, single-use, and rotate on every refresh
  - Refresh-token reuse (a token used twice) revokes the entire session
    immediately — this is the "rotating refresh tokens + reuse detection"
    requirement from spec §6
  - Absolute session lifetime and idle timeout are both enforced
    independently of the JWT's own expiry
"""
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.service import record_audit_event
from app.auth.models import RefreshToken, Session
from app.core.config import get_settings
from app.core.exceptions import AuthenticationError
from app.core.security import (
    create_access_token,
    generate_refresh_token,
    hash_refresh_token,
    verify_password,
)
from app.users.models import User
from app.users.service import get_user_by_email

settings = get_settings()


async def _issue_token_pair(session: AsyncSession, *, user: User, auth_session: Session) -> tuple[str, str]:
    access = create_access_token(user_id=user.id, role=user.role.code, session_id=auth_session.id)

    raw_refresh = generate_refresh_token()
    now = datetime.now(timezone.utc)
    token_row = RefreshToken(
        session_id=auth_session.id,
        token_hash=hash_refresh_token(raw_refresh),
        issued_at=now,
        expires_at=now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )
    session.add(token_row)
    await session.flush()
    return access, raw_refresh


async def login(
    session: AsyncSession,
    *,
    email: str,
    password: str,
    ip_address: str | None,
    user_agent: str | None,
    device_label: str | None,
) -> tuple[str, str, User]:
    user = await get_user_by_email(session, email)

    # Constant-shape failure path: don't reveal whether the email exists.
    if user is None:
        raise AuthenticationError("Invalid email or password.")

    now = datetime.now(timezone.utc)
    if user.locked_until and user.locked_until > now:
        await record_audit_event(
            session, actor_id=user.id, actor_role=user.role.code,
            action="auth.login_blocked_locked", entity_type="User", entity_id=str(user.id),
            source_ip=ip_address,
        )
        # Commit before raising: the router-level get_db() dependency
        # rolls back the session on any exception propagating out of the
        # request, which would otherwise silently discard this audit
        # record — a security event must survive even a "failed" request,
        # per docs/security's audit-immutability rules.
        await session.commit()
        raise AuthenticationError("Account temporarily locked due to repeated failed logins. Try again later.")

    if not user.is_active:
        raise AuthenticationError("This account has been deactivated.")

    if not verify_password(password, user.password_hash):
        user.failed_login_attempts += 1
        if user.failed_login_attempts >= settings.LOGIN_MAX_ATTEMPTS:
            user.locked_until = now + timedelta(minutes=settings.LOGIN_LOCKOUT_MINUTES)
        await record_audit_event(
            session, actor_id=user.id, actor_role=user.role.code,
            action="auth.login_failed", entity_type="User", entity_id=str(user.id),
            source_ip=ip_address, reason=f"attempt {user.failed_login_attempts}",
        )
        # Same reasoning as above: the incremented failed_login_attempts
        # counter (and the lockout it may trigger) is the entire point of
        # this code path — it must persist even though we're about to
        # raise and fail the request. Without this explicit commit, the
        # brute-force lockout in spec §6 silently never engages, because
        # every failed attempt's own counter increment gets rolled back
        # by the exception that reports the failure to the caller.
        await session.commit()
        raise AuthenticationError("Invalid email or password.")

    # Success — reset throttle counters
    user.failed_login_attempts = 0
    user.locked_until = None
    user.last_login_at = now

    auth_session = Session(
        user_id=user.id,
        device_label=device_label,
        ip_address=ip_address,
        user_agent=user_agent,
        expires_at=now + timedelta(hours=settings.ABSOLUTE_SESSION_LIFETIME_HOURS),
        last_active_at=now,
    )
    session.add(auth_session)
    await session.flush()

    access, refresh = await _issue_token_pair(session, user=user, auth_session=auth_session)

    await record_audit_event(
        session, actor_id=user.id, actor_role=user.role.code,
        action="auth.login_success", entity_type="User", entity_id=str(user.id),
        source_ip=ip_address, session_id=auth_session.id,
    )
    return access, refresh, user


async def refresh_tokens(
    session: AsyncSession, *, raw_refresh_token: str, ip_address: str | None
) -> tuple[str, str]:
    token_hash = hash_refresh_token(raw_refresh_token)
    result = await session.execute(select(RefreshToken).where(RefreshToken.token_hash == token_hash))
    token_row = result.scalar_one_or_none()

    if token_row is None:
        raise AuthenticationError("Invalid refresh token.")

    now = datetime.now(timezone.utc)

    if token_row.used_at is not None:
        # REUSE DETECTED — this token was already rotated away. Someone is
        # replaying an old token (stolen, or a client bug). Nuke the session.
        auth_session = await session.get(Session, token_row.session_id)
        if auth_session and auth_session.is_valid:
            auth_session.revoked_at = now
            auth_session.revoked_reason = "refresh_token_reuse_detected"
            await record_audit_event(
                session, actor_id=auth_session.user_id, actor_role=None,
                action="auth.refresh_reuse_detected_session_revoked",
                entity_type="Session", entity_id=str(auth_session.id),
                source_ip=ip_address,
            )
            # This revocation IS the security control — it must survive the
            # exception we're about to raise, same reasoning as login()'s
            # lockout-counter commits above. Without this, reuse detection
            # would silently never actually revoke anything.
            await session.commit()
        raise AuthenticationError("Session invalidated — please log in again.")

    auth_session = await session.get(Session, token_row.session_id)
    if not auth_session or not auth_session.is_valid or auth_session.expires_at < now:
        raise AuthenticationError("Session expired — please log in again.")

    idle_cutoff = auth_session.last_active_at + timedelta(minutes=settings.IDLE_TIMEOUT_MINUTES)
    if idle_cutoff < now:
        auth_session.revoked_at = now
        auth_session.revoked_reason = "idle_timeout"
        await session.commit()
        raise AuthenticationError("Session expired due to inactivity — please log in again.")

    if token_row.expires_at < now:
        raise AuthenticationError("Refresh token expired — please log in again.")

    user = await session.get(User, auth_session.user_id)
    if not user or not user.is_active:
        raise AuthenticationError("Account unavailable.")

    # Rotate: mark old token used, issue a brand-new pair
    token_row.used_at = now
    auth_session.last_active_at = now

    new_access, new_refresh = await _issue_token_pair(session, user=user, auth_session=auth_session)

    # Link old -> new for forensic traceability
    new_token_hash = hash_refresh_token(new_refresh)
    new_row_result = await session.execute(select(RefreshToken).where(RefreshToken.token_hash == new_token_hash))
    new_row = new_row_result.scalar_one()
    token_row.replaced_by_id = new_row.id

    return new_access, new_refresh


async def logout(session: AsyncSession, *, session_id: uuid.UUID, actor_id: uuid.UUID) -> None:
    auth_session = await session.get(Session, session_id)
    if auth_session and auth_session.is_valid:
        auth_session.revoked_at = datetime.now(timezone.utc)
        auth_session.revoked_reason = "user_logout"
        await record_audit_event(
            session, actor_id=actor_id, actor_role=None,
            action="auth.logout", entity_type="Session", entity_id=str(session_id),
        )


async def revoke_all_sessions_for_user(session: AsyncSession, *, user_id: uuid.UUID, reason: str) -> None:
    """Used for 'log out everywhere' and forced-logout-on-role-change flows."""
    result = await session.execute(
        select(Session).where(Session.user_id == user_id, Session.revoked_at.is_(None))
    )
    now = datetime.now(timezone.utc)
    for s in result.scalars().all():
        s.revoked_at = now
        s.revoked_reason = reason
