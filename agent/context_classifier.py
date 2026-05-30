"""
agent/context_classifier.py
LLM-based context gap classifier. Single GPT-4o-mini call to determine
what additional context (palm, pdf) is needed before the main answer call.

Fail-open design: on any API or parse error, returns proceed=True so the
user is never blocked by a classifier failure. The downstream astrologer.py
will answer as best it can with whatever context is already available.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv(Path(__file__).parent.parent / ".env")

logger = logging.getLogger(__name__)

# GPT classifies question topic only — no knowledge of what has been uploaded.
# Principle-based prompt: no keyword lists, semantic decision framework only.
_SYSTEM_PROMPT = """\
Classify the user's astrology question intent.
Return only valid JSON, no markdown: {"intent": [...]}

Return {"intent": ["pdf"]} ONLY when the question is time-bound — the user is asking about their current situation, a specific time period, or near-future trajectory where the answer would change depending on when it is asked. "Will I ever" questions are NOT time-bound.

Return {"intent": ["palm"]} ONLY when the user is asking about physical features of their hand — lines, mounts, markings, or a palmistry reading.

Return {"intent": []} for everything else: personality, life patterns, relationships, wealth potential, career nature, general destiny. These are answered from the birth chart alone.\
"""

# Python-side message templates — GPT never generates these.
_MESSAGES = {
    "palm": "Please share a photo of your palm using the sidebar on the left.",
    "pdf":  "Please upload your AstroSage PDF using the sidebar on the left.",
    "both": "Please upload your palm photo and AstroSage PDF using the sidebar on the left.",
}


def classify_context(
    question: str,
    has_kundali: bool,
    has_pdf: bool,
    has_palm: bool,
) -> dict:
    """
    Classify context gaps via a single GPT-4o-mini call.

    Separation of concerns:
    - GPT classifies question intent only (what the question is about), receiving
      only the question text. It has no knowledge of has_palm or has_pdf, which
      prevents it from misinterpreting boolean flags embedded in freetext.
    - Python applies the gate deterministically: an intent item becomes a need
      only when the corresponding context is absent (has_palm / has_pdf).
    - Upload prompt messages are Python-generated templates, not LLM output.

    Returns:
        {
            "proceed": bool,        # True when no uploads are needed
            "needs":   list[str],   # subset of ["palm", "pdf"]
            "message": str | None,  # friendly upload prompt; None when proceed=True
        }

    Fail-open: any API error, timeout, or JSON parse failure returns
    {"proceed": True, "needs": [], "message": None} so the user is never
    blocked by a classifier error. The main astrologer call proceeds and
    answers with whatever context is already available.
    """
    try:
        client = OpenAI()
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": question},
            ],
            temperature=0,
            max_tokens=60,
        )
        raw = response.choices[0].message.content
        parsed = json.loads(raw)

        # Whitelist guard — only recognised intent values pass through.
        intent = [i for i in parsed.get("intent", []) if i in ("palm", "pdf")]

        # Python gate — booleans stay out of GPT's hands entirely.
        needs = [
            i for i in intent
            if (i == "palm" and not has_palm) or (i == "pdf" and not has_pdf)
        ]

        if not needs:
            return {"proceed": True, "needs": [], "message": None}

        message = _MESSAGES["both"] if len(needs) == 2 else _MESSAGES[needs[0]]
        return {"proceed": False, "needs": needs, "message": message}

    except Exception:
        logger.warning(
            "context_classifier: GPT-4o-mini call failed for question=%r — failing open",
            question,
        )
        return {"proceed": True, "needs": [], "message": None}
