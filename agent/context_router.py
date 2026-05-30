"""
agent/context_router.py
Classify question intent and return the optimal context_order for prompt assembly.
Pure function — no external dependencies, no side effects.
"""

from __future__ import annotations


def route(
    question: str,
    has_kundali: bool,
    has_pdf: bool,
    has_palm: bool,
    low_confidence: bool = False,
) -> dict:
    """
    Classify question intent and return context priority order.

    Args:
        question:       User question string.
        has_kundali:    True if a birth chart context is loaded.
        has_pdf:        True if AstroSage PDF context is loaded.
        has_palm:       True if a palm description is loaded.
        low_confidence: Reserved — no longer used; kept for caller compatibility.

    Returns:
        {
            "context_order": list[str],  # Priority order for prompt assembly
        }
    """
    if not question or not question.strip():
        return {"context_order": ["rag", "kundali", "pdf"]}

    q_lower = question.lower()

    # Substring match covers multi-word keywords (e.g. "sade sati", "lal kitab").
    is_time = any(kw in q_lower for kw in {
        "year", "months", "forecast", "annual", "transit",
        "varshaphal", "muntha", "sade sati", "lal kitab",
        "2025", "2026", "predictions",
    })
    is_palm = any(kw in q_lower for kw in {
        "health", "life", "longevity", "marriage", "children",
        "love", "career", "fate", "success", "wealth", "rich", "money",
    })

    if is_time and is_palm:
        context_order = ["pdf", "palm", "kundali", "rag"]
    elif is_time:
        context_order = ["pdf", "kundali", "rag"]
    elif is_palm:
        context_order = ["palm", "kundali", "rag"]
    else:
        context_order = ["rag", "kundali", "pdf"]

    return {"context_order": context_order}
