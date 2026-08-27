"""
Password hashing (Argon2id) and JWT access/refresh token issuance.

Security rules enforced here (per ARCHITECTURE.md / docs/security):
  - Argon2id only, never plaintext, never logged
  - Short-lived access tokens (15 min default)
  - Refresh tokens are opaque random strings, stored hashed in the DB,
    with reuse detection (a used-and-reused refresh token revokes the
    entire session chain — see app/auth/service.py)
  - Absolute session lifetime and idle timeout enforced independently
    of token expiry
"""
import secrets
import uuid
from datetime import datetime, timedelta, timezone

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from app.core.config import get_settings

settings = get_settings()

_hasher = PasswordHasher(
    time_cost=3,
    memory_cost=65536,  # 64 MB
    parallelism=4,
)


def hash_password(plain: str) -> str:
    return _hasher.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return _hasher.verify(hashed, plain)
    except VerifyMismatchError:
        return False


def password_needs_rehash(hashed: str) -> bool:
    return _hasher.check_needs_rehash(hashed)


def validate_password_strength(plain: str) -> list[str]:
    """Returns a list of violated rules; empty list = acceptable."""
    errors = []
    if len(plain) < settings.PASSWORD_MIN_LENGTH:
        errors.append(f"Password must be at least {settings.PASSWORD_MIN_LENGTH} characters.")
    if not any(c.isupper() for c in plain):
        errors.append("Password must contain an uppercase letter.")
    if not any(c.islower() for c in plain):
        errors.append("Password must contain a lowercase letter.")
    if not any(c.isdigit() for c in plain):
        errors.append("Password must contain a digit.")
    return errors


def create_access_token(*, user_id: uuid.UUID, role: str, session_id: uuid.UUID) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "role": role,
        "sid": str(session_id),
        "type": "access",
        "iat": now,
        "exp": now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    """Raises jwt.PyJWTError on invalid/expired tokens — caller handles as 401."""
    return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])


def generate_refresh_token() -> str:
    """Opaque, high-entropy token — never a JWT. Stored hashed, never logged."""
    return secrets.token_urlsafe(48)


def hash_refresh_token(token: str) -> str:
    """Refresh tokens are hashed at rest (SHA-256 is fine here — this is a lookup hash,
    not a password hash; the token itself already has 384 bits of entropy)."""
    import hashlib
    return hashlib.sha256(token.encode()).hexdigest()
