import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.service import record_audit_event
from app.core.exceptions import ConflictError, NotFoundError
from app.core.security import hash_password, validate_password_strength
from app.users.models import User
from app.users.schemas import UserCreate, UserUpdate


async def get_user_by_id(session: AsyncSession, user_id: uuid.UUID) -> User:
    user = await session.get(User, user_id)
    if not user:
        raise NotFoundError("User not found", error_code="user_not_found")
    return user


async def get_user_by_email(session: AsyncSession, email: str) -> User | None:
    result = await session.execute(select(User).where(User.email == email.lower()))
    return result.scalar_one_or_none()


async def list_users(session: AsyncSession) -> list[User]:
    result = await session.execute(select(User).order_by(User.full_name))
    return list(result.scalars().all())


async def list_users_by_role_code(session: AsyncSession, role_code: str) -> list[User]:
    """Used for lightweight staff-picker UIs (e.g. the doctor list on the
    appointment book) that need names, not the full user-management view
    GET /users is gated behind — those callers only have appointments.read,
    not admin.manage_users."""
    from app.roles.models import Role

    result = await session.execute(
        select(User).join(Role).where(Role.code == role_code, User.is_active.is_(True)).order_by(User.full_name)
    )
    return list(result.scalars().all())


async def create_user(
    session: AsyncSession, data: UserCreate, *, actor_id: uuid.UUID, actor_role: str
) -> User:
    if await get_user_by_email(session, data.email):
        raise ConflictError("A user with this email already exists", error_code="email_taken")

    errors = validate_password_strength(data.temporary_password)
    if errors:
        raise ConflictError("; ".join(errors), error_code="weak_password")

    user = User(
        employee_code=data.employee_code,
        full_name=data.full_name,
        email=data.email.lower(),
        phone=data.phone,
        department=data.department,
        role_id=data.role_id,
        password_hash=hash_password(data.temporary_password),
        must_change_password=True,
    )
    session.add(user)
    await session.flush()

    await record_audit_event(
        session,
        actor_id=actor_id,
        actor_role=actor_role,
        action="user.created",
        entity_type="User",
        entity_id=str(user.id),
        after_state={"employee_code": user.employee_code, "email": user.email, "role_id": str(user.role_id)},
    )
    return user


async def update_user(
    session: AsyncSession, user_id: uuid.UUID, data: UserUpdate, *, actor_id: uuid.UUID, actor_role: str
) -> User:
    user = await get_user_by_id(session, user_id)
    before = {"full_name": user.full_name, "department": user.department, "is_active": user.is_active, "role_id": str(user.role_id)}

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(user, field, value)
    await session.flush()

    await record_audit_event(
        session,
        actor_id=actor_id,
        actor_role=actor_role,
        action="user.updated",
        entity_type="User",
        entity_id=str(user.id),
        before_state=before,
        after_state=data.model_dump(exclude_unset=True, mode="json"),
    )
    return user
