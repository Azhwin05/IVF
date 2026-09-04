"""Plain data carried between extraction stages.

These are not persisted. The service layer maps :class:`ExtractedRow` onto
``LabResult`` rows, copying the four extracted fields into the immutable
``extracted_*`` snapshot at the same time.
"""

from dataclasses import dataclass, field

from app.laboratory.models import (
    DocumentKind,
    ExtractionMethod,
    NormalizationMatch,
    ResultValidationStatus,
)


@dataclass
class ExtractedRow:
    """One candidate result parsed from the document."""

    test_name: str | None = None
    value: str | None = None
    unit: str | None = None
    reference_range: str | None = None

    source_snippet: str | None = None
    source_location: str | None = None

    normalization_match: NormalizationMatch = NormalizationMatch.unmatched
    normalization_note: str | None = None

    validation_status: ResultValidationStatus = ResultValidationStatus.needs_review
    validation_notes: list[str] = field(default_factory=list)

    confidence: float | None = None


@dataclass
class ExtractionOutcome:
    """The result of running the pipeline over one uploaded document."""

    document_kind: DocumentKind
    method: ExtractionMethod
    page_count: int | None = None
    rows: list[ExtractedRow] = field(default_factory=list)
    # Set only when extraction could not run at all (e.g. unreadable file, OCR
    # required but unavailable). A populated ``error`` means ``rows`` is empty.
    error: str | None = None
