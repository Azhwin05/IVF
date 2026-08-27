"""
FastAPI dependencies used across every module's router:
  - get_current_user: validates the access token, loads the user
  - require_permission("x.y"): the ONE mechanism every sensitive route
    uses to authorize an action — never a bare role-name check.

Per ARCHITECTURE.md §4 / spec §6: "Never trust frontend role checks
alone." Every route that mutates or reads sensitive data must depend
on require_permission(...), which re-derives the user's permission set
from the database on every request (not from the JWT payload, which
only carries the role code for convenience/logging — permissions are
looked up fresh so a permission revoked mid-session takes effect on
the very next request, not just the next login).
"""
from collections.abc import Callable
from datetime import datetime, timezone

import jwt
from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import AuthenticationError, PermissionDeniedError
from app.core.security import decode_access_token
from app.users.models import User


async def get_current_user(request: Request, session: AsyncSession = Depends(get_db)) -> User:
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise AuthenticationError("Missing or malformed Authorization header.")

    token = auth_header.removeprefix("Bearer ").strip()
    try:
        payload = decode_access_token(token)
    except jwt.ExpiredSignatureError:
        raise AuthenticationError("Access token expired.", error_code="token_expired")
    except jwt.PyJWTError:
        raise AuthenticationError("Invalid access token.")

    if payload.get("type") != "access":
        raise AuthenticationError("Wrong token type.")

    user_id = payload["sub"]
    user = await session.get(User, user_id)
    if not user or not user.is_active:
        raise AuthenticationError("User not found or deactivated.")

    request.state.current_user = user
    request.state.session_id = payload.get("sid")
    return user


def require_permission(permission_code: str) -> Callable:
    """Usage: `current_user: User = Depends(require_permission("billing.refund"))`"""

    async def checker(user: User = Depends(get_current_user)) -> User:
        codes = {p.code for p in user.role.permissions}
        if permission_code not in codes:
            raise PermissionDeniedError(
                f"Missing required permission: {permission_code}",
                error_code="permission_denied",
            )
        return user

    return checker


def require_any_permission(*permission_codes: str) -> Callable:
    async def checker(user: User = Depends(get_current_user)) -> User:
        codes = {p.code for p in user.role.permissions}
        if not codes.intersection(permission_codes):
            raise PermissionDeniedError(
                f"Missing one of required permissions: {', '.join(permission_codes)}",
                error_code="permission_denied",
            )
        return user

    return checker
