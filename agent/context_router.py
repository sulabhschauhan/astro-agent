"""
agent/context_router.py
Classify context gaps in a user query and return an advisory nudge.
Pure function — no external dependencies, no side effects.
"""

from __future__ import annotations

# Keywords indicating the user would benefit from AstroSage PDF transit/forecast data.
_PDF_TOPICS: frozenset[str] = frozenset({
    "year", "months", "forecast", "annual", "transit",
    "varshaphal", "muntha", "sade sati", "lal kitab",
    "2025", "2026", "predictions",
})

# Keywords indicating the user would benefit from palm description context.
_PALM_TOPICS: frozenset[str] = frozenset({
    "health", "life", "longevity", "marriage", "children",
    "love", "career", "fate", "success", "wealth", "rich", "money",
})


def route(
    question: str,
    has_kundali: bool,
    has_pdf: bool,
    has_palm: bool,
    low_confidence: bool = False,
) -> dict:
    """
    Classify context gaps and return an advisory nudge.

    Args:
        question:       User question string.
        has_kundali:    True if a birth chart context is loaded.
        has_pdf:        True if AstroSage PDF context is loaded.
        has_palm:       True if a palm description is loaded.
        low_confidence: True if top retrieval score is below threshold.

    Returns:
        {
            "needs_pdf":  bool,      # PDF topic matched but PDF not yet uploaded
            "needs_palm": bool,      # Palm topic matched but palm not yet provided
            "nudge":      str|None,  # Ready-to-pass st.info() text; None if not needed
        }
    """
    if not question or not question.strip():
        return {"needs_pdf": False, "needs_palm": False, "nudge": None, "context_order": ["rag", "kundali", "pdf"]}

    q_lower = question.lower()

    # Substring match covers multi-word keywords (e.g. "sade sati", "lal kitab").
    pdf_match  = any(kw in q_lower for kw in _PDF_TOPICS)
    palm_match = any(kw in q_lower for kw in _PALM_TOPICS)

    needs_pdf  = pdf_match  and not has_pdf
    needs_palm = palm_match and not has_palm

    nudge = _build_nudge(
        needs_pdf=needs_pdf,
        needs_palm=needs_palm,
        low_confidence=low_confidence,
        has_any_context=has_kundali or has_pdf or has_palm,
    )

    is_time = pdf_match
    is_palm = palm_match
    if is_time and is_palm:
        context_order = ["pdf", "palm", "kundali", "rag"]
    elif is_time:
        context_order = ["pdf", "kundali", "rag"]
    elif is_palm:
        context_order = ["palm", "kundali", "rag"]
    else:
        context_order = ["rag", "kundali", "pdf"]

    return {"needs_pdf": needs_pdf, "needs_palm": needs_palm, "nudge": nudge, "context_order": context_order}


# ─── Internal helper ──────────────────────────────────────────────────────────

def _build_nudge(
    needs_pdf: bool,
    needs_palm: bool,
    low_confidence: bool,
    has_any_context: bool,
) -> str | None:
    """Compose a single advisory message from detected context gaps."""
    parts: list[str] = []

    if needs_pdf:
        parts.append("Upload your AstroSage PDF for a detailed year-ahead forecast")
    if needs_palm:
        parts.append("Share a photo of your palm for a more personal reading")
    if low_confidence and not parts and has_any_context:
        # Confidence is low but no specific gap — suggest rephrasing.
        parts.append("Try rephrasing your question for a sharper match from the texts")

    if not parts:
        return None

    msg = "; ".join(parts)
    return msg if msg.endswith(".") else msg + "."
