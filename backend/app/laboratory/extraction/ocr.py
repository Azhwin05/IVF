"""OCR for scanned PDFs and image reports — guarded, optional.

``pytesseract`` is a thin wrapper over the system ``tesseract`` binary. Neither
the Python package nor the binary is guaranteed to be present. Every entry point
here raises :class:`OcrUnavailable` when OCR cannot run, and the pipeline turns
that into a failed report with no fabricated rows — it never substitutes blank
or guessed values for a page it could not read.

The binary is located in this order: an explicit ``TESSERACT_CMD`` setting, then
``tesseract`` on ``PATH``, then the standard Windows install locations. On a
Linux container it is expected on ``PATH`` (``apt-get install tesseract-ocr``).
"""

from __future__ import annotations

import os
import shutil
from functools import lru_cache

from app.laboratory.extraction.layout import Word, render_line

# Standard install locations for the UB-Mannheim / upstream Windows builds.
_WINDOWS_CANDIDATES = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    os.path.expandvars(r"%LOCALAPPDATA%\Programs\Tesseract-OCR\tesseract.exe"),
)


class OcrUnavailable(RuntimeError):
    """Raised when OCR is required but pytesseract or Tesseract is not usable."""


@lru_cache(maxsize=1)
def _resolve_tesseract_cmd() -> str | None:
    """Best-effort path to the Tesseract binary, or ``None`` if not found."""
    try:
        from app.core.config import get_settings

        configured = get_settings().TESSERACT_CMD
    except Exception:
        configured = None

    for candidate in (configured, os.environ.get("TESSERACT_CMD")):
        if candidate and os.path.isfile(candidate):
            return candidate

    on_path = shutil.which("tesseract")
    if on_path:
        return on_path

    for candidate in _WINDOWS_CANDIDATES:
        if candidate and os.path.isfile(candidate):
            return candidate

    return None


def _load_pytesseract() -> "object | None":
    try:
        import pytesseract
    except Exception:
        return None
    cmd = _resolve_tesseract_cmd()
    if cmd:
        pytesseract.pytesseract.tesseract_cmd = cmd
    return pytesseract


@lru_cache(maxsize=1)
def ocr_available() -> bool:
    pytesseract = _load_pytesseract()
    if pytesseract is None:
        return False
    try:
        pytesseract.get_tesseract_version()
    except Exception:
        return False
    return True


def _require_ocr() -> "object":
    pytesseract = _load_pytesseract()
    if pytesseract is None:  # pragma: no cover - import environment specific
        raise OcrUnavailable(
            "OCR is not available on this server (pytesseract is not installed)."
        )
    try:
        pytesseract.get_tesseract_version()
    except Exception as exc:
        raise OcrUnavailable(
            "OCR is not available on this server (the Tesseract binary was not found)."
        ) from exc
    return pytesseract


def ocr_word_rows(pil_image: object) -> list[list[Word]]:
    """Run OCR and return the words grouped into rows, keeping their bounding
    boxes. Rows come from Tesseract's own layout analysis
    (``block_num, par_num, line_num``); words within a row are x-sorted. Rows are
    in top-to-bottom reading order.

    This is the geometry-preserving entry point used by
    :mod:`app.laboratory.extraction.table`. Raises :class:`OcrUnavailable` if OCR
    cannot run.
    """
    pytesseract = _require_ocr()
    data = pytesseract.image_to_data(  # type: ignore[attr-defined]
        pil_image, output_type=pytesseract.Output.DICT  # type: ignore[attr-defined]
    )

    lines: dict[tuple[int, int, int], list[Word]] = {}
    line_order: list[tuple[int, int, int]] = []
    for i in range(len(data["text"])):
        txt = data["text"][i].strip()
        if not txt:
            continue
        try:
            if int(data["conf"][i]) < 0:  # -1 == no recognised text
                continue
        except (TypeError, ValueError):
            pass
        key = (
            int(data["block_num"][i]),
            int(data["par_num"][i]),
            int(data["line_num"][i]),
        )
        if key not in lines:
            lines[key] = []
            line_order.append(key)
        lines[key].append(
            {
                "text": txt,
                "x0": float(data["left"][i]),
                "x1": float(data["left"][i] + data["width"][i]),
                "top": float(data["top"][i]),
            }
        )

    line_order.sort(key=lambda k: min(w["top"] for w in lines[k]))
    return [sorted(lines[k], key=lambda w: w["x0"]) for k in line_order]


def ocr_layout_text(pil_image: object) -> str:
    """Run OCR and return layout-preserving text: one line per Tesseract row,
    wide horizontal gaps turned into multiple spaces so the fallback line
    parsers still see column boundaries.

    Raises :class:`OcrUnavailable` if OCR cannot run.
    """
    return "\n".join(render_line(row) for row in ocr_word_rows(pil_image))
