"""Rebuild text from word bounding boxes, preserving column gaps.

Outside labs send ruled tables. ``pdfplumber.extract_text()`` and a raw OCR dump
both collapse the wide horizontal gaps between table columns to a single space,
which destroys the one signal the rule-based parsers key on ("2+ spaces = a
column boundary"). This reconstructs each line from word positions and turns a
wide gap back into multiple spaces.

Lifted from the research prototype's ``pipeline._reconstruct_layout_text`` with
no behavioural change.
"""

from collections.abc import Iterable
from typing import TypedDict


class Word(TypedDict):
    text: str
    x0: float
    x1: float
    top: float


def reconstruct_layout_text(words: Iterable[Word]) -> str:
    words = list(words)
    if not words:
        return ""

    # Group into lines by vertical position (4pt buckets), left to right.
    words.sort(key=lambda w: (round(w["top"] / 4), w["x0"]))
    lines: list[list[Word]] = []
    cur_top: int | None = None
    cur: list[Word] = []
    for w in words:
        bucket = round(w["top"] / 4)
        if cur_top is None or bucket == cur_top:
            cur.append(w)
            cur_top = bucket
        else:
            lines.append(cur)
            cur = [w]
            cur_top = bucket
    if cur:
        lines.append(cur)

    return "\n".join(render_line(line) for line in lines)


def render_line(words: list[Word]) -> str:
    """Join one line of words left-to-right, turning a wide horizontal gap back
    into multiple spaces so the "2+ spaces = column boundary" rule still fires.
    """
    if not words:
        return ""
    line = sorted(words, key=lambda w: w["x0"])
    parts = [line[0]["text"]]
    for prev, nxt in zip(line, line[1:]):
        gap = nxt["x0"] - prev["x1"]
        n_spaces = 1 if gap < 8 else max(2, int(gap / 4))
        parts.append(" " * n_spaces + nxt["text"])
    return "".join(parts)
