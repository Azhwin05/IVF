"""Request/response shapes for outside-lab report ingestion.

Responses are declared explicitly; ORM objects are never returned directly. A
field that extraction could not read is ``null`` here - the API never invents a
value, a unit or a reference range.
"""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.types import UtcDatetime
from app.laboratory.models import (
    CorrectionField,
    DocumentKind,
    EntryOrigin,
    ExtractionMethod,
    ExtractionStatus,
    NormalizationMatch,
    ResultValidationStatus,
)


def _blank_to_none(value: object) -> object:
    if isinstance(value, str):
        return value.strip() or None
    return value


class LabReportPatientRef(BaseModel):
    """The minimum a report list/detail needs to name its patient. Deliberately
    not the full PatientSummary - report ingestion stays decoupled from the
    patients module's response shape."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    uhid: str
    full_name: str


class LabReportResultRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    report_id: UUID

    test_name: str | None
    value: str | None
    unit: str | None
    reference_range: str | None

    # Exactly what extraction produced. Null on every field for a hand-added row.
    extracted_test_name: str | None
    extracted_value: str | None
    extracted_unit: str | None
    extracted_reference_range: str | None

    entry_origin: EntryOrigin
    normalization_match: NormalizationMatch
    normalization_note: str | None
    validation_status: ResultValidationStatus
    validation_notes: list[str]
    source_snippet: str | None
    source_location: str | None
    confidence: float | None

    created_at: UtcDatetime
    updated_at: UtcDatetime


class LabReportSummary(BaseModel):
    """A report without its results - used in list responses."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    patient: LabReportPatientRef
    original_filename: str
    content_type: str
    byte_size: int
    document_kind: DocumentKind
    extraction_status: ExtractionStatus
    extraction_method: ExtractionMethod
    extraction_error: str | None
    page_count: int | None
    extracted_at: UtcDatetime | None
    created_at: UtcDatetime


class LabReportDetail(LabReportSummary):
    """A report and every result parsed from or added to it."""

    results: list[LabReportResultRead]


class LabReportPage(BaseModel):
    items: list[LabReportSummary]
    next_cursor: str | None = None
    has_more: bool = False


class LabReportResultManualCreate(BaseModel):
    """A result row a person adds by hand for a report."""

    test_name: str = Field(min_length=1, max_length=200)
    value: str | None = Field(default=None, max_length=120)
    unit: str | None = Field(default=None, max_length=60)
    reference_range: str | None = Field(default=None, max_length=120)

    _strip = field_validator(
        "test_name", "value", "unit", "reference_range", mode="before"
    )(_blank_to_none)

    @field_validator("test_name")
    @classmethod
    def _test_name_required(cls, value: str | None) -> str:
        if not value:
            raise ValueError("Enter the test name.")
        return value


class LabReportResultCorrectionRequest(BaseModel):
    """A correction to one or more fields of an extracted or manual result.

    Only the fields present in the payload are changed. Sending a field with an
    explicit ``null`` clears it. Each changed field is recorded in the result's
    correction history with the value it replaced.
    """

    model_config = ConfigDict(extra="forbid")

    test_name: str | None = Field(default=None, max_length=200)
    value: str | None = Field(default=None, max_length=120)
    unit: str | None = Field(default=None, max_length=60)
    reference_range: str | None = Field(default=None, max_length=120)
    reason: str | None = Field(default=None, max_length=300)

    _strip = field_validator(
        "test_name", "value", "unit", "reference_range", "reason", mode="before"
    )(_blank_to_none)


class LabReportResultCorrectionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    result_id: UUID
    field: CorrectionField
    previous_value: str | None
    new_value: str | None
    corrected_by_id: UUID
    reason: str | None
    created_at: UtcDatetime
