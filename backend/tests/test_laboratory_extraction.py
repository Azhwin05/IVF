"""Benchmark-style tests for the deterministic extraction pipeline.

Runs the pipeline over the 13 synthetic outside-lab reports carried over from the
research prototype and scores the output against the hand-written ground truth.
This is a regression floor, not a demand for perfection: the rule-based approach
is known to miss rows on the harder layouts (the prototype measured ~63% of
ground-truth rows missing overall), and the scanned reports need OCR that is not
present in every environment. What the assertions guarantee is that the pipeline

  * never raises on a real report,
  * never emits a row without both a test name and a value,
  * gets value/unit exactly right on the rows it does match,
  * still extracts the clean digital tables it is expected to handle.
"""

import json
import re
from pathlib import Path

import pytest

from app.core.config import get_settings
from app.laboratory.extraction import extract_document
from app.laboratory.extraction.normalization import normalize_test_name
from app.laboratory.extraction.ocr import ocr_available

FIXTURES = Path(__file__).parent / "fixtures" / "lab_reports"
REPORTS_DIR = FIXTURES / "reports"
GT_DIR = FIXTURES / "ground_truth"

# Reports whose source is a scanned image / rotated scan: only scorable with OCR.
NEEDS_OCR = {
    "report_E_scanned",
    "report_G_ocr_stress",
    "report_M_scanned_rotated",
    "lab_sample2",
    "labsample1",
}

_CONTENT_TYPE = {".pdf": "application/pdf", ".png": "image/png"}


def _norm(s: object) -> str | None:
    if s is None:
        return None
    return str(s).strip().lower().replace("–", "-").replace(" ", "")


def _canon_name(s: object) -> str | None:
    """Fold a test name to its canonical form so the ground truth (which uses
    lab abbreviations) and the pipeline output (which normalises them) compare
    equal."""
    if s is None:
        return None
    canonical, _ = normalize_test_name(str(s))
    return _norm(canonical or s)


def _score(pred: list[dict], gt: list[dict]) -> dict:
    gt_used = [False] * len(gt)
    matched: list[tuple[dict, dict]] = []
    for p in pred:
        best_i, best_s = None, 0
        for i, g in enumerate(gt):
            if gt_used[i]:
                continue
            pn, gn = _canon_name(p["test_name"]), _canon_name(g["test_name"])
            s = 3 if pn == gn else (1 if pn and gn and (pn in gn or gn in pn) else 0)
            if s > best_s:
                best_s, best_i = s, i
        if best_i is not None:
            gt_used[best_i] = True
            matched.append((p, gt[best_i]))

    value_ok = sum(1 for p, g in matched if _norm(p["value"]) == _norm(g["value"]))
    unit_ok = sum(1 for p, g in matched if _norm(p["unit"]) == _norm(g["unit"]))
    return {
        "n_gt": len(gt),
        "n_pred": len(pred),
        "n_matched": len(matched),
        "value_ok": value_ok,
        "unit_ok": unit_ok,
    }


def _cases() -> list[str]:
    return sorted(p.stem for p in REPORTS_DIR.iterdir() if p.suffix in _CONTENT_TYPE)


def _run(report_id: str) -> list[dict]:
    path = next(REPORTS_DIR.glob(f"{report_id}.*"))
    outcome = extract_document(
        path.read_bytes(),
        filename=path.name,
        content_type=_CONTENT_TYPE[path.suffix],
        settings=get_settings(),
    )
    return [
        {
            "test_name": r.test_name,
            "value": r.value,
            "unit": r.unit,
            "reference_range": r.reference_range,
            "status": r.validation_status.value,
        }
        for r in outcome.rows
    ], outcome


@pytest.mark.parametrize("report_id", _cases())
def test_pipeline_never_raises_and_never_fabricates(report_id: str) -> None:
    rows, outcome = _run(report_id)

    if outcome.error:
        # Only acceptable when the report genuinely needs OCR and it is absent.
        assert report_id in NEEDS_OCR and not ocr_available()
        assert rows == []
        return

    for row in rows:
        # A row is only emitted with both a name and a value, or it is flagged
        # as not-extracted for the reviewer — never a silent blank.
        if row["status"] != "not_extracted":
            assert row["test_name"] and row["value"], row


def test_clean_digital_tables_are_extracted_accurately() -> None:
    """Aggregate floor over the digital-PDF reports."""
    total_matched = 0
    total_value_ok = 0
    total_unit_ok = 0
    total_gt = 0

    for report_id in _cases():
        if report_id in NEEDS_OCR:
            continue
        rows, outcome = _run(report_id)
        assert not outcome.error, (report_id, outcome.error)
        gt = json.loads((GT_DIR / f"{report_id}.json").read_text())["results"]
        s = _score(rows, gt)
        total_matched += s["n_matched"]
        total_value_ok += s["value_ok"]
        total_unit_ok += s["unit_ok"]
        total_gt += s["n_gt"]

    # The pipeline must match a meaningful share of the digital-report rows...
    assert total_matched >= total_gt * 0.4
    # ...and be exact on value and unit for the rows it does match.
    assert total_value_ok == total_matched
    assert total_unit_ok == total_matched


def test_clean_table_report_is_fully_recovered() -> None:
    """report_A is the baseline every future change must keep passing."""
    rows, outcome = _run("report_A_clean_table")
    assert not outcome.error
    gt = json.loads((GT_DIR / "report_A_clean_table.json").read_text())["results"]
    s = _score(rows, gt)
    assert s["n_matched"] == s["n_gt"]
    assert s["value_ok"] == s["n_gt"]
    assert s["unit_ok"] == s["n_gt"]


@pytest.mark.skipif(not ocr_available(), reason="Tesseract OCR not installed")
@pytest.mark.parametrize("report_id", sorted(NEEDS_OCR))
def test_scanned_reports_go_through_ocr_and_extract_something(report_id: str) -> None:
    rows, outcome = _run(report_id)
    assert not outcome.error
    assert outcome.method.value == "ocr"
    assert len(rows) >= 1
    # OCR may misread a character, but a row that is *saved as a result* always
    # has a name and a value. A row the pipeline could not complete is flagged
    # "not_extracted" (its fields left empty) rather than fabricated.
    for r in rows:
        if r["status"] != "not_extracted":
            assert (r["test_name"] or "").strip()
            assert (r["value"] or "").strip()


@pytest.mark.skipif(not ocr_available(), reason="Tesseract OCR not installed")
def test_report_g_ocr_recovers_the_whole_panel() -> None:
    """report_G is the clean-OCR baseline: three rows, values exact."""
    rows, outcome = _run("report_G_ocr_stress")
    assert not outcome.error
    gt = json.loads((GT_DIR / "report_G_ocr_stress.json").read_text())["results"]
    s = _score(rows, gt)
    assert s["n_matched"] == s["n_gt"] == 3
    assert s["value_ok"] == 3
    assert s["unit_ok"] == 3


# ----- regression: dense 4-column scanned panels (lab_sample2.png) ------------
#
# A wide OCR line such as
#   "Fasting Blood Sugar        103        mg/dL        70 -  100"
# was swallowed *whole* into test_name (270 chars) by try_parse_simple_triplet,
# whose lazy name group can consume digits, column gaps and units. That 270-char
# string then failed the INSERT into lab_results.test_name (VARCHAR(200)) on
# PostgreSQL and surfaced as HTTP 500. The parser must split the line into
# name / value / unit / reference_range instead.

_LIMITS = {"test_name": 200, "value": 120, "unit": 60, "reference_range": 120}


def test_dense_multi_column_row_is_split_not_swallowed_into_test_name() -> None:
    """Pure-parser check, no OCR needed: the exact failure pattern is separated
    into columns and no test_name approaches the VARCHAR(200) limit."""
    from app.laboratory.extraction.parsers import parse_lines

    header = (
        "TEST" + " " * 40 + "RESULT" + " " * 40 + "UNIT" + " " * 20
        + "BIOLOGICAL REFERENCE" + " " * 4 + "RANGE"
    )
    dense = (
        "Fasting Blood Sugar" + " " * 80 + "103" + " " * 60 + "mg/dL"
        + " " * 70 + "70 -  100"
    )
    rows = parse_lines([header, dense], "page 1")

    fbs = [r for r in rows if (r.test_name or "").strip().lower() == "fasting blood sugar"]
    assert fbs, f"row not isolated; parser produced {[r.test_name for r in rows]!r}"
    r = fbs[0]
    assert r.value == "103"
    assert r.unit == "mg/dL"
    assert r.reference_range == "70 - 100"
    assert all(len(x.test_name or "") <= _LIMITS["test_name"] for x in rows)


@pytest.mark.skipif(not ocr_available(), reason="Tesseract OCR not installed")
def test_lab_sample2_extraction_is_bounded_and_the_fbs_row_is_correct() -> None:
    """End-to-end over the real scanned image."""
    rows, outcome = _run("lab_sample2")
    assert not outcome.error
    assert outcome.method.value == "ocr"

    for row in rows:
        for field, limit in _LIMITS.items():
            v = row[field]
            assert v is None or len(v) <= limit, (field, len(v), row)

    # The alias table normalises "Fasting Blood Sugar" -> "Fasting Blood Glucose";
    # accept either so the row can be found regardless of that (separate) step.
    fbs = [
        r for r in rows
        if (r["test_name"] or "").lower() in ("fasting blood sugar", "fasting blood glucose")
    ]
    assert fbs, f"Fasting Blood Sugar row missing; got {[r['test_name'] for r in rows]!r}"
    r = fbs[0]
    assert r["value"] == "103"
    assert r["unit"] == "mg/dL"
    assert r["reference_range"] == "70 - 100"


# ----- regression: value + unit glued into VALUE (labsample1.png) -------------
#
# labsample1.png is a clean rendered lab report. OCR reads it well BUT clips the
# narrow "UNIT" column header to "UN". The geometry parser matched only
# TEST / RESULT / REFERENCE RANGE, built no unit band, and every unit token fell
# into the value band -> value "13.8 g/dL", unit None, plus a stream of false
# "value is neither numeric" warnings and bogus normalisation suggestions
# (Basophils -> Neutrophils, HDL Cholesterol -> Total Cholesterol).
#
# Fix: (1) _classify_header_token accepts an OCR-clipped "UN..." unit header;
# (2) a value/unit splitter separates "<number> <unit>" whenever the unit column
# is missing; (3) common CBC/biochem/LFT names are exact aliases so they are not
# fuzzily "suggested" as unrelated tests. Genuine OCR damage in the reference
# range (Basophils "0 - 1" -> "o-1") stays flagged, never auto-corrected.

_LABSAMPLE1_KNOWN_OCR_RANGE = {
    # canonical name -> the range as OCR actually read it (a real misread we do
    # NOT silently fix; value / unit / name are still correct).
    "basophils": "o-1",             # '0' read as 'o'  -> flagged needs_review
    "serumcreatinine": "0,67-1.17",  # '.' read as ','  (value/unit still exact)
}


@pytest.mark.skipif(not ocr_available(), reason="Tesseract OCR not installed")
def test_labsample1_value_unit_reference_are_separated() -> None:
    rows, outcome = _run("labsample1")
    assert not outcome.error
    assert outcome.method.value == "ocr"

    gt = json.loads((GT_DIR / "labsample1.json").read_text(encoding="utf-8"))["results"]
    assert len(rows) == len(gt) == 22, f"expected 22 rows, got {len(rows)}"

    by_name = {_canon_name(r["test_name"]): r for r in rows}

    for g in gt:
        cname = _canon_name(g["test_name"])
        assert cname in by_name, f"missing row for {g['test_name']!r}: got {sorted(by_name)}"
        r = by_name[cname]

        # --- the core regression: VALUE holds only the number, UNIT holds only
        # the unit, and neither is empty ---
        assert r["value"] and _norm(r["value"]) == _norm(g["value"]), (
            g["test_name"], "value", r["value"], "!=", g["value"]
        )
        assert r["unit"], f"{g['test_name']}: unit was not separated from the value"
        assert _norm(r["unit"]) == _norm(g["unit"]), (
            g["test_name"], "unit", r["unit"], "!=", g["unit"]
        )
        # value must be a bare number / comparator — never "<number> <unit>"
        assert not re.search(r"[A-Za-z]", r["value"] or ""), (
            g["test_name"], "value still contains letters:", r["value"]
        )
        assert "/" not in (r["value"] or ""), (g["test_name"], r["value"])

        # --- reference range: exact, or one of the two documented OCR misreads ---
        if _norm(r["reference_range"]) != _norm(g["reference_range"]):
            assert cname in _LABSAMPLE1_KNOWN_OCR_RANGE, (
                g["test_name"], "unexpected range", r["reference_range"],
                "expected", g["reference_range"],
            )
            assert _norm(r["reference_range"]) == _norm(
                _LABSAMPLE1_KNOWN_OCR_RANGE[cname]
            )
            if cname == "basophils":
                assert r["status"] == "needs_review", (
                    "an OCR-garbled range must stay flagged, not pass as ok"
                )

    # --- normalisation: obvious exact tests are aliases, NOT fuzzy suggestions ---
    from app.laboratory.extraction import extract_document as _ed

    outcome2 = _ed(
        (REPORTS_DIR / "labsample1.png").read_bytes(),
        filename="labsample1.png", content_type="image/png", settings=get_settings(),
    )
    for er in outcome2.rows:
        assert er.validation_status.value != "not_extracted", er.test_name
        if er.test_name and er.test_name.lower() in {
            "basophils", "monocytes", "eosinophils", "neutrophils", "lymphocytes",
            "hdl cholesterol", "ldl cholesterol (calculated)", "total cholesterol",
            "triglycerides", "sgot (ast)", "sgpt (alt)",
        }:
            assert er.normalization_match.value == "exact_alias", er.test_name
            assert not (er.normalization_note and "Possible tests" in er.normalization_note), (
                er.test_name, er.normalization_note,
            )

    # at most the two genuine OCR-range rows need review; nothing is unreadable
    statuses = [r["status"] for r in rows]
    assert statuses.count("not_extracted") == 0
    assert statuses.count("needs_review") <= 2
