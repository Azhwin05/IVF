"""Test-name normalization: curated alias table, exact match only.

Ported from the research prototype. The rule that matters clinically: fuzzy or
semantic matching is **never** auto-applied to a test's identity. An exact alias
hit rewrites the name; anything less only produces a suggestion string for the
human reviewer, and the extracted name is left untouched.

The alias table is a small seed for the clinic's common panels (CBC, hormone,
biochem, semen analysis). A real deployment extends it per outsourced-lab
template and, where useful, attaches a LOINC code.
"""

import difflib
import re

from app.laboratory.models import NormalizationMatch

ALIASES: dict[str, str] = {
    "hb": "Hemoglobin", "hgb": "Hemoglobin", "hemoglobin": "Hemoglobin",
    "wbc": "White Blood Cell Count", "tlc": "White Blood Cell Count",
    "rbc count": "Red Blood Cell Count", "rbc": "Red Blood Cell Count",
    "platelet count": "Platelet Count", "platelets": "Platelet Count",
    "hematocrit": "Hematocrit", "hct": "Hematocrit",
    "mcv": "Mean Corpuscular Volume",
    "neutrophils": "Neutrophils", "lymphocytes": "Lymphocytes",
    "fsh": "Follicle Stimulating Hormone",
    "follicle stimulating hormone": "Follicle Stimulating Hormone",
    "lh": "Luteinizing Hormone", "luteinizing hormone": "Luteinizing Hormone",
    "prolactin": "Prolactin",
    "tsh": "Thyroid Stimulating Hormone",
    "amh": "Anti-Mullerian Hormone", "anti-mullerian hormone": "Anti-Mullerian Hormone",
    "estradiol (e2)": "Estradiol", "estradiol": "Estradiol", "e2": "Estradiol",
    "progesterone": "Progesterone",
    "beta hcg": "Beta hCG", "b-hcg": "Beta hCG",
    "free t4": "Free Thyroxine (Free T4)",
    "vitamin d (25-oh)": "Vitamin D (25-Hydroxy)",
    "vitamin b12": "Vitamin B12",
    "ferritin": "Ferritin",
    "fasting blood sugar": "Fasting Blood Glucose",
    "hba1c": "Glycated Hemoglobin (HbA1c)",
    "total cholesterol": "Total Cholesterol",
    "creatinine": "Creatinine",
    "sodium": "Sodium",
    "hiv (elisa)": "HIV Antibody (ELISA)",
    "hbsag": "Hepatitis B Surface Antigen (HBsAg)",
    "urine sugar": "Urine Glucose",
    "urine albumin": "Urine Albumin",
    "blood group": "Blood Group & Rh Type",
    "volume": "Semen Volume",
    "sperm concentration": "Sperm Concentration",
    "total motility": "Total Sperm Motility",
    "progressive motility": "Progressive Sperm Motility",
    "normal morphology": "Normal Sperm Morphology (%)",
    # Common CBC / biochemistry / LFT panel names. Recognised as exact tests so
    # they no longer produce a misleading fuzzy "did you mean" suggestion
    # (Basophils -> Neutrophils, HDL -> Total Cholesterol, ...). Mapped to
    # themselves where there is no established shorter canonical, and any
    # specimen / method qualifier ("Serum ...", "(Calculated)", "(1st hour)") is
    # kept — it is clinically meaningful.
    "haemoglobin": "Hemoglobin",  # British -> the spelling already used above
    "total leucocyte count": "White Blood Cell Count",
    "total leucocyte count (tlc)": "White Blood Cell Count",
    "total leukocyte count": "White Blood Cell Count",
    "eosinophils": "Eosinophils",
    "monocytes": "Monocytes",
    "basophils": "Basophils",
    "esr": "ESR", "esr (1st hour)": "ESR (1st hour)",
    "erythrocyte sedimentation rate": "ESR",
    "blood urea": "Blood Urea", "urea": "Blood Urea",
    "serum creatinine": "Serum Creatinine",
    "uric acid": "Uric Acid", "serum uric acid": "Serum Uric Acid",
    "triglycerides": "Triglycerides",
    "hdl cholesterol": "HDL Cholesterol",
    "ldl cholesterol": "LDL Cholesterol",
    "ldl cholesterol (calculated)": "LDL Cholesterol (Calculated)",
    "sgot": "SGOT (AST)", "sgot (ast)": "SGOT (AST)", "ast": "SGOT (AST)",
    "sgpt": "SGPT (ALT)", "sgpt (alt)": "SGPT (ALT)", "alt": "SGPT (ALT)",
    "alkaline phosphatase": "Alkaline Phosphatase", "alp": "Alkaline Phosphatase",
    "total bilirubin": "Total Bilirubin",
    "direct bilirubin": "Direct Bilirubin",
    "fasting blood glucose": "Fasting Blood Glucose",
}


def normalize_test_name(raw_name: str) -> tuple[str | None, NormalizationMatch]:
    """Return ``(canonical_name, match)`` — ``canonical_name`` is ``None`` unless
    the lowercased name is an exact alias. Fuzzy matches are never returned here.
    """
    key = (raw_name or "").strip().lower()
    if key in ALIASES:
        return ALIASES[key], NormalizationMatch.exact_alias
    return None, NormalizationMatch.unmatched


def _stem(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", s.lower())


def suggest_candidates(raw_name: str, limit: int = 3) -> list[str]:
    """Canonical names that *look* close to ``raw_name`` — only when they
    plausibly ARE the same test. A pure ``difflib`` ratio is not enough: two
    names that merely share a trailing word ("HDL Cholesterol" vs "Total
    Cholesterol") or a suffix ("Basophils" vs "Neutrophils") score high but are
    different tests, so a shared leading stem (or one name contained in the
    other) is also required. Never used to auto-fill a name.
    """
    raw = (raw_name or "").strip().lower()
    if not raw:
        return []
    raw_stem = _stem(raw)
    keys = list(ALIASES.keys())
    matches = difflib.get_close_matches(raw, keys, n=limit * 4, cutoff=0.72)

    seen: set[str] = set()
    out: list[str] = []
    for m in matches:
        m_stem = _stem(m)
        same_head = raw_stem[:3] and raw_stem[:3] == m_stem[:3]
        contained = (len(m) >= 4 and m in raw) or (len(raw) >= 4 and raw in m)
        if not (same_head or contained):
            continue
        canonical = ALIASES[m]
        if canonical not in seen:
            seen.add(canonical)
            out.append(canonical)
        if len(out) >= limit:
            break
    return out
