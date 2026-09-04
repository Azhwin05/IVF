"""Deterministic lab-report extraction.

Adapted from the research prototype's Approach A (PDF text / OCR → layout-aware
text → rule-based parsers → normalization → validation). The safety rule the
prototype was built around carries over unchanged: a field that cannot be read
confidently is left empty and flagged, never guessed.

The public entry point is :func:`extract_document`. AI-assisted extraction is a
seam only — :class:`AIExtractionProvider` in ``provider`` defines the plug point
and raises :class:`NotImplementedError` until a real provider is wired in.
"""

from app.laboratory.extraction.dto import ExtractedRow, ExtractionOutcome
from app.laboratory.extraction.extractor import extract_document
from app.laboratory.extraction.ocr import OcrUnavailable

__all__ = [
    "ExtractedRow",
    "ExtractionOutcome",
    "extract_document",
    "OcrUnavailable",
]
