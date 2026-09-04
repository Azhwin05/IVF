"""Geometry-aware table extraction from positioned words.

The line parsers in :mod:`app.laboratory.extraction.parsers` rebuild columns from
runs of spaces in already-flattened text. That is unreliable on real reports:
OCR renders vertical table rules as stray ``|`` tokens, splits reference ranges
like ``70 - 100`` across cells, and uses inconsistent gap widths.

This module works from the word bounding boxes instead — available from
Tesseract's ``image_to_data`` and pdfplumber's ``extract_words``. It finds the
column *bands* from where words actually sit on the page, assigns each word to a
band, then decides which band is the test name / value / unit / reference range
from the header row or from cell content — never from fixed character positions.

It is deterministic. :func:`extract_rows_from_word_rows` returns ``None`` when the
page does not look like a column table, so the caller falls back to the line
parsers for narrative / single-column / colon-inline / dotted-leader layouts.
"""

from __future__ import annotations

import re
import statistics
from collections.abc import Sequence

from app.laboratory.extraction.dto import ExtractedRow
from app.laboratory.extraction.layout import Word

# --------------------------------------------------------------------------- #
# lexicons / patterns
# --------------------------------------------------------------------------- #

# Exact (alpha-only) header words. Kept tight on purpose: a loose substring match
# turned "TEST-PATIENT-001" into a "test" header and "Patient:" into a "value"
# header, so the wrong row anchored the columns.
_HEADER_KEYWORDS: dict[str, tuple[str, ...]] = {
    "test_name": ("test", "tests", "investigation", "investigations", "parameter",
                  "parameters", "analyte", "analytes"),
    "value": ("result", "results", "value", "values", "observed", "observation",
              "reading", "readings", "finding", "findings"),
    "unit": ("unit", "units"),
    "reference_range": ("reference", "range", "ranges", "interval", "intervals",
                        "normal", "biological", "expected"),
}

# Single-character tokens OCR emits when it reads a vertical rule. Real content is
# wider than a couple of pixels.
_RULE_CHARS = {"|", "!", "I", "l", "[", "]", "{", "}", ";", ":", "/", "\\", "."}
_RULE_MAX_WIDTH = 4.0

# Accepts plain, thousands-grouped and Indian lakh-grouped numbers (2,12,000).
_NUMERIC_CELL = re.compile(r"^[<>]?\s*[+-]?\d[\d,]*(?:\.\d+)?\s*[<>]?$")
_NON_UNIT_TOKEN = re.compile(r"^\d|[|!]")
_RANGE_CELL = re.compile(
    r"\d[\d.,]*\s*[-–—]\s*\d[\d.,]*"          # 12-16 , 4,000 - 11,000 , 70 - 100
    r"|^\s*[<>]\s*=?\s*\d"                    # < 200 , >40
    r"|\d[\d.,]*\s+to\s+\d",                  # 12 to 16
    re.I,
)
_UNIT_SHAPE = re.compile(r"^[A-Za-zµ%][A-Za-zµ%0-9/^.()\-]{0,14}$")
_UNIT_LEXICON = {
    "%", "g/dl", "g/l", "mg/dl", "mg/l", "u/l", "iu/l", "miu/ml", "µiu/ml", "uiu/ml",
    "ng/ml", "pg/ml", "ug/ml", "pmol/l", "nmol/l", "umol/l", "mmol/l", "meq/l",
    "cells/ul", "cells/cumm", "cells/cmm", "mill/cmm", "million/cmm", "lakhs/cmm",
    "10^3/ul", "10^6/ul", "fl", "pg", "sec", "secs", "mm/hr", "mm/br", "ratio",
    "index", "copies/ml", "u/ml", "iu/ml", "ku/l", "mg/24hr", "years", "yrs",
}

# Canonical spelling for a unit, keyed by its lowercased ascii form (µ -> u,
# spaces removed, a trailing '.' stripped). Repairs OCR case damage
# ("g/dl" -> "g/dL"), and the short truncations OCR makes in a narrow UNIT
# column ("g/d" -> "g/dL", "mg/d" -> "mg/dL"). It never turns a non-unit into a
# unit — an unrecognised token comes back only trimmed, unchanged. Plain ascii
# "u" (not "µ") is kept, matching the rest of the project's unit strings.
_UNIT_CANON: dict[str, str] = {
    "%": "%",
    "g/dl": "g/dL", "g/d": "g/dL", "gm/dl": "g/dL", "gdl": "g/dL", "g/l": "g/L",
    "mg/dl": "mg/dL", "mg/d": "mg/dL", "mgdl": "mg/dL", "mg/l": "mg/L",
    "ug/dl": "ug/dL", "ng/dl": "ng/dL",
    "u/l": "U/L", "iu/l": "IU/L", "ku/l": "kU/L",
    "u/ml": "U/mL", "iu/ml": "IU/mL", "miu/ml": "mIU/mL", "uiu/ml": "uIU/mL",
    "ng/ml": "ng/mL", "pg/ml": "pg/mL", "ug/ml": "ug/mL",
    "pmol/l": "pmol/L", "nmol/l": "nmol/L", "umol/l": "umol/L",
    "mmol/l": "mmol/L", "meq/l": "mEq/L",
    "mm/hr": "mm/hr", "mm/br": "mm/hr",
    "cells/ul": "cells/uL", "cells/cumm": "cells/cumm", "cells/cmm": "cells/cmm",
    "mill/cmm": "mill/cmm", "million/cmm": "million/cmm", "mill/ml": "mill/mL",
    "10^3/ul": "10^3/uL", "10^6/ul": "10^6/uL",
    "fl": "fL", "pg": "pg", "sec": "sec", "secs": "sec", "ml": "mL",
    "ratio": "ratio", "index": "index", "copies/ml": "copies/mL",
    "years": "years", "yrs": "years",
}


def _unit_key(token: str) -> str:
    return (token or "").strip().rstrip(".").strip().lower().replace(
        "µ", "u"
    ).replace("μ", "u").replace(" ", "")


def _canon_unit(raw: str) -> str:
    """Canonical spelling for a unit OCR read; unknown tokens are only trimmed."""
    cleaned = (raw or "").strip().rstrip(".").strip()
    return _UNIT_CANON.get(_unit_key(cleaned), cleaned)


def _looks_like_unit(token: str) -> bool:
    t = (token or "").strip().rstrip(".")
    if not t:
        return False
    key = _unit_key(t)
    if key in _UNIT_CANON or key in _UNIT_LEXICON or t == "%":
        return True
    # Generic measurement-unit shape ("cells/cumm", a new "mIU/mL" variant):
    # letters with a "/" or "%", never starting with a digit.
    return (
        bool(_UNIT_SHAPE.match(t))
        and any(ch in t for ch in "%/")
        and not t[:1].isdigit()
    )


def _split_value_unit(value: str) -> tuple[str, str | None]:
    """Separate a value cell OCR glued together as '<number> <unit>' because the
    report's UNIT column was missing or its header unreadable. Splits only when
    the trailing token is a recognised unit and the leading token is numeric —
    a reference range, a comparator value ('< 200') or a plain number is left
    untouched."""
    parts = value.strip().rsplit(None, 1)
    if len(parts) != 2:
        return value, None
    head, tail = parts
    if _NUMERIC_CELL.match(head) and _looks_like_unit(tail):
        return head, _canon_unit(tail)
    return value, None


_QUALITATIVE = {
    "non-reactive", "reactive", "negative", "positive", "nil", "trace", "absent",
    "present", "detected", "not detected", "normal", "abnormal", "clear", "hazy",
    "o positive", "o negative", "a positive", "a negative", "b positive",
    "b negative", "ab positive", "ab negative",
}
_SECTION_RE = re.compile(
    r"^(h[ae]?matolog(y|ical)|biochemistr(y|ical)|serolog(y|ical)|clinical\s+chemistry"
    r"|liver\s+function(\s+tests?)?|renal\s+function(\s+tests?)?|kidney\s+function"
    r"|lipid\s+(profile|panel)|thyroid\s+(profile|panel|function)|urine\s+(examination|analysis|routine)"
    r"|complete\s+blood\s+count|cbc|differential\s+(leu[ck]ocyte\s+count|count|leu[ck]ocytes?)"
    r"|electrolytes|coagulation(\s+profile)?|immunology|endocrinolog(y|ical)|hormones?"
    r"|blood\s+sugar|glucose\s+studies|iron\s+studies)\s*[:.-]?\s*$",
    re.I,
)
_BULLET = re.compile(r"^\s*[-–—•·*.•]+\s*")
_FOOTER_RE = re.compile(
    r"end\s+of\s+report|verified\s+by|authoris|authoriz|electronically\s+signed"
    r"|not\s+accredited|conditions?\s+of\s+report|computer[- ]generated"
    r"|results?\s+are\s+related\s+to\s+the\s+specimen|reg\.?\s*no|specimen\s+received"
    r"|\bnote\s*[:]|\bpathologist\b|\bmd\s*\(",
    re.I,
)


# --------------------------------------------------------------------------- #
# public entry point
# --------------------------------------------------------------------------- #

def extract_rows_from_word_rows(
    word_rows: Sequence[Sequence[Word]], source_label: str
) -> list[ExtractedRow] | None:
    """Return one :class:`ExtractedRow` per data row, or ``None`` if the page
    does not read as a column table (let the caller fall back)."""
    rows = [_clean_row(list(r)) for r in word_rows]
    rows = [r for r in rows if r]
    if len(rows) < 3:
        return None

    header_idx, header_map = _find_header(rows)
    if header_map is not None:
        bands, fields = _bands_from_header(rows[header_idx], header_map)
        data_rows = rows[header_idx + 1:]
    else:
        result = _bands_from_content(rows)
        if result is None:
            return None
        bands, fields = result
        data_rows = rows

    if "test_name" not in fields or "value" not in fields:
        return None
    if len(bands) < 2:
        return None

    extracted: list[ExtractedRow] = []
    pending_name_prefix: str | None = None
    for raw_row in data_rows:
        if _FOOTER_RE.search(_row_text(raw_row)):
            break  # everything past the report footer is boilerplate
        cells = _row_to_cells(raw_row, bands, fields)
        name = (cells.get("test_name") or "").strip()
        if name and _NUMERIC_CELL.match(name):
            # A bare number in the name band is a shifted value, never a test
            # name. Drop it so the row is flagged, not mislabelled.
            name = ""
        value = (cells.get("value") or "").strip()
        unit = (cells.get("unit") or "").strip()
        ref = (cells.get("reference_range") or "").strip()
        raw_cells = (name, value, unit, ref)  # exactly as the bands read them

        # Recover a unit OCR glued onto the value because the UNIT column was
        # missing or its header unreadable ("13.8 g/dL" -> value "13.8" + unit
        # "g/dL"). Deterministic reshaping of what OCR already read; the glued
        # form stays visible in source_snippet.
        if value and not unit:
            value, split_unit = _split_value_unit(value)
            if split_unit:
                unit = split_unit
        if unit:
            unit = _canon_unit(unit)

        has_data = bool(value or unit or ref)
        if not name and not has_data:
            continue
        # No name and no usable value: not a result row, just noise.
        if not name and not (
            _NUMERIC_CELL.match(value) or value.lower() in _QUALITATIVE
        ):
            continue

        if name and not has_data:
            # A row with only the name column filled: a section heading, or the
            # first line of a wrapped test name.
            if _is_section_heading(name):
                pending_name_prefix = None
                continue
            pending_name_prefix = name
            continue

        if pending_name_prefix:
            if name.startswith("(") or not name or name[:1].islower():
                name = f"{pending_name_prefix} {name}".strip()
            pending_name_prefix = None

        name = _BULLET.sub("", name).strip()
        if not name and not has_data:
            continue

        row = ExtractedRow(
            test_name=name or None,
            value=value or None,
            unit=unit or None,
            reference_range=ref or None,
            source_snippet=" | ".join(c for c in raw_cells if c)[:480],
            source_location=source_label,
        )
        n_expected = len(fields)
        n_filled = sum(bool(x) for x in (name, value, unit, ref))
        row.confidence = round(n_filled / max(n_expected, 1), 2)
        extracted.append(row)

    # Guard rails: if the geometry pass produced almost nothing usable, decline
    # so the caller can fall back to the line parsers.
    usable = [r for r in extracted if r.test_name and (r.value or r.reference_range)]
    if len(usable) < 2:
        return None
    return extracted


# --------------------------------------------------------------------------- #
# row / word helpers
# --------------------------------------------------------------------------- #

def _clean_row(words: list[Word]) -> list[Word]:
    kept: list[Word] = []
    for w in sorted(words, key=lambda x: x["x0"]):
        text = (w["text"] or "").strip()
        if not text:
            continue
        if text in _RULE_CHARS and (w["x1"] - w["x0"]) <= _RULE_MAX_WIDTH:
            continue  # OCR read a vertical table rule
        kept.append({**w, "text": text})
    return kept


def _row_text(words: list[Word]) -> str:
    return " ".join(w["text"] for w in words).strip()


def _center(w: Word) -> float:
    return (w["x0"] + w["x1"]) / 2.0


# --------------------------------------------------------------------------- #
# header detection
# --------------------------------------------------------------------------- #

def _classify_header_token(token: str) -> str | None:
    low = re.sub(r"[^a-z]", "", token.lower())
    if not low:
        return None
    for field, kws in _HEADER_KEYWORDS.items():
        if low in kws:
            return field
    # OCR routinely clips the short "UNIT" column header to "UN" / "UNI" / "UNT".
    # Accept a 2-5 char 'u...' token as the unit header. Only reached from
    # _find_header(), which already requires a real TEST + RESULT token in the
    # same row and rejects any row that contains a data token, so a stray short
    # word cannot hijack a data row.
    if 2 <= len(low) <= 5 and low[0] == "u" and (
        "units".startswith(low) or low in {"unt", "uit", "unl", "unic", "unir"}
    ):
        return "unit"
    return None


def _looks_like_data_token(token: str) -> bool:
    """Dates, IDs and long numbers — a header row has none of these."""
    if _NUMERIC_CELL.match(token.strip()) and len(re.sub(r"\D", "", token)) >= 3:
        return True
    return bool(re.search(r"\d", token)) and len(token) >= 5


def _find_header(rows: list[list[Word]]) -> tuple[int, dict[str, tuple[float, float]] | None]:
    """Locate the column-header row. Returns ``(index, {field: (x0, x1)})`` or
    ``(-1, None)``."""
    for idx, row in enumerate(rows[:12]):
        if any(_looks_like_data_token(w["text"]) for w in row):
            continue
        spans: dict[str, list[float]] = {}
        for w in row:
            field = _classify_header_token(w["text"])
            if field:
                spans.setdefault(field, []).extend([w["x0"], w["x1"]])
        if "test_name" in spans and "value" in spans:
            return idx, {f: (min(xs), max(xs)) for f, xs in spans.items()}
    return -1, None


def _bands_from_header(
    header_row: list[Word], header_map: dict[str, tuple[float, float]]
) -> tuple[list[tuple[float, float]], list[str]]:
    ordered = sorted(header_map.items(), key=lambda kv: (kv[1][0] + kv[1][1]) / 2)
    centers = [((x0 + x1) / 2, f) for f, (x0, x1) in ordered]
    bands: list[tuple[float, float]] = []
    fields: list[str] = []
    for i, (c, f) in enumerate(centers):
        lo = float("-inf") if i == 0 else (centers[i - 1][0] + c) / 2
        hi = float("inf") if i == len(centers) - 1 else (centers[i + 1][0] + c) / 2
        bands.append((lo, hi))
        fields.append(f)
    return bands, fields


# --------------------------------------------------------------------------- #
# headerless: cluster columns from word geometry, label by content
# --------------------------------------------------------------------------- #

def _candidate_data_rows(rows: list[list[Word]]) -> list[list[Word]]:
    out = []
    for r in rows:
        if len(r) < 2:
            continue
        if not any(re.search(r"[A-Za-z]", w["text"]) for w in r):
            continue
        out.append(r)
    return out


def _cluster_columns(rows: list[list[Word]]) -> list[tuple[float, float]] | None:
    centers = sorted(_center(w) for r in rows for w in r)
    if len(centers) < 4:
        return None
    widths = [w["x1"] - w["x0"] for r in rows for w in r]
    med_w = statistics.median(widths) if widths else 30.0
    gap_threshold = max(40.0, 2.5 * med_w)

    clusters: list[list[float]] = [[centers[0]]]
    for c in centers[1:]:
        if c - clusters[-1][-1] > gap_threshold:
            clusters.append([c])
        else:
            clusters[-1].append(c)
    if len(clusters) < 2:
        return None

    cluster_centers = [statistics.mean(cl) for cl in clusters]
    bands: list[tuple[float, float]] = []
    for i, cc in enumerate(cluster_centers):
        lo = float("-inf") if i == 0 else (cluster_centers[i - 1] + cc) / 2
        hi = float("inf") if i == len(cluster_centers) - 1 else (cluster_centers[i + 1] + cc) / 2
        bands.append((lo, hi))
    return bands


def _bands_from_content(
    rows: list[list[Word]]
) -> tuple[list[tuple[float, float]], list[str]] | None:
    data = _candidate_data_rows(rows)
    if len(data) < 3:
        return None
    bands = _cluster_columns(data)
    if bands is None:
        return None

    # Collect each band's cell text across the data rows.
    n = len(bands)
    columns: list[list[str]] = [[] for _ in range(n)]
    for r in data:
        assigned = _assign(r, bands)
        for bi in range(n):
            columns[bi].append(assigned.get(bi, ""))

    def frac(cells: list[str], pred) -> float:
        vals = [c for c in cells if c.strip()]
        if not vals:
            return 0.0
        return sum(1 for c in vals if pred(c)) / len(vals)

    is_num = lambda c: bool(_NUMERIC_CELL.match(c.strip())) or c.strip().lower() in _QUALITATIVE
    is_alpha = lambda c: bool(re.search(r"[A-Za-z]", c)) and not _NUMERIC_CELL.match(c.strip())
    is_unit = lambda c: (
        c.strip().lower().rstrip(".") in _UNIT_LEXICON
        or (bool(_UNIT_SHAPE.match(c.strip())) and not _NUMERIC_CELL.match(c.strip())
            and any(ch in c for ch in "%/") )
        or c.strip() in {"%"}
    )
    is_range = lambda c: bool(_RANGE_CELL.search(c.strip()))

    fields: list[str | None] = [None] * n
    # test_name: leftmost strongly-alpha band
    for bi in range(n):
        if frac(columns[bi], is_alpha) >= 0.5:
            fields[bi] = "test_name"
            break
    if "test_name" not in fields:
        return None
    name_bi = fields.index("test_name")

    # value: leftmost numeric/qualitative band to the right of the name band
    for bi in range(name_bi + 1, n):
        if fields[bi] is None and frac(columns[bi], is_num) >= 0.5:
            fields[bi] = "value"
            break
    if "value" not in fields:
        return None

    # unit: a remaining band that is unit-shaped and not numeric
    for bi in range(name_bi + 1, n):
        if fields[bi] is None and frac(columns[bi], is_unit) >= 0.4 and frac(columns[bi], is_num) < 0.4:
            fields[bi] = "unit"
            break

    # reference_range: a remaining band that looks like ranges, else the rightmost
    for bi in range(n - 1, name_bi, -1):
        if fields[bi] is None and frac(columns[bi], is_range) >= 0.4:
            fields[bi] = "reference_range"
            break
    if "reference_range" not in fields:
        for bi in range(n - 1, name_bi, -1):
            if fields[bi] is None:
                fields[bi] = "reference_range"
                break

    kept = [(b, f) for b, f in zip(bands, fields) if f is not None]
    kept.sort(key=lambda bf: bf[0][0])
    return [b for b, _ in kept], [f for _, f in kept]


# --------------------------------------------------------------------------- #
# assign words to bands
# --------------------------------------------------------------------------- #

def _assign(row: list[Word], bands: list[tuple[float, float]]) -> dict[int, str]:
    buckets: dict[int, list[Word]] = {}
    for w in row:
        c = _center(w)
        for bi, (lo, hi) in enumerate(bands):
            if lo <= c < hi:
                buckets.setdefault(bi, []).append(w)
                break
    out: dict[int, str] = {}
    for bi, ws in buckets.items():
        text = " ".join(x["text"] for x in sorted(ws, key=lambda x: x["x0"]))
        out[bi] = _tidy_cell(text)
    return out


def _row_to_cells(
    row: list[Word], bands: list[tuple[float, float]], fields: list[str]
) -> dict[str, str]:
    assigned = _assign(row, bands)
    cells: dict[str, str] = {}
    for bi, field in enumerate(fields):
        if bi in assigned and assigned[bi]:
            cells[field] = (cells.get(field, "") + " " + assigned[bi]).strip()
    # A unit cell of several tokens ("il mg/dL") keeps only the unit-shaped ones,
    # dropping OCR crumbs that drifted into the band.
    unit = cells.get("unit")
    if unit and " " in unit:
        parts = [p for p in unit.split() if _UNIT_SHAPE.match(p) and not _NON_UNIT_TOKEN.match(p)]
        if parts:
            cells["unit"] = " ".join(parts[-1:])
    return cells


def _tidy_cell(text: str) -> str:
    """Collapse run-together spacing only. Do not inject or remove spaces around
    a dash: a split range ("70", "-", "100") reunites as "70 - 100" via the word
    join, while a single-token range ("12-16") is left exactly as printed."""
    return re.sub(r"\s{2,}", " ", text).strip()


def _is_section_heading(name: str) -> bool:
    n = name.strip()
    if _SECTION_RE.match(n):
        return True
    words = n.split()
    if len(words) >= 2 and n == n.upper() and not n.startswith(("(", "-")):
        return True
    return False
