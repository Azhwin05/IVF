import uuid
from datetime import date

from pydantic import BaseModel, ConfigDict

from app.hr.models import LeaveStatus


class EmployeeCreate(BaseModel):
    user_id: uuid.UUID | None = None
    full_name: str
    department: str
    designation: str
    phone: str | None = None
    joined_date: date
    reporting_manager_id: uuid.UUID | None = None


class EmployeeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    full_name: str
    department: str
    designation: str
    phone: str | None
    joined_date: date
    leave_balance_days: int


class LeaveRequestCreate(BaseModel):
    employee_id: uuid.UUID
    leave_type: str
    from_date: date
    to_date: date


class LeaveRequestOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    employee_id: uuid.UUID
    leave_type: str
    from_date: date
    to_date: date
    status: LeaveStatus
