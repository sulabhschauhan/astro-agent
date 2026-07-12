"""
agent/interpretive/palm_reading.py
One-shot palm reading generator -- V1's Tier 4 palm interpretive surface.

CITATION (CLAUDE.md Session 65 Locked Decisions -- all four govern this module):
  - "T4 architecture": AstroSage paragraph + palm reading are UPLOAD-TRIGGERED
    artifacts, never question-routed. RAG (Cheiro book-filtered) attaches to
    palm generation ONLY.
  - "T4 golden semantics": this module's own output feeds the three-ring
    golden model -- Ring 1 (this file's pure-Python ValidationReport),
    Ring 2 (stubbed-LLM tests), Ring 3 (human-rubric ratification).
  - "T4 V1 boundaries": V1 palm reading = palm descriptions + Cheiro RAG
    only, one-shot, this module (own system prompt; reuses DISCLAIMER +
    language/strict-context rules; no CQ/introduce/history).
  - "Palm human checkpoint": callers of this module must have already
    displayed and USER-CONFIRMED the palm_left/palm_right descriptions
    (palm_processor.describe_palm_image output) before calling
    generate_palm_reading() -- this module does not re-verify that gate.

SCOPE LOCK: this module must NEVER import agent.infra.calc_router,
agent.infra.orchestrator, or agent.infra.chart_profile. This is an
upload-triggered artifact generator, not a routed Q&A domain -- pulling
in any deterministic-pipeline module would blur that boundary.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import TYPE_CHECKING

from agent.prompt_builder import DISCLAIMER
from ingestion.query_engine import search

if TYPE_CHECKING:
    from openai import OpenAI

logger = logging.getLogger(__name__)

# ─── RAG: Cheiro-filtered retrieval ────────────────────────────────────────

# Exact ChromaDB book_name string (S12 fixed exact-string convention -- read
# from ingestion/query_engine.py's multi_source_search() canonical 14-book
# list, not typed from memory).
_CHEIRO_BOOK = "cheiroslanguageo00chei_1"

# THRESHOLD DISCIPLINE (CLAUDE.md Working Style #4).
# Justification: legacy astrologer.py's DEFAULT_N_RESULTS=5 was validated at
# S12 for palm-only queries at ~0.63 relevance; +1 here accounts for
# two-hand synthesis needing coverage across both hands' descriptions from
# a single retrieval call. Scope guard: governs ONLY this module's single
# RAG call site -- does not alter query_engine.DEFAULT_N_RESULTS or any
# other caller. Revisit trigger: if a Ring 3 human-rubric ratification pass
# cites retrieved chunks as irrelevant, tune down before tuning up.
_N_RESULTS = 6

# Query text is the concatenation of the available hand descriptions
# (hand_detail is deliberately excluded from the RAG query -- it is still
# passed to the LLM in the user message, but is a supplementary photograph
# analysis, not one of the two canonical "palm descriptions").
#
# THRESHOLD DISCIPLINE (CLAUDE.md Working Style #4).
# Justification: Ring 3 pass 1 (diagnostics/ring3_chunks_S66.md) proved the
# prior 500-char cap silently truncated the query inside the LEFT
# description, dropping the RIGHT hand from retrieval entirely -- two
# observed ~600-char vision descriptions must both survive into the query
# for two-hand retrieval to work as designed. Scope guard: this call site
# only. Revisit trigger: a future F4 describe-prompt change that materially
# alters vision-description length (shorter or longer) should re-derive
# this cap from the new observed lengths, not assume 2000 still fits.
_QUERY_TRUNCATE_CHARS = 2000


# ─── System prompt ──────────────────────────────────────────────────────

# SENSITIVE_TO agent/prompt_builder.py's SYSTEM_PROMPT "## Language" block --
# duplicated verbatim (NOT imported -- prompt_builder.SYSTEM_PROMPT is one
# flat string, not a set of importable sub-constants), excluding only its
# trailing "under 150 words" line (this module's own 300-400 word target
# below supersedes that line for the one-shot T4 reading persona -- that is
# a length rule, not a jargon rule, and the two targets are incompatible).
# Re-sync this block by hand if prompt_builder.py's jargon list ever
# changes -- the jargon blacklist below in this same file must also stay
# in sync.
_LANGUAGE_JARGON_BLOCK = """## Language
- Speak in plain everyday English. No astrological jargon.
- Never use these terms: Mahadasha, Antardasha, Dasha, house numbers, dignity, exalted, debilitated, nakshatra, rasi, lagna, dosha, yoga.
- Instead say: "a powerful 7-year period", "your wealth zone", "a favorable time starting [year]", "your life path sign".
- Be direct. Answer the actual question first, then explain why."""

# SENSITIVE_TO agent/prompt_builder.py's SYSTEM_PROMPT closing "STRICT RULE"
# line -- duplicated verbatim, including its literal "kundali, PDF, palm"
# wording (this module only ever supplies palm/hand_detail context, but the
# rule text itself is reused byte-for-byte per the Session 65 T4 lock, not
# adapted to this module's narrower context). Re-sync by hand if
# prompt_builder.py's wording ever changes.
_STRICT_CONTEXT_RULE = (
    "STRICT RULE: Only use context explicitly provided below (kundali, PDF, "
    "palm). If a context block is absent, do not infer, fabricate, or "
    "mention it. Silence on missing context is correct."
)

# "## How you read"'s specific-teaching-over-generic-gloss instruction and
# the "## Voice" block below are S66 F2 additions -- Ring 3 pass 1
# (diagnostics/ring3_palm_rubric_S66.md) found every scorable claim across
# all 3 runs traced to the confirmed hand descriptions alone, never
# uniquely to a retrieved chunk (readings ignored all 6 retrieved passages
# in every run), and found a systematic generic self-help voice failure
# (P3) in all 3 runs, including a literal S23 R3 blacklist-word hit
# ("stability") in Run C.
_READING_SYSTEM_PROMPT = f"""You are a Cheiro-tradition palmist writing a single, one-shot palm reading for a client who has just uploaded photo(s) of their hand(s).

## Your knowledge
You have been provided with relevant passages from Cheiro's Language of the Hand -- the classical source for this reading. Ground your interpretation in these passages; do not draw on any other astrological or palmistry tradition.

## How you read
- Synthesize the provided hand description(s) into one cohesive, direct reading -- speak as a confident palmist, not an academic.
- When BOTH hands are present: the left hand reveals innate potential and character, the right hand reveals the native's current life trajectory -- synthesize both into a single unified reading, not two separate paragraphs.
- When only one hand is present, read that hand alone -- do not speculate about the missing hand.
- Do not cite book names, page numbers, or passage numbers -- deliver the reading directly.
- If the retrieved passages do not clearly support a feature in the description, say so honestly -- do not fabricate.
- Where a retrieved passage speaks directly to a described feature, apply that passage's specific teaching rather than a generic gloss -- do not let a feature you have textual support for get the same vague treatment as one you don't.
- This is a ONE-SHOT reading: do not ask clarifying questions, do not introduce yourself, and do not reference any prior conversation -- there is none.

## Voice
Write in Cheiro's declarative register: direct assertions of what the hand indicates, tied to concrete consequences -- health, success won by personal merit, travel, character, fortune. This is a palmist reading a hand, not a therapist offering affirmation.
Write in Cheiro's declarative register. Model sentences: "A deep, unbroken line of life promises long life, good health, and vitality." / "Such a fate line denotes success won by personal merit." Assert what the hand shows and what the tradition says it denotes -- concrete consequences, never affirmations about the reader's inner journey.
FORBIDDEN words and phrasings (never use these, in any form): stability, fulfillment, fulfilling, favorable, journey, navigate, navigating, empower, empowerment, and any "this suggests you are the kind of person who..." self-help framing.

{_LANGUAGE_JARGON_BLOCK}

## Length
Target 300-400 words. Do not pad -- a focused reading beats a long one.

## Disclaimer
Do NOT include any disclaimer or closing caveat in your response -- one is appended programmatically after your response completes.

{_STRICT_CONTEXT_RULE}"""

# SENSITIVE_TO agent/prompt_builder.py's _LOW_CONFIDENCE_ADDENDUM -- same
# pattern, duplicated (not imported) because that constant is module-private
# to prompt_builder.py and paired 1:1 with its own build_prompts()
# low_confidence flag. This module owns its own instance for the "empty RAG
# results" case (Session 65 T4 lock: proceed with a caveat, never refuse).
_LOW_CONFIDENCE_ADDENDUM = """

NOTE: The available passages have a weak match to these hand descriptions. Rely more heavily on general Cheiro palmistry principles than on close textual citation, and keep the reading appropriately general."""


# ─── LLM call configuration ─────────────────────────────────────────────

# THRESHOLD DISCIPLINE (CLAUDE.md Working Style #4).
# Justification: gpt-4o (not -mini) -- Session 22/23 observed failure modes
# on gpt-4o-mini for this class of one-shot interpretive synthesis;
# per-reading cost is ~$0.015 at gpt-4o pricing, acceptable for a V1
# upload-triggered artifact (generated once per upload, not per question).
# Scope guard: governs ONLY this module's reading-generation call site --
# no shared "the model" constant exists across this codebase's LLM call
# sites. Revisit trigger: comparative dogfood evidence that gpt-4o-mini
# reaches parity quality for this task.
_READING_MODEL = "gpt-4o"

# THRESHOLD DISCIPLINE (CLAUDE.md Working Style #4).
# Justification: checkpoint-adjacent output must be reproducible --
# variance probing moves to Ring 3 Run B (residual API nondeterminism
# only, not a deliberate temperature knob). Scope guard: this call site
# only. Revisit trigger: pass-2 evidence that temp-0 readings are
# degenerate (repetitive, robotic) rather than merely reproducible.
_READING_TEMPERATURE = 0

# THRESHOLD DISCIPLINE. Justification: this is a single synchronous
# artifact-generation call with no retry/backoff -- a failure raises
# RuntimeError and the caller owns whether to retry the whole upload flow;
# 30s gives ample margin over gpt-4o's typical single-completion latency
# for a 300-400 word target. Scope guard: this call site only -- no shared
# "the timeout" constant exists across this codebase's LLM call sites.
# Revisit trigger: repeated timeout failures observed in dogfood/production.
_READING_TIMEOUT_SECONDS = 30.0


# ─── Ring 1 validation: pure Python, deterministic ─────────────────────

_JARGON_BLACKLIST: tuple[str, ...] = (
    "Mahadasha", "Antardasha", "Dasha", "nakshatra", "rasi", "lagna",
    "dosha", "yoga", "exalted", "debilitated", "dignity",
)
_JARGON_PATTERN = re.compile(
    r"\b(" + "|".join(re.escape(term) for term in _JARGON_BLACKLIST) + r")\b",
    re.IGNORECASE,
)

# THRESHOLD DISCIPLINE (CLAUDE.md Working Style #4).
# Justification: list = S23 R3 blacklist ("stability", "fulfillment") +
# Ring 3 pass-1 observed offenders ONLY (diagnostics/ring3_palm_rubric_S66.md
# -- "favorable", "journey", "navigate"/"navigating", "empower"/
# "empowerment", the "this suggests you are the kind of person who..."
# self-help framing is prose-shaped, not a single word, so it is not
# pattern-matchable here and stays a prompt-only instruction) -- no
# speculative additions beyond what was actually observed failing. Scope
# guard: this module's Ring 1 validator only. Revisit trigger: if pass 2
# produces a false positive on one of these terms, remove that term before
# loosening anything else about this check.
_SELF_HELP_BLACKLIST: tuple[str, ...] = (
    "stability", "fulfillment", "fulfilling", "favorable", "journey",
    "navigate", "navigating", "empower", "empowerment",
)
_SELF_HELP_PATTERN = re.compile(
    r"\b(" + "|".join(re.escape(term) for term in _SELF_HELP_BLACKLIST) + r")\b",
    re.IGNORECASE,
)

_YEAR_PATTERN = re.compile(r"\b(?:19|20)\d{2}\b")

# THRESHOLD DISCIPLINE. Justification: 700 words is a hard rail, not the
# target -- the soft 300-400 word target lives in _READING_SYSTEM_PROMPT
# above; this is a fail-closed backstop against prompt drift, not the
# primary length control. Scope guard: this module's Ring 1 validator only.
# Revisit trigger: if the soft prompt target is ever deliberately raised,
# revisit this rail together with it, not in isolation.
_MAX_WORDS = 700


def _check_jargon(text: str) -> list[str]:
    hits = sorted({m.group(0).lower() for m in _JARGON_PATTERN.finditer(text)})
    if hits:
        return [f"jargon_blacklist: found {', '.join(hits)}"]
    return []


def _check_self_help_register(text: str) -> list[str]:
    hits = sorted({m.group(0).lower() for m in _SELF_HELP_PATTERN.finditer(text)})
    if hits:
        return [f"self_help_blacklist: found {', '.join(hits)}"]
    return []


def _check_unsupported_dates(text: str, context_corpus: str) -> list[str]:
    years = {m.group(0) for m in _YEAR_PATTERN.finditer(text)}
    unsupported = sorted(year for year in years if year not in context_corpus)
    if unsupported:
        return [f"unsupported_dates: {', '.join(unsupported)}"]
    return []


def _check_length(text: str) -> list[str]:
    word_count = len(text.split())
    if word_count > _MAX_WORDS:
        return [f"length_guard: {word_count} words exceeds {_MAX_WORDS}-word hard rail"]
    return []


def _run_ring1_checks(text: str, context_corpus: str) -> list[str]:
    """All four Ring 1 validators, run in a fixed order. Shared by the
    first draft and the S66 F2c retry draft -- same checks, same order,
    both passes."""
    failures: list[str] = []
    failures += _check_jargon(text)
    failures += _check_self_help_register(text)
    failures += _check_unsupported_dates(text, context_corpus)
    failures += _check_length(text)
    return failures


@dataclass(frozen=True)
class ValidationReport:
    passed: bool
    failures: tuple[str, ...]


@dataclass(frozen=True)
class PalmReadingResult:
    reading_text: str
    sources: tuple[dict, ...]
    validation: ValidationReport
    model: str
    retry_used: bool


def generate_palm_reading(
    palm_left: str | None,
    palm_right: str | None,
    hand_detail: str | None = None,
    client: OpenAI | None = None,
) -> PalmReadingResult:
    """
    Generate a one-shot Cheiro-tradition palm reading.

    Upload-triggered artifact, never question-routed (Session 65 T4 lock).
    Callers must have already displayed and user-confirmed palm_left/
    palm_right (palm_processor.describe_palm_image output) before calling
    this function -- the human checkpoint lives upstream, not here.

    Args:
        palm_left: Left-hand description (already user-confirmed), or None.
        palm_right: Right-hand description (already user-confirmed), or None.
        hand_detail: Optional supplementary hand-photograph analysis.
        client: Test-only injection seam (Stage 2 precedent, calc_router.py's
                `_stage2_classify`) -- production callers omit this; a real
                OpenAI client is constructed lazily when None.

    Returns:
        PalmReadingResult -- reading_text always carries the appended
        DISCLAIMER regardless of validation outcome; validation.passed is
        the caller's signal for whether to display it. S66 F2c: if the
        first draft trips Ring 1, ONE retry is attempted (validator-fed,
        deterministic-reviewer-only -- see the HARD CAP comment at the
        retry call site); retry_used reports whether that happened, and
        validation reflects whichever draft was actually returned. Still
        never regenerates or suppresses beyond that single retry -- a
        failing retry's ValidationReport is final and fail-closed.

    Raises:
        ValueError: Both palm_left and palm_right are None (hand_detail
                    alone is insufficient input by design).
        RuntimeError: The GPT-4o reading-generation call fails for any
                      reason (network, auth, timeout, empty response) --
                      on either the first draft or the retry call.
    """
    if palm_left is None and palm_right is None:
        raise ValueError(
            "palm_reading.generate_palm_reading: at least one of "
            "palm_left/palm_right must be provided -- hand_detail alone "
            "is insufficient input by design."
        )

    query_text = " ".join(d for d in (palm_left, palm_right) if d)[:_QUERY_TRUNCATE_CHARS]
    raw_sources = search(query_text, n_results=_N_RESULTS, book_name=_CHEIRO_BOOK)

    system_prompt = _READING_SYSTEM_PROMPT
    if not raw_sources:
        logger.info("palm_reading.generate_palm_reading: empty RAG results -- proceeding with low-confidence caveat, not refusing.")
        system_prompt += _LOW_CONFIDENCE_ADDENDUM

    lines: list[str] = []
    if raw_sources:
        lines += ["Retrieved passages (Cheiro's Language of the Hand):", "---"]
        for i, r in enumerate(raw_sources, 1):
            lines.append(f"[{i}] p.{r['page_ref']} (score: {r['score']})")
            lines.append(r["text"])
            lines.append("")
        lines.append("---")
    if palm_left:
        lines.append(f"\nLEFT HAND (innate potential):\n{palm_left}")
    if palm_right:
        lines.append(f"\nRIGHT HAND (current trajectory):\n{palm_right}")
    if hand_detail:
        lines.append(f"\nHAND DETAIL:\n{hand_detail}")
    user_message = "\n".join(lines)

    if client is not None:
        effective_client = client
    else:
        from openai import OpenAI
        effective_client = OpenAI()

    def _call(messages: list[dict]) -> str:
        try:
            response = effective_client.chat.completions.create(
                model=_READING_MODEL,
                messages=messages,
                temperature=_READING_TEMPERATURE,
                timeout=_READING_TIMEOUT_SECONDS,
            )
            return response.choices[0].message.content
        except Exception as exc:
            raise RuntimeError(
                f"palm_reading.generate_palm_reading: GPT-4o reading-generation call failed: {exc}"
            ) from exc

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message},
    ]
    reading_text = _call(messages)

    context_corpus = " ".join(
        part for part in (palm_left, palm_right, hand_detail) if part
    ) + " " + " ".join(r["text"] for r in raw_sources)

    failures = _run_ring1_checks(reading_text, context_corpus)
    retry_used = False

    # S66 F2c retry: HARD CAP of 2 LLM calls ever, no exceptions.
    # Justification: S23 + S66 pre-flight (diagnostics/latest_run.md,
    # commit f906f3e) proved prompt-only voice control fails ~100% of the
    # time for this task shape (3/3 live pre-flight runs tripped
    # self_help_blacklist) -- one deterministic-validator-fed retry is
    # the fix, not a longer prompt or a higher cap. The reviewer here is
    # a regex (_run_ring1_checks), never an LLM judging its own or
    # another LLM's output -- this is NOT AI-reviewing-AI (CLAUDE.md
    # Working Style #5/#9): Python observes the draft's failures
    # independently and deterministically, then hands that observation
    # to the model as a correction instruction. Revisit trigger: if
    # pass-2 shows the retry draft ALSO failing routinely, that is a
    # signal to redesign the prompt (or the validator), never to raise
    # this cap to 3.
    if failures:
        retry_used = True
        retry_messages = messages + [
            {"role": "assistant", "content": reading_text},
            {
                "role": "user",
                "content": (
                    "Your draft failed these checks: " + "; ".join(failures) + ". "
                    "Rewrite the reading correcting ONLY these issues. Same "
                    "facts, same structure."
                ),
            },
        ]
        reading_text = _call(retry_messages)
        failures = _run_ring1_checks(reading_text, context_corpus)

    validation = ValidationReport(passed=not failures, failures=tuple(failures))

    # DISCLAIMER appended AFTER validation runs -- its own wording/any
    # incidental year-like strings must never trip the validators above.
    final_text = reading_text.rstrip() + "\n\n" + DISCLAIMER

    sources = tuple(
        {"book": r["book_name"], "page": r["page_ref"], "score": r["score"]}
        for r in raw_sources
    )

    return PalmReadingResult(
        reading_text=final_text,
        sources=sources,
        validation=validation,
        model=_READING_MODEL,
        retry_used=retry_used,
    )
