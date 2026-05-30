"""
agent/context_classifier.py
Replaces both the old context_classifier.py and context_router.py.

Single GPT-4o-mini call classifies question intent and retrieval profile.
Python owns all gating logic, message generation, and whitelist validation.
LLM output is treated as untrusted — every field is whitelisted before use.
Fail-open design: any API error or parse failure returns proceed=True so the
user is never blocked by a classifier failure.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

from agent.context_bundle import ContextBundle

load_dotenv(Path(__file__).parent.parent / ".env")

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """\
You are a routing classifier for an astrology AI agent.

Your job: read the user's question and return a JSON object that tells the system
what kind of question this is and what context would best answer it.

You will receive:
- The current question
- Optionally: the previous question and the first part of the previous answer
  (for context when the current question references "this", "it", "the problem", etc.)

Return ONLY valid JSON. No markdown, no explanation, no preamble.

OUTPUT CONTRACT
{
  "retrieval_profile": "vedic" | "palmistry" | "lal_kitab" | "all",
  "context_order": [ordered subset of: "kundali", "own_pdf", "spouse_pdf",
                    "palm_left", "palm_right", "hand_detail", "rag"],
  "needs_required": [subset of: "own_pdf", "palm"],
  "needs_enriching": [subset of: "spouse_pdf", "hand_detail"]
}

FIELD RULES

retrieval_profile — choose ONE:
  "vedic"     → birth chart, planets, yogas, dashas, houses, personality,
                 destiny, karma, relationships from chart perspective,
                 general life patterns. DEFAULT — when uncertain, return this.
  "palmistry" → hand lines, mounts, markings, what the hand reveals,
                 palm reading request.
  "lal_kitab" → remedies, solutions, avoiding bad outcomes, what to do about
                 a problem, how to reduce suffering, how to fix something.
                 Route here when the user wants a fix, not just an explanation.
  "all"       → question explicitly involves the user AND their spouse/partner,
                 OR requires cross-domain synthesis across chart + palm + remedies.

context_order — ordered list, most important first, relevant sources only:
  "kundali"     → birth chart data
  "own_pdf"     → user's AstroSage annual report (time-bound predictions)
  "spouse_pdf"  → spouse's AstroSage annual report
  "palm_left"   → left hand reading (potential, inherited traits)
  "palm_right"  → right hand reading (developed path, current life)
  "hand_detail" → detailed hand photograph analysis
  "rag"         → classical text passages from the corpus

needs_required — ONLY when the question CANNOT be answered without this context:
  "palm"    → ONLY when retrieval_profile is "palmistry" AND no palm described
  "own_pdf" → ONLY when question asks about a specific time period, current year,
              near-future predictions, or "what will happen" (not "will I ever")

needs_enriching — context that improves the answer but is not blocking:
  "spouse_pdf"  → question involves the user's spouse or partner
  "hand_detail" → palmistry question where a detailed hand photo adds precision

REASONING PRINCIPLES

1. Semantic intent, not surface words. Infer meaning from the full question and
   prior context. Never match on keywords alone.

2. When prior context exists and the current question uses "this", "it", "the problem",
   "that", "same issue" — treat the current question as a continuation of the prior topic.
   Inherit the topic domain (vedic / palmistry / lal_kitab) from the prior exchange
   unless the current question clearly shifts domain.

3. "We", "my husband", "my wife", "my partner", "both of us" → add "spouse_pdf"
   to needs_enriching and set retrieval_profile to "all".

4. Time-bound triggers for needs_required: ["own_pdf"]:
   YES → "what will happen this year", "2025", "2026", "next few months",
         "current period", "right now in my life", "these days"
   NO  → "will I ever", "in my lifetime", "generally", "by nature"

5. Remedy intent triggers lal_kitab even without the word "remedy":
   "how to reduce", "what should I do", "how to avoid", "what helps",
   "is there a solution", "how can I fix", "what can I do about" → lal_kitab
   when the topic is a problem, malefic planet, or difficult life situation.

6. If uncertain between two profiles → return "vedic". Never return "all"
   as a fallback for uncertainty.

7. needs_required is a HARD BLOCK. Only set it when the question is completely
   unanswerable without that context. When in doubt → needs_enriching.\
"""

# Python-side message templates — LLM never generates these.
_NUDGE_MESSAGES: dict[str, str] = {
    "spouse_pdf":  "Uploading your spouse's AstroSage PDF will allow me to give you a more personalised reading for both of you.",
    "hand_detail": "A clearer photo of your full hand will help me read the finer lines and markings more accurately.",
}

_REQUIRED_MESSAGES: dict[str, str] = {
    "palm":    "Please share a photo of your palm using the sidebar so I can read your hand lines.",
    "own_pdf": "Please upload your AstroSage PDF using the sidebar so I can answer questions about your current period.",
    "both":    "Please upload your AstroSage PDF and a photo of your palm using the sidebar.",
}

_VALID_PROFILES:     frozenset[str] = frozenset({"vedic", "palmistry", "lal_kitab", "all"})
_VALID_ORDER_SLOTS:  frozenset[str] = frozenset({"kundali", "own_pdf", "spouse_pdf", "palm_left", "palm_right", "hand_detail", "rag"})
_VALID_REQUIRED:     frozenset[str] = frozenset({"own_pdf", "palm"})
_VALID_ENRICHING:    frozenset[str] = frozenset({"spouse_pdf", "hand_detail"})

_FAIL_OPEN: dict = {
    "proceed":           True,
    "hard_block":        False,
    "blocked_on":        None,
    "retrieval_profile": "vedic",
    "context_order":     ["kundali", "rag"],
    "needs_enriching":   [],
    "nudges":            [],
    "required_message":  None,
}


def classify(
    question: str,
    bundle: ContextBundle,
    last_user_q: str | None = None,
    last_assistant_answer: str | None = None,
) -> dict:
    """
    Classify question intent via a single GPT-4o-mini call.

    LLM determines: retrieval_profile, context_order, needs_required, needs_enriching.
    Python applies: whitelist validation, gating logic, message generation.

    Args:
        question:              Current user question.
        bundle:                ContextBundle with all available context flags.
        last_user_q:           Previous turn's user question (optional, for continuity).
        last_assistant_answer: Previous turn's assistant answer (optional, first 150 chars used).

    Returns:
        {
            "proceed":           bool,        # False only on hard_block
            "hard_block":        bool,
            "blocked_on":        str | None,  # "palm" | "own_pdf" | "both" | None
            "retrieval_profile": str,
            "context_order":     list[str],
            "needs_enriching":   list[str],
            "nudges":            list[str],   # Python-generated from _NUDGE_MESSAGES
            "required_message":  str | None,  # Python-generated from _REQUIRED_MESSAGES
        }

    Fail-open: any exception returns _FAIL_OPEN so the user is never blocked
    by a classifier error.
    """
    try:
        # ── a. Build user message ─────────────────────────────────────────────
        user_msg = f"CURRENT QUESTION:\n{question}"
        if last_user_q and last_assistant_answer:
            user_msg += (
                f"\n\nPRIOR EXCHANGE (for context only):\n"
                f"User asked: {last_user_q}\n"
                f"Assistant answered: {last_assistant_answer[:150]}..."
            )

        # ── b. GPT-4o-mini call ───────────────────────────────────────────────
        client = OpenAI()
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user",   "content": user_msg},
            ],
            temperature=0,
            max_tokens=120,
        )
        raw = response.choices[0].message.content

        # ── c. Parse JSON ─────────────────────────────────────────────────────
        parsed = json.loads(raw)

        # ── d. Whitelist all LLM output fields ────────────────────────────────
        retrieval_profile = parsed.get("retrieval_profile", "vedic")
        if retrieval_profile not in _VALID_PROFILES:
            retrieval_profile = "vedic"

        context_order = [
            slot for slot in parsed.get("context_order", [])
            if slot in _VALID_ORDER_SLOTS
        ]
        if not context_order:
            context_order = ["kundali", "rag"]

        needs_required = [
            item for item in parsed.get("needs_required", [])
            if item in _VALID_REQUIRED
        ]

        needs_enriching = [
            item for item in parsed.get("needs_enriching", [])
            if item in _VALID_ENRICHING
        ]

        # ── e. Python-side override: spouse_pdf enriching → profile = "all" ──
        if "spouse_pdf" in needs_enriching and retrieval_profile != "all":
            retrieval_profile = "all"

        # ── f. Python-side gating using bundle.availability_map ──────────────
        avail = bundle.availability_map

        palm_needed   = "palm" in needs_required
        pdf_needed    = "own_pdf" in needs_required
        palm_missing  = not avail["palm_left"] and not avail["palm_right"]
        pdf_missing   = not avail["own_pdf"]

        hard_block = False
        blocked_on: str | None = None

        if palm_needed and palm_missing and pdf_needed and pdf_missing:
            hard_block = True
            blocked_on = "both"
        elif palm_needed and palm_missing:
            hard_block = True
            blocked_on = "palm"
        elif pdf_needed and pdf_missing:
            hard_block = True
            blocked_on = "own_pdf"

        # Remove enriching items already present in bundle.
        needs_enriching = [e for e in needs_enriching if not avail.get(e, False)]

        # ── h. Build return dict ──────────────────────────────────────────────
        nudges = [_NUDGE_MESSAGES[e] for e in needs_enriching if e in _NUDGE_MESSAGES]
        required_message = _REQUIRED_MESSAGES.get(blocked_on) if hard_block else None

        return {
            "proceed":           not hard_block,
            "hard_block":        hard_block,
            "blocked_on":        blocked_on,
            "retrieval_profile": retrieval_profile,
            "context_order":     context_order,
            "needs_enriching":   needs_enriching,
            "nudges":            nudges,
            "required_message":  required_message,
        }

    except Exception:
        logger.warning(
            "context_classifier.classify: failed for question=%r — failing open",
            question,
        )
        return dict(_FAIL_OPEN)
