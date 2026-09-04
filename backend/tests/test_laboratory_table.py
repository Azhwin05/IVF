"""Unit tests for the geometry-aware table extractor.

These feed synthetic *positioned words* straight into
``table.extract_rows_from_word_rows`` — no OCR, no image, fully deterministic —
so they pin the column-detection behaviour across the layouts the rule-based
line parsers could not handle: inconsistent spacing, reordered columns, missing
fields, reference ranges split across cells, multi-line names, OCR rule
artefacts, and numeric tokens drifting toward the test-name column.
"""

from app.laboratory.extraction import table
from app.laboratory.extraction.validation import validate_row

_CHAR_W = 9


def W(text: str, x0: float) -> dict:
    return {"text": text, "x0": float(x0), "x1": float(x0 + len(text) * _CHAR_W), "top": 0.0}


def rule(x0: float) -> dict:
    """A 1-px-wide vertical-rule token, the way OCR emits it."""
    return {"text": "|", "x0": float(x0), "x1": float(x0 + 1), "top": 0.0}


def R(*cells: tuple[str, float]) -> list[dict]:
    return [W(t, x) for t, x in cells]


# Column x-centres used by most cases: name~60, value~630, unit~940, range~1250
HEADER = R(("TEST", 55), ("RESULT", 615), ("UNIT", 930), ("REFERENCE", 1160), ("RANGE", 1390))


def _by_name(rows, name):
    for r in rows:
        if (r.test_name or "").lower().startswith(name.lower()):
            return r
    raise AssertionError(f"{name!r} not in {[r.test_name for r in rows]}")


class TestHeaderAnchored:
    def test_basic_four_column(self):
        rows = table.extract_rows_from_word_rows(
            [
                HEADER,
                R(("Hemoglobin", 55), ("13.5", 625), ("g/dL", 935), ("12-16", 1245)),
                R(("Sodium", 55), ("138", 630), ("mEq/L", 930), ("135-145", 1240)),
                R(("Platelet Count", 55), ("250000", 615), ("cells/uL", 930), ("150000-450000", 1230)),
            ],
            "page 1",
        )
        assert rows is not None and len(rows) == 3
        hb = _by_name(rows, "Hemoglobin")
        assert (hb.test_name, hb.value, hb.unit, hb.reference_range) == (
            "Hemoglobin", "13.5", "g/dL", "12-16",
        )
        assert all(len(r.test_name) <= 200 for r in rows)

    def test_inconsistent_spacing_still_maps(self):
        # each row's words wobble ±18px but stay inside their band
        rows = table.extract_rows_from_word_rows(
            [
                HEADER,
                R(("Urea", 40), ("28", 648), ("mg/dL", 918), ("15-40", 1262)),
                R(("Creatinine", 72), ("0.9", 612), ("mg/dL", 956), ("0.6-1.2", 1228)),
                R(("Uric Acid", 58), ("5.7", 636), ("mg/dL", 944), ("3.5-7.2", 1255)),
            ],
            "page 1",
        )
        assert rows is not None and len(rows) == 3
        assert [r.value for r in rows] == ["28", "0.9", "5.7"]
        assert [r.unit for r in rows] == ["mg/dL", "mg/dL", "mg/dL"]

    def test_reordered_columns_follow_the_header(self):
        header = R(("Reference", 40), ("Range", 250), ("Test", 620), ("Result", 930), ("Unit", 1240))
        rows = table.extract_rows_from_word_rows(
            [
                header,
                R(("12-16", 40), ("Hemoglobin", 620), ("13.5", 930), ("g/dL", 1240)),
                R(("135-145", 40), ("Sodium", 620), ("138", 930), ("mEq/L", 1240)),
            ],
            "page 1",
        )
        assert rows is not None and len(rows) == 2
        hb = _by_name(rows, "Hemoglobin")
        assert (hb.value, hb.unit, hb.reference_range) == ("13.5", "g/dL", "12-16")

    def test_missing_unit(self):
        rows = table.extract_rows_from_word_rows(
            [
                HEADER,
                R(("Hemoglobin", 55), ("13.5", 625), ("g/dL", 935), ("12-16", 1245)),
                R(("Ratio", 55), ("1.8", 630), ("1.0-2.0", 1240)),  # no unit cell
            ],
            "page 1",
        )
        assert rows is not None
        ratio = _by_name(rows, "Ratio")
        assert ratio.value == "1.8"
        assert ratio.unit is None
        assert ratio.reference_range == "1.0-2.0"

    def test_missing_reference_range(self):
        rows = table.extract_rows_from_word_rows(
            [
                HEADER,
                R(("Hemoglobin", 55), ("13.5", 625), ("g/dL", 935), ("12-16", 1245)),
                R(("Glucose", 55), ("95", 630), ("mg/dL", 935)),  # no range cell
            ],
            "page 1",
        )
        glu = _by_name(rows, "Glucose")
        assert (glu.value, glu.unit) == ("95", "mg/dL")
        assert glu.reference_range is None

    def test_missing_value_is_left_empty_not_guessed(self):
        rows = table.extract_rows_from_word_rows(
            [
                HEADER,
                R(("Hemoglobin", 55), ("13.5", 625), ("g/dL", 935), ("12-16", 1245)),
                R(("Sodium", 55), ("138", 630), ("mEq/L", 935), ("135-145", 1245)),
                R(("Potassium", 55), ("mEq/L", 935), ("3.5-5.1", 1245)),  # value cell missing
            ],
            "page 1",
        )
        k = _by_name(rows, "Potassium")
        assert k.value is None
        assert validate_row(k).validation_status.value == "not_extracted"

    def test_split_reference_range_is_rejoined(self):
        rows = table.extract_rows_from_word_rows(
            [
                HEADER,
                R(("Hemoglobin", 55), ("13.5", 625), ("g/dL", 935), ("12-16", 1245)),
                R(("Fasting Blood Sugar", 55), ("103", 630), ("mg/dL", 935),
                  ("70", 1240), ("-", 1268), ("100", 1284)),
            ],
            "page 1",
        )
        fbs = _by_name(rows, "Fasting Blood Sugar")
        assert fbs.value == "103"
        assert fbs.unit == "mg/dL"
        assert fbs.reference_range == "70 - 100"
        assert len(fbs.test_name) <= 200

    def test_ocr_rule_artefacts_are_dropped(self):
        # exactly the lab_sample2 failure: "|" tokens between the real bands
        rows = table.extract_rows_from_word_rows(
            [
                HEADER,
                R(("Hemoglobin", 55), ("13.5", 625), ("g/dL", 935), ("12-16", 1245)),
                [W("-", 62), W("Eosinophils", 75), rule(522), W("5", 641),
                 W("%", 944), rule(1099), W("1-6", 1272)],
                [W("-", 62), W("Monocytes", 75), rule(522), W("4", 640), rule(802),
                 W("%", 944), rule(1099), W("2-8", 1271)],
            ],
            "page 1",
        )
        eo = _by_name(rows, "Eosinophils")
        assert (eo.value, eo.unit, eo.reference_range) == ("5", "%", "1-6")
        mo = _by_name(rows, "Monocytes")
        assert (mo.value, mo.unit, mo.reference_range) == ("4", "%", "2-8")

    def test_multi_line_test_name_with_paren_continuation(self):
        rows = table.extract_rows_from_word_rows(
            [
                HEADER,
                R(("Hemoglobin", 55), ("13.5", 625), ("g/dL", 935), ("12-16", 1245)),
                R(("Sodium", 55), ("138", 625), ("mEq/L", 935), ("135-145", 1245)),
                R(("Vitamin D", 55)),  # name wraps
                R(("(25-OH)", 55), ("32", 630), ("ng/mL", 935), ("30-100", 1245)),
            ],
            "page 1",
        )
        vd = _by_name(rows, "Vitamin D")
        assert vd.test_name == "Vitamin D (25-OH)"
        assert (vd.value, vd.unit, vd.reference_range) == ("32", "ng/mL", "30-100")

    def test_section_heading_is_not_emitted_as_a_result(self):
        rows = table.extract_rows_from_word_rows(
            [
                HEADER,
                R(("Hemoglobin", 55), ("13.5", 625), ("g/dL", 935), ("12-16", 1245)),
                R(("BIOCHEMISTRY", 55)),
                R(("Glucose", 55), ("95", 630), ("mg/dL", 935), ("70-100", 1245)),
                R(("Urea", 55), ("28", 630), ("mg/dL", 935), ("15-40", 1245)),
            ],
            "page 1",
        )
        assert "BIOCHEMISTRY" not in [r.test_name for r in rows]
        assert {r.test_name for r in rows} == {"Hemoglobin", "Glucose", "Urea"}

    def test_numeric_token_never_becomes_the_test_name(self):
        rows = table.extract_rows_from_word_rows(
            [
                HEADER,
                R(("Hemoglobin", 55), ("13.5", 625), ("g/dL", 935), ("12-16", 1245)),
                R(("Sodium", 55), ("138", 625), ("mEq/L", 935), ("135-145", 1245)),
                # OCR dropped the name; a stray number sits where the name would be
                R(("0.8", 60), ("102", 630), ("mg/dL", 935), ("<130", 1245)),
            ],
            "page 1",
        )
        for r in rows:
            assert r.test_name is None or not r.test_name.strip().replace(".", "").isdigit()
        stray = [r for r in rows if r.test_name in (None, "", "0.8")]
        assert stray, "the nameless numeric row should still be present, flagged"
        assert validate_row(stray[0]).validation_status.value == "not_extracted"


class TestHeaderlessContentClustering:
    def test_headerless_cbc_panel(self):
        rows = table.extract_rows_from_word_rows(
            [
                R(("Hemoglobin", 55), ("13.5", 625), ("g/dL", 935), ("12-16", 1245)),
                R(("WBC", 55), ("7200", 625), ("cells/uL", 930), ("4000-11000", 1235)),
                R(("Sodium", 55), ("138", 630), ("mEq/L", 935), ("135-145", 1245)),
            ],
            "page 1",
        )
        assert rows is not None and len(rows) == 3
        na = _by_name(rows, "Sodium")
        assert (na.value, na.unit, na.reference_range) == ("138", "mEq/L", "135-145")

    def test_declines_on_a_narrative_block(self):
        # "Test name" / "Result: X unit" / "Reference Interval: Y" — not a column
        # table; the geometry pass must return None so the caller falls back.
        rows = table.extract_rows_from_word_rows(
            [
                R(("Follicle", 55), ("Stimulating", 130), ("Hormone", 240)),
                R(("Result:", 55), ("6.2", 130), ("mIU/mL", 175)),
                R(("Reference", 55), ("Interval:", 140), ("1.5-12.4", 230)),
            ],
            "page 1",
        )
        assert rows is None
