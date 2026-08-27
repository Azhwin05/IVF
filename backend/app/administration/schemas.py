import uuid

from pydantic import BaseModel, ConfigDict


class ProcedureChargeCreate(BaseModel):
    service_code: str
    procedure_name: str
    charge_paise: int


class ProcedureChargeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    service_code: str
    procedure_name: str
    charge_paise: int
    is_active: bool


class PackageCreate(BaseModel):
    name: str
    price_paise: int
    validity_description: str | None = None


class PackageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    name: str
    price_paise: int
    validity_description: str | None
    is_active: bool


class LabTestCreate(BaseModel):
    test_name: str
    price_paise: int
    turnaround_time: str
    sample_type: str | None = None
