import uuid

from pydantic import BaseModel, ConfigDict, EmailStr


class UserSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    employee_code: str
    full_name: str
    email: EmailStr
    department: str | None
    is_active: bool
    role_code: str


class UserCreate(BaseModel):
    employee_code: str
    full_name: str
    email: EmailStr
    phone: str | None = None
    department: str | None = None
    role_id: uuid.UUID
    temporary_password: str


class UserUpdate(BaseModel):
    full_name: str | None = None
    phone: str | None = None
    department: str | None = None
    role_id: uuid.UUID | None = None
    is_active: bool | None = None
