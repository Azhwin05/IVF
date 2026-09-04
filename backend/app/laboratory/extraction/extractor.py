"""Orchestrates one extraction run: bytes in, :class:`ExtractionOutcome` out.

Flow:

    uploaded bytes
        -> detect digital PDF vs scanned PDF vs image
        -> collect positioned words per page
             digital PDF : pdfplumber.extract_words
             scanned/image: OCR (guarded) -> ocr_word_rows
        -> geometry-aware column table  (table.extract_rows_from_word_rows)
             ... or, when the page is not a column table,
           rule-based line parsers      (parsers.parse_lines on flattened text)
        -> test-name normalization      (exact alias only)
        -> deterministic validation     (structural checks, never medical)
        -> ExtractedRow list

Nothing here writes to the database. A field that could not be read stays
``None`` and its row is flagged; a document that could not be processed at all
comes back with ``error`` set and ``rows`` empty.
"""

from __future__ import annotations

import io
import logging
from collections.abc import Sequence

from app.core.config import Settings
from app.laboratory.extraction import table
from app.laboratory.extraction.dto import ExtractedRow, ExtractionOutcome
from app.laboratory.extraction.layout import Word, render_line
from app.laboratory.extraction.normalization import (
    normalize_test_name,
    suggest_candidates,
)
from app.laboratory.extraction.ocr import OcrUnavailable, ocr_word_rows
from app.laboratory.extraction.parsers import parse_lines
from app.laboratory.extraction.provider import get_ai_provider
from app.laboratory.extraction.validation import validate_row
from app.laboratory.models import DocumentKind, ExtractionMethod, NormalizationMatch

logger = logging.getLogger(__name__)

# Below this many characters of embedded text on a page, treat it as scanned and
# send it to OCR.
_DIGITAL_TEXT_MIN_CHARS = 40

_PDF_TYPES = {"application/pdf", "application/x-pdf"}
_IMAGE_TYPES = {"image/png", "image/jpeg", "image/jpg", "image/tiff", "image/bmp"}


def _is_pdf(filename: str, content_type: str) -> bool:
    return content_type.lower() in _PDF_TYPES or filename.lower().endswith(".pdf")


def _is_image(filename: str, content_type: str) -> bool:
    if content_type.lower() in _IMAGE_TYPES:
        return True
    return filename.lower().endswith((".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp"))


# --------------------------------------------------------------------------- #
# words -> rows
# --------------------------------------------------------------------------- #

def _pdf_page_word_rows(page) -> list[list[Word]]:
    """Group a digital PDF page's words into rows by vertical position."""
    words = page.extract_words(x_tolerance=1, y_tolerance=3, keep_blank_chars=False)
    boxes: list[Word] = [
        {
            "text": w["text"],
            "x0": float(w["x0"]),
            "x1": float(w["x1"]),
            "top": float(w["top"]),
        }
        for w in words
    ]
    boxes.sort(key=lambda w: (round(w["top"] / 3), w["x0"]))
    rows: list[list[Word]] = []
    cur_bucket: int | None = None
    cur: list[Word] = []
    for w in boxes:
        bucket = round(w["top"] / 3)
        if cur_bucket is None or bucket == cur_bucket:
            cur.append(w)
        else:
            rows.append(sorted(cur, key=lambda x: x["x0"]))
            cur = [w]
        cur_bucket = bucket
    if cur:
        rows.append(sorted(cur, key=lambda x: x["x0"]))
    return rows


def _page_rows(word_rows: Sequence[Sequence[Word]], source_label: str) -> list[ExtractedRow]:
    """Geometry-aware table first; fall back to the line parsers on the
    flattened text for narrative / non-tabular layouts."""
    if word_rows:
        from_table = table.extract_rows_from_word_rows(word_rows, source_label)
        if from_table is not None:
            return from_table
    flat = "\n".join(render_line(list(r)) for r in word_rows)
    return parse_lines(flat.splitlines(), source_label)


def _finalize(rows: list[ExtractedRow]) -> list[ExtractedRow]:
    _normalize(rows)
    for row in rows:
        validate_row(row)
    return rows


# --------------------------------------------------------------------------- #
# per-document
# --------------------------------------------------------------------------- #

def _extract_pdf(data: bytes) -> ExtractionOutcome:
    import pdfplumber

    pages: list[tuple[int, list[list[Word]]]] = []
    needs_ocr: list[int] = []

    with pdfplumber.open(io.BytesIO(data)) as pdf:
        page_count = len(pdf.pages)
        for i, page in enumerate(pdf.pages):
            plain = page.extract_text() or ""
            if len(plain.strip()) >= _DIGITAL_TEXT_MIN_CHARS:
                pages.append((i, _pdf_page_word_rows(page)))
            else:
                needs_ocr.append(i)

        if needs_ocr:
            try:
                for i in needs_ocr:
                    image = pdf.pages[i].to_image(resolution=200).original
                    pages.append((i, ocr_word_rows(image)))
            except OcrUnavailable as exc:
                return ExtractionOutcome(
                    document_kind=DocumentKind.scanned_pdf,
                    method=ExtractionMethod.ocr,
                    page_count=page_count,
                    rows=[],
                    error=str(exc),
                )
            kind = DocumentKind.scanned_pdf
            method = ExtractionMethod.ocr
        else:
            kind = DocumentKind.digital_pdf
            method = ExtractionMethod.native_pdf_text

    pages.sort(key=lambda t: t[0])
    rows: list[ExtractedRow] = []
    for page_no, word_rows in pages:
        rows.extend(_page_rows(word_rows, f"page {page_no + 1}"))
    return ExtractionOutcome(
        document_kind=kind, method=method, page_count=page_count, rows=_finalize(rows)
    )


def _extract_image(data: bytes) -> ExtractionOutcome:
    from PIL import Image

    try:
        image = Image.open(io.BytesIO(data))
        word_rows = ocr_word_rows(image)
    except OcrUnavailable as exc:
        return ExtractionOutcome(
            document_kind=DocumentKind.image,
            method=ExtractionMethod.ocr,
            page_count=1,
            rows=[],
            error=str(exc),
        )
    rows = _finalize(_page_rows(word_rows, "page 1"))
    return ExtractionOutcome(
        document_kind=DocumentKind.image,
        method=ExtractionMethod.ocr,
        page_count=1,
        rows=rows,
    )


def _normalize(rows: list[ExtractedRow]) -> None:
    for row in rows:
        if not row.test_name:
            continue
        canonical, _match = normalize_test_name(row.test_name)
        if canonical:
            if canonical != row.test_name:
                row.normalization_note = f"Normalised from '{row.test_name}'."
            row.test_name = canonical
            row.normalization_match = NormalizationMatch.exact_alias
        else:
            row.normalization_match = NormalizationMatch.unmatched
            candidates = suggest_candidates(row.test_name)
            if candidates:
                row.normalization_note = (
                    "No exact match. Possible tests for review: "
                    + ", ".join(candidates)
                )


def extract_document(
    data: bytes,
    *,
    filename: str,
    content_type: str,
    settings: Settings,
) -> ExtractionOutcome:
    """Run the pipeline. Never raises for bad input — returns an outcome whose
    ``error`` is set and ``rows`` is empty instead.
    """
    # The AI seam is consulted here only so a future provider has a call site.
    # It is always ``None`` today (deterministic-only).
    _ai_provider = get_ai_provider(settings)

    try:
        if _is_pdf(filename, content_type):
            return _extract_pdf(data)
        if _is_image(filename, content_type):
            return _extract_image(data)
    except OcrUnavailable as exc:
        return ExtractionOutcome(
            document_kind=DocumentKind.unknown,
            method=ExtractionMethod.none,
            page_count=None,
            rows=[],
            error=str(exc),
        )
    except Exception:  # noqa: BLE001 - a corrupt upload must not 500 the request
        logger.exception("Lab extraction failed for %s", filename)
        return ExtractionOutcome(
            document_kind=DocumentKind.unknown,
            method=ExtractionMethod.none,
            page_count=None,
            rows=[],
            error="The document could not be read. Upload a clearer copy or enter results manually.",
        )

    return ExtractionOutcome(
        document_kind=DocumentKind.unknown,
        method=ExtractionMethod.none,
        page_count=None,
        rows=[],
        error=f"Unsupported file type: {content_type or filename}.",
    )
