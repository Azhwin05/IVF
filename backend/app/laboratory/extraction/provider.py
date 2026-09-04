"""Extraction provider seam.

The deterministic pipeline (PDF text / OCR + rule-based parsers) is the default
and only wired-in provider. AI-assisted extraction — a vision LLM or a cloud
Document AI processor given the page image and a strict schema — is expected
because outsourced reports vary so much, but no provider is configured here.

``AIExtractionProvider`` is the plug point. It raises ``NotImplementedError`` on
purpose: a stubbed "AI" response that returned plausible-looking values would
violate the never-fabricate rule more dangerously than an honest failure,
because it would look real. Wire a real provider in before enabling
``LAB_AI_EXTRACTION_ENABLED``.
"""

from __future__ import annotations

from typing import Protocol

from app.core.config import Settings
from app.laboratory.extraction.dto import ExtractedRow


class AIExtractionProvider(Protocol):
    """Given one page rendered to PNG bytes, return rows the model actually read.

    Implementations must set a real confidence reported by the provider (never
    invented) and must return ``[]`` for a page they cannot read — never guesses.
    """

    def extract_page(self, page_png: bytes, page_number: int) -> list[ExtractedRow]:
        ...


class UnconfiguredAIProvider:
    """Placeholder until a provider is selected and credentials exist."""

    def extract_page(self, page_png: bytes, page_number: int) -> list[ExtractedRow]:
        raise NotImplementedError(
            "No AI extraction provider is configured. This is a deliberate stub. "
            "Wire a real vision-LLM or Document AI provider here before enabling "
            "LAB_AI_EXTRACTION_ENABLED."
        )


def get_ai_provider(settings: Settings) -> AIExtractionProvider | None:
    """Return the configured AI provider, or ``None`` when AI extraction is off.

    Today this always returns ``None`` (or the unconfigured stub when the flag is
    set without a provider), so :func:`extract_document` stays deterministic.
    """
    if not settings.LAB_AI_EXTRACTION_ENABLED:
        return None
    return UnconfiguredAIProvider()
