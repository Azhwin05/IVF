import uuid

from pydantic import BaseModel, ConfigDict


class PermissionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    code: str
    module: str
    description: str | None
    is_critical: bool


class RoleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    code: str
    name: str
    description: str | None
    is_system_role: bool
    permissions: list[PermissionOut]


class RolePermissionsUpdate(BaseModel):
    permission_ids: list[uuid.UUID]
