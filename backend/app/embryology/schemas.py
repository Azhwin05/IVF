import uuid
from datetime import date

from pydantic import BaseModel, ConfigDict

from app.embryology.models import EmbryoStatus


class OocyteAssessmentCreate(BaseModel):
    cycle_id: uuid.UUID
    retrieval_date: date
    oocytes_retrieved: int
    mature_oocytes: int
    normally_fertilised: int
    fertilisation_method: str = "ICSI"


class OocyteAssessmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    cycle_id: uuid.UUID
    retrieval_date: date
    oocytes_retrieved: int
    mature_oocytes: int
    normally_fertilised: int


class EmbryoCreate(BaseModel):
    cycle_id: uuid.UUID
    label: str
    day: int
    grade: str
    expansion: str | None = None
    icm_grade: str | None = None
    trophectoderm_grade: str | None = None
    quality_score: int | None = None
    embryologist_notes: str | None = None


class EmbryoStatusUpdate(BaseModel):
    status: EmbryoStatus
    notes: str | None = None


class EmbryoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    cycle_id: uuid.UUID
    label: str
    day: int
    grade: str
    expansion: str | None
    icm_grade: str | None
    trophectoderm_grade: str | None
    quality_score: int | None
    status: EmbryoStatus
    embryologist_notes: str | None
