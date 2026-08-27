from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.service import record_audit_event
from app.core.database import get_db
from app.core.deps import require_permission
from app.core.exceptions import NotFoundError
from app.roles.models import Permission, Role
from app.roles.schemas import PermissionOut, RoleOut, RolePermissionsUpdate
from app.users.models import User

router = APIRouter(prefix="/roles", tags=["roles"])


@router.get("", response_model=list[RoleOut])
async def list_roles(
    session: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("admin.manage_roles")),
) -> list[RoleOut]:
    result = await session.execute(select(Role).order_by(Role.name))
    return list(result.scalars().all())


@router.get("/permissions", response_model=list[PermissionOut])
async def list_permissions(
    session: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("admin.manage_roles")),
) -> list[PermissionOut]:
    result = await session.execute(select(Permission).order_by(Permission.module, Permission.code))
    return list(result.scalars().all())


@router.put("/{role_id}/permissions", response_model=RoleOut)
async def set_role_permissions(
    role_id: str,
    body: RolePermissionsUpdate,
    session: AsyncSession = Depends(get_db),
    current: User = Depends(require_permission("admin.manage_roles")),
) -> RoleOut:
    role = await session.get(Role, role_id)
    if not role:
        raise NotFoundError("Role not found")
    if role.is_system_role and role.code == "administrator":
        raise NotFoundError("Cannot modify the Administrator role's permission set.", error_code="protected_role")

    before = sorted(p.code for p in role.permissions)
    result = await session.execute(select(Permission).where(Permission.id.in_(body.permission_ids)))
    role.permissions = list(result.scalars().all())
    await session.flush()

    await record_audit_event(
        session, actor_id=current.id, actor_role=current.role.code,
        action="role.permissions_updated", entity_type="Role", entity_id=str(role.id),
        before_state={"permissions": before},
        after_state={"permissions": sorted(p.code for p in role.permissions)},
    )
    return role
