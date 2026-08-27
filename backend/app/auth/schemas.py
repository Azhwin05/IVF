import uuid

from pydantic import BaseModel


class LoginRequest(BaseModel):
    email: str
    password: str
    device_label: str | None = None


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in_seconds: int


class RefreshRequest(BaseModel):
    refresh_token: str


class SessionInfo(BaseModel):
    id: uuid.UUID
    device_label: str | None
    ip_address: str | None
    last_active_at: str
    is_current: bool


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str
