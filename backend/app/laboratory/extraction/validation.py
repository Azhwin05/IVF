"""Deterministic checks on extraction correctness — not medical interpretation.

A value is never flagged for being medically abnormal; only structural problems,
OCR artefacts and column-mapping mistakes are flagged. Validation identifies
problems and, where a field is clearly wrong, discards it (leaving it empty for
the reviewer) — it never invents corrections.
"""

import re

from app.laboratory.extraction.dto import ExtractedRow
from app.laboratory.models import ResultValidationStatus

# Column-length ceilings that mirror the LabResult model. A field longer than
# this is a parser error; it is dropped, never truncated into the database.
_MAX_LEN = {"test_name": 200, "value": 120, "unit": 60, "reference_range": 120}

# Plain / thousands-grouped / Indian lakh-grouped (2,12,000) numbers, optional
# comparator, optional trailing '%'.
_VALUE_NUMERIC = re.compile(r"^[<>]?=?\s*[+-]?\d[\d,]*(?:\.\d+)?\s*%?\s*[<>]?$")
_BARE_NUMBER = re.compile(r"^[+-]?\d[\d,]*(?:\.\d+)?$")
_GARBLED_NUMBER = re.compile(r"^\d[\d,]*\.\d+\.\d")  # e.g. "3.5.2." from a bad OCR
_LOOKS_LIKE_RANGE = re.compile(
    r"\d[\d.,]*\s*(?:[-–—]|to)\s*\d[\d.,]*|^\s*[<>]\s*=?\s*\d", re.I
)
# A lone letter where a digit belongs in a reference range — OCR reading 0 as
# "o"/"O", 1 as "l"/"I", 5 as "S". Flags e.g. "o-1" for review; never auto-fixed.
_RANGE_OCR_LETTER = re.compile(r"(?:^|[\s(<>\-–—])[OolIiSsZzBb](?=$|[\s)\-–—.0-9])")
_UNIT_OK = re.compile(r"^[A-Za-zµ%][A-Za-zµ%0-9/^().\-\s]{0,58}$")
_KNOWN_TEXTUAL_VALUES = {
    "non-reactive", "reactive", "negative", "positive", "nil", "trace", "absent",
    "present", "detected", "not detected", "normal", "abnormal",
    "o positive", "o negative", "a positive", "a negative",
    "b positive", "b negative", "ab positive", "ab negative",
}
_SUSPECT_OCR_CHARS = re.compile(r"[Il|][0-9]|[0-9][Il|]|O0|0O")


def _looks_like_test_name(name: str) -> bool:
    letters = sum(ch.isalpha() for ch in name)
    digits = sum(ch.isdigit() for ch in name)
    return letters >= 2 and letters >= digits


def validate_row(row: ExtractedRow) -> ExtractedRow:
    notes: list[str] = []

    # 1. hard length guard — drop, never truncate.
    for field, limit in _MAX_LEN.items():
        v = getattr(row, field)
        if v is not None and len(v) > limit:
            setattr(row, field, None)
            notes.append(
                f"Extracted {field.replace('_', ' ')} exceeded the storage limit "
                f"and was discarded — parser error."
            )

    # 2. test name must actually look like a test name.
    if not row.test_name or not row.test_name.strip():
        row.validation_status = ResultValidationStatus.not_extracted
        row.validation_notes = notes + ["Missing test name."]
        return row
    if not _looks_like_test_name(row.test_name):
        row.validation_notes = notes + [
            f"'{row.test_name}' does not look like a laboratory test name "
            "(likely a value shifted into the test column)."
        ]
        row.validation_status = ResultValidationStatus.not_extracted
        return row

    # 3. value must be present and plausible.
    if row.value is None or not str(row.value).strip():
        row.validation_status = ResultValidationStatus.not_extracted
        row.validation_notes = notes + ["Missing value — please enter manually."]
        return row

    value_str = str(row.value).strip()
    is_numeric = bool(_VALUE_NUMERIC.match(value_str))
    is_known_textual = value_str.lower() in _KNOWN_TEXTUAL_VALUES

    if not is_numeric and not is_known_textual:
        if _LOOKS_LIKE_RANGE.search(value_str):
            notes.append(
                f"Value '{value_str}' looks like a reference range — the columns "
                "may be shifted; verify against the source."
            )
        else:
            notes.append(
                f"Value '{value_str}' is neither numeric nor a recognised "
                "qualitative result — verify against the source."
            )

    # 4. unit sanity.
    if row.unit:
        unit_str = row.unit.strip()
        if _BARE_NUMBER.match(unit_str) or _VALUE_NUMERIC.match(unit_str):
            notes.append(
                f"Unit '{unit_str}' looks like a number — the value/unit columns "
                "may be shifted."
            )
        elif not _UNIT_OK.match(unit_str):
            notes.append(f"Unit '{unit_str}' does not look like a measurement unit.")
    elif is_numeric:
        notes.append("Numeric value captured with no unit.")

    # 5. reference range sanity.
    if row.reference_range:
        ref_str = row.reference_range.strip()
        if _BARE_NUMBER.match(ref_str):
            notes.append(
                f"Reference range '{ref_str}' is a single number, not a range — "
                "half of it may have been lost."
            )
        elif _GARBLED_NUMBER.match(ref_str) or ref_str.count(".") >= 3:
            notes.append(
                f"Reference range '{ref_str}' looks garbled — verify against the source."
            )
        elif _RANGE_OCR_LETTER.search(ref_str):
            notes.append(
                f"Reference range '{ref_str}' has a letter where a digit is expected "
                "(O/0, l/1, S/5) — verify against the source."
            )
    else:
        notes.append(
            "No reference range captured (may be genuinely absent, or a parsing miss)."
        )

    # 6. OCR-confusable characters in the value.
    if _SUSPECT_OCR_CHARS.search(value_str):
        notes.append(
            "Value contains a character pattern OCR often confuses (O/0, I/1); "
            "verify against the source image."
        )

    row.validation_notes = notes
    row.validation_status = (
        ResultValidationStatus.ok if not notes else ResultValidationStatus.needs_review
    )
    return row
