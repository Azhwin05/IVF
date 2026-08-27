"""
Embryo grading and development tracking, from the frontend's Embryo
shape (Gardner grading: expansion/ICM/trophectoderm, quality score).
"""
import enum
import uuid
from datetime import date

from sqlalchemy import Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import TimestampMixin, UUIDPrimaryKeyMixin
from app.core.database import Base


class EmbryoStatus(str, enum.Enum):
    UNDER_REVIEW = "under_clinical_review"
    SELECTED_FOR_TRANSFER = "selected_for_transfer"
    CRYOPRESERVED = "cryopreserved"
    NOT_SUITABLE = "not_suitable_for_transfer"
    TRANSFERRED = "transferred"
    DISCARDED = "discarded"


class Embryo(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "embryos"

    cycle_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("ivf_cycles.id"), nullable=False, index=True)
    label: Mapped[str] = mapped_column(String(16), nullable=False)  # "E-01"

    day: Mapped[int] = mapped_column(Integer, nullable=False)
    grade: Mapped[str] = mapped_column(String(8), nullable=False)  # "4AA"
    expansion: Mapped[str | None] = mapped_column(String(64), nullable=True)
    icm_grade: Mapped[str | None] = mapped_column(String(64), nullable=True)
    trophectoderm_grade: Mapped[str | None] = mapped_column(String(64), nullable=True)
    quality_score: Mapped[int | None] = mapped_column(Integer, nullable=True)

    status: Mapped[EmbryoStatus] = mapped_column(Enum(EmbryoStatus), default=EmbryoStatus.UNDER_REVIEW, index=True)
    embryologist_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    graded_by_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)


class OocyteAssessment(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Retrieval-day summary — oocytes retrieved, mature, fertilised, from
    the frontend's EMBRYO_SUMMARY funnel."""
    __tablename__ = "oocyte_assessments"

    cycle_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("ivf_cycles.id"), nullable=False, unique=True, index=True)
    retrieval_date: Mapped[date] = mapped_column(nullable=False)
    oocytes_retrieved: Mapped[int] = mapped_column(Integer, default=0)
    mature_oocytes: Mapped[int] = mapped_column(Integer, default=0)
    normally_fertilised: Mapped[int] = mapped_column(Integer, default=0)
    fertilisation_method: Mapped[str] = mapped_column(String(16), default="ICSI")
