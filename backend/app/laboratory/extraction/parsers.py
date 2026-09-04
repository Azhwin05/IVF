"""Layout-aware rule-based parsers: text lines -> structured rows.

Ported from the research prototype. These are deliberately a set of small
strategies each targeting one structural pattern (ruled table with a header,
narrative block, colon-inline, dotted leader, one-line triplet, qualitative
result), not one universal regex. ``parse_lines`` tries them in order and a
test name is only claimed by the first strategy that matches it, so rows are
never double-counted. Every new outsourced-lab template risks needing a new
strategy here — that is the documented cost of the rule-based approach.
"""

import re

from app.laboratory.extraction.dto import ExtractedRow

_NUM = r"[<>]?\d+(?:\.\d+)?"

_HEADER_KEYWORDS = {
    "test_name": ["test", "investigation", "parameter"],
    "value": ["result", "value"],
    "unit": ["unit"],
    "reference_range": ["reference", "range", "ref"],
}


def _classify_header_cols(cols: list[str]) -> dict[int, str]:
    mapping: dict[int, str] = {}
    for i, col in enumerate(cols):
        low = col.strip().lower()
        for field, kws in _HEADER_KEYWORDS.items():
            if any(kw in low for kw in kws):
                mapping[i] = field
                break
    return mapping


def try_parse_table_block(lines: list[str], source_label: str) -> list[ExtractedRow]:
    """Header-directed column split for ruled/aligned tables (2+ space gaps)."""
    results: list[ExtractedRow] = []
    header_map: dict[int, str] | None = None
    for raw in lines:
        line = raw.rstrip()
        if not line.strip():
            continue
        cols = re.split(r"\s{2,}", line.strip())
        if header_map is None:
            m = _classify_header_cols(cols)
            if len(m) >= 3:  # confident this is the header row
                header_map = m
            continue
        if len(cols) < 3:
            continue
        row = {"test_name": None, "value": None, "unit": None, "reference_range": None}
        for i, val in enumerate(cols):
            field = header_map.get(i)
            if not field:
                continue
            val = val.strip()
            if not val:
                continue
            # A header can split one logical column across two cells — e.g.
            # "BIOLOGICAL REFERENCE" then "RANGE" both classify as
            # reference_range, and a value like "70 -" "100" arrives in two
            # cells. Join them rather than letting the later cell overwrite the
            # earlier one and lose half the range.
            row[field] = f"{row[field]} {val}" if row[field] else val
        if row["test_name"] and row["value"]:
            results.append(
                ExtractedRow(
                    test_name=row["test_name"],
                    value=row["value"],
                    unit=row["unit"],
                    reference_range=row["reference_range"],
                    source_snippet=line,
                    source_location=source_label,
                )
            )
    return results


_NARRATIVE_RESULT = re.compile(
    r"^Result:\s*(" + _NUM + r")\s*([A-Za-z%/µu]+(?:/[A-Za-z]+)?)?", re.I
)
_NARRATIVE_REF = re.compile(r"^Reference (?:Interval|Range):\s*(.+)$", re.I)


def try_parse_narrative_block(lines: list[str], source_label: str) -> list[ExtractedRow]:
    """'Test name' line, then 'Result: X unit', then 'Reference Interval: Y'."""
    results: list[ExtractedRow] = []
    i = 0
    n = len(lines)
    while i < n:
        name_line = lines[i].strip()
        if name_line and i + 1 < n and _NARRATIVE_RESULT.match(lines[i + 1].strip()):
            m = _NARRATIVE_RESULT.match(lines[i + 1].strip())
            assert m is not None
            value, unit = m.group(1), m.group(2)
            ref = None
            j = i + 2
            if j < n:
                rm = _NARRATIVE_REF.match(lines[j].strip())
                if rm:
                    ref = rm.group(1).strip()
                    j += 1
            results.append(
                ExtractedRow(
                    test_name=name_line,
                    value=value,
                    unit=unit,
                    reference_range=ref,
                    source_snippet=" | ".join(lines[i:j]),
                    source_location=source_label,
                )
            )
            i = j
        else:
            i += 1
    return results


_COLON_INLINE = re.compile(
    r"^([A-Za-z0-9 /()\-]+?):\s*(<?>?\d+(?:\.\d+)?)\s*"
    r"([A-Za-z%/µ]+(?:/[A-Za-z]+)?)?\s*(?:\(Ref:\s*([^)]+)\))?\s*$"
)
_RESERVED_COLON_LABELS = {"result", "reference", "reference interval", "reference range"}


def try_parse_colon_inline(lines: list[str], source_label: str) -> list[ExtractedRow]:
    results: list[ExtractedRow] = []
    for line in lines:
        m = _COLON_INLINE.match(line.strip())
        if m and m.group(1).strip().lower() not in _RESERVED_COLON_LABELS:
            name, value, unit, ref = m.groups()
            results.append(
                ExtractedRow(
                    test_name=name.strip(),
                    value=value,
                    unit=unit,
                    reference_range=ref.strip() if ref else None,
                    source_snippet=line.strip(),
                    source_location=source_label,
                )
            )
    return results


_DOTTED_LINE = re.compile(
    r"^([A-Za-z0-9 %()\-]+?)\s*\.{3,}\s*(<?>?\d+(?:\.\d+)?)\s+"
    r"([A-Za-z%/µ]+(?:/[A-Za-z]+)?)\s+(.+)$"
)


def try_parse_dotted(lines: list[str], source_label: str) -> list[ExtractedRow]:
    results: list[ExtractedRow] = []
    for line in lines:
        m = _DOTTED_LINE.match(line.strip())
        if m:
            name, value, unit, ref = m.groups()
            results.append(
                ExtractedRow(
                    test_name=name.strip(),
                    value=value,
                    unit=unit,
                    reference_range=ref.strip(),
                    source_snippet=line.strip(),
                    source_location=source_label,
                )
            )
    return results


_TEXTUAL_RESULT = re.compile(
    r"^([A-Za-z0-9 ()/\-]+?)\s{2,}"
    r"(Non-Reactive|Reactive|Negative|Positive|Nil|Trace|[A-Za-z]+ (?:Positive|Negative))\s*$",
    re.I,
)


def try_parse_textual(lines: list[str], source_label: str) -> list[ExtractedRow]:
    results: list[ExtractedRow] = []
    for line in lines:
        m = _TEXTUAL_RESULT.match(line.strip())
        if m:
            name, value = m.groups()
            results.append(
                ExtractedRow(
                    test_name=name.strip(),
                    value=value.strip(),
                    unit=None,
                    reference_range=None,
                    source_snippet=line.strip(),
                    source_location=source_label,
                )
            )
    return results


_SIMPLE_TRIPLET = re.compile(
    r"^([A-Za-z0-9 ()/\-]+?)\s{2,}(<?>?\d+(?:\.\d+)?)\s*"
    r"([A-Za-z%/µ]+(?:/[A-Za-z]+)?)?\s*$"
)


def try_parse_simple_triplet(lines: list[str], source_label: str) -> list[ExtractedRow]:
    """name  value  [unit] on one line, no reference range present at all."""
    results: list[ExtractedRow] = []
    for line in lines:
        s = line.strip()
        if not s or ":" in s:
            continue
        # This strategy only handles two or three whitespace-run columns
        # (name / value / optional unit). A line with more columns is a
        # multi-column table row — leave it to the column-aware parsers.
        # Without this guard the lazy name group can swallow an entire wide
        # OCR line (value, unit and half the range) into test_name.
        if not 2 <= len(re.split(r"\s{2,}", s)) <= 3:
            continue
        m = _SIMPLE_TRIPLET.match(s)
        if m:
            name, value, unit = m.groups()
            results.append(
                ExtractedRow(
                    test_name=name.strip(),
                    value=value,
                    unit=unit,
                    reference_range=None,
                    source_snippet=s,
                    source_location=source_label,
                )
            )
    return results


_COLUMNAR_NUMERIC = re.compile(r"^[<>]?=?\s*-?\d[\d.,]*$")
_COLUMNAR_UNIT = re.compile(r"^[A-Za-zµ%][A-Za-zµ%/.]*$")
_COLUMNAR_HEADER_WORDS = {
    "test", "investigation", "parameter", "result", "value", "unit",
    "reference", "range", "ref", "analyte", "observation",
}


def try_parse_columnar_row(lines: list[str], source_label: str) -> list[ExtractedRow]:
    """Header-less whitespace-delimited rows: ``name  value  [unit]  [range]``.

    Common in scanned CBC/biochem panels that carry no column header row, which
    is why the header-directed table parser cannot claim them. Only fires when
    the second column is numeric, so prose lines are left alone.
    """
    results: list[ExtractedRow] = []
    for raw in lines:
        s = raw.strip()
        if not s or ":" in s:
            continue
        cols = re.split(r"\s{2,}", s)
        if not (3 <= len(cols) <= 5):
            continue
        name, value, *rest = [c.strip() for c in cols]
        if not any(ch.isalpha() for ch in name):
            continue
        if name.lower() in _COLUMNAR_HEADER_WORDS:
            continue
        if not _COLUMNAR_NUMERIC.match(value):
            continue

        unit: str | None = None
        reference_range: str | None = None
        for token in rest:
            has_digit = any(ch.isdigit() for ch in token)
            if unit is None and not has_digit and _COLUMNAR_UNIT.match(token):
                unit = token
            elif reference_range is None and has_digit:
                reference_range = token
        results.append(
            ExtractedRow(
                test_name=name,
                value=value,
                unit=unit,
                reference_range=reference_range,
                source_snippet=s,
                source_location=source_label,
            )
        )
    return results


_STRATEGIES = (
    try_parse_table_block,
    try_parse_narrative_block,
    try_parse_colon_inline,
    try_parse_dotted,
    try_parse_textual,
    try_parse_simple_triplet,
    try_parse_columnar_row,
)


def parse_lines(lines: list[str], source_label: str) -> list[ExtractedRow]:
    all_results: list[ExtractedRow] = []
    claimed: set[str] = set()
    for fn in _STRATEGIES:
        for row in fn(lines, source_label):
            key = (row.test_name or "").strip().lower()
            if not key or key in claimed:
                continue
            claimed.add(key)
            all_results.append(row)
    return all_results
