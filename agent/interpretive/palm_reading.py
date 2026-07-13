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

LOCK LIFTED (S67 R1, design chat Conflict A ruling (b)): the S65/S66
"hand_detail excluded from the RAG query" rule is REPEALED. That
rationale (hand_detail was a supplementary photo analysis, not one of
the two canonical palm descriptions) died when F1 (S66) gave
hand_detail the same human-confirmation checkpoint as palm_left/
palm_right -- it is now RAG-extraction-eligible on the same footing.
See the per-feature retrieval section below.

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

# ─── RAG: Cheiro-filtered PER-FEATURE retrieval (S67 R1) ───────────────────
#
# Replaces the single whole-description query (pre-S67: one search() call
# on the concatenated palm_left + palm_right text) with one query per
# OBSERVED canonical hand feature. Ratified in design chat from the S67
# measure-first probe (scripts/probe_r1_retrieval.py,
# diagnostics/latest_run.md as committed by that script, commit 0a738c3):
# the whole-description query mostly returned nomenclature/procedural
# Cheiro text, not per-feature doctrine; per-feature queries using the
# probe's variant (iii) template reliably surfaced the two known-doctrine
# pages (p.134 life-line, p.163 fate-line) where they exist in the corpus.
#
# Field parsing + quality extraction below are PORTED from
# scripts/probe_r1_retrieval.py's _parse_fields/_extract_quality/
# _clean_quality_prefix/_build_feature_map -- same logic, cited not
# reinvented. Two deliberate extensions beyond the probe (which only ever
# read palm_left/palm_right):
#   1. hand_detail is now a THIRD feature-extraction source, parsed with a
#      second regex for its markdown "- **Label**: text" bullet format
#      (describe_hand_detail_image's format differs from F4's flat
#      "LABEL: text" fields -- see the S67 carry-forward flagging this for
#      palm_processor.py's next touch). This is what the LOCK LIFTED note
#      in the module docstring above is about.
#   2. Both field parsers reset the "current field" on a blank line -- the
#      probe's LEFT/RIGHT-only data never had a trailing non-field
#      sentence after the last labeled field, but hand_detail's closing
#      "These are the physical observations..." line does, and would
#      otherwise silently glue onto the last bullet's text.

_CHEIRO_BOOK = "cheiroslanguageo00chei_1"

# THRESHOLD DISCIPLINE (CLAUDE.md Working Style #4).
# Justification: S67 probe (diagnostics/latest_run.md, commit 0a738c3)
# measured the worst doctrine-first-hit rank at 2 across all 8 provable
# features under the ratified variant (iii) template -- +1 margin. Scope
# guard: this module's per-feature call sites only -- does not alter
# query_engine.DEFAULT_N_RESULTS or any other caller. Revisit trigger:
# pass-3 claim ledgers showing support routinely landing at rank 3 -- go
# to 4 before blaming the template.
_N_RESULTS_PER_FEATURE = 3

_FEATURE_REGISTRY: tuple[str, ...] = (
    "life line", "head line", "heart line", "fate line", "sun line",
    "thumb", "fingers", "mount of venus", "mount of jupiter",
    "markings/other features",
)

# THRESHOLD DISCIPLINE (CLAUDE.md Working Style #4).
# Justification: S67 probe-proven -- querying an absence-phrased field
# (e.g. "No clear marks visible") returns junk (markings tables, scores
# 0.33-0.47), not doctrine. A feature is skipped (no query) only when
# EVERY source that mentions it uses one of these phrases; a single
# non-absent mentioning source is enough to proceed to a real query.
# Scope guard: this module's per-feature gate only. Revisit trigger: a
# future pass-3 finding that one of these phrases is itself informative
# for some feature (none observed yet).
_ABSENCE_PHRASES: tuple[str, ...] = (
    "not clearly visible", "no clear marks", "unremarkable",
    "not observed", "not visible", "none",
)

_FIELD_LINE = re.compile(r"^([A-Z][A-Z ]{2,}):\s*(.*)$")
_BULLET_FIELD = re.compile(r"^-\s*\*\*([^*]+)\*\*:\s*(.*)$")


def _parse_fields(block: str) -> dict[str, str]:
    """palm_left/palm_right's flat 'LABEL: text' fields (F4 format).
    Ported from scripts/probe_r1_retrieval.py's _parse_fields (blank-line
    reset added, see module-level comment above)."""
    fields: dict[str, list[str]] = {}
    current: str | None = None
    for line in block.splitlines():
        stripped = line.strip()
        if not stripped:
            current = None
            continue
        m = _FIELD_LINE.match(stripped)
        if m:
            current = m.group(1).strip()
            fields[current] = [m.group(2).strip()]
        elif current:
            fields[current].append(stripped)
    return {k: " ".join(v).strip() for k, v in fields.items()}


def _parse_bullet_fields(block: str) -> dict[str, str]:
    """hand_detail's markdown '- **Label**: text' fields, including
    nested bullets under 'Visible Lines' (indentation is irrelevant to
    the regex, since every line is .strip()'d before matching)."""
    fields: dict[str, list[str]] = {}
    current: str | None = None
    for line in block.splitlines():
        stripped = line.strip()
        if not stripped:
            current = None
            continue
        m = _BULLET_FIELD.match(stripped)
        if m:
            current = m.group(1).strip()
            fields[current] = [m.group(2).strip()]
        elif current:
            fields[current].append(stripped)
    return {k: " ".join(v).strip() for k, v in fields.items()}


def _extract_quality(text: str) -> str:
    """First non-generic descriptive clause: a bare leading 'Present' is
    uninformative on its own, so skip it and take the next clause;
    otherwise use the first clause as-is. Ported from
    scripts/probe_r1_retrieval.py's _extract_quality."""
    clauses = [c.strip() for c in text.rstrip(".").split(",")]
    if clauses[0].lower() == "present" and len(clauses) > 1:
        return clauses[1].lower()
    return clauses[0].lower()


def _clean_quality_prefix(quality: str, feature: str) -> str:
    """Strips a leading self-referential mention of the feature name plus
    a linking verb (e.g. 'sun line is faintly visible' -> 'faintly
    visible') so the query template's '{quality} {feature}' doesn't
    duplicate the feature name. Ported from
    scripts/probe_r1_retrieval.py's _clean_quality_prefix."""
    q = quality.strip()
    fl = feature.lower()
    if q.lower().startswith(fl):
        q = q[len(fl):].strip()
    for verb in ("is ", "appears ", "are "):
        if q.lower().startswith(verb):
            q = q[len(verb):].strip()
            break
    return q or quality


def _is_absence(text: str) -> bool:
    low = text.lower()
    return any(phrase in low for phrase in _ABSENCE_PHRASES)


def _extract_needle_clause(text: str, needle: str) -> str:
    """For a multi-clause MOUNTS-style field that may only PARTLY concern
    the sub-feature (e.g. 'Mount of Venus appears developed, other
    mounts are unremarkable' only concerns Venus in its first clause),
    return just the clause(s) naming the needle. Without this, an
    unrelated clause's absence phrase (here, 'unremarkable' about a
    DIFFERENT mount) would wrongly flag the whole field absent and drop
    a genuinely observed quality ('developed')."""
    clauses = [c.strip() for c in text.split(",")]
    matching = [c for c in clauses if needle in c.lower()]
    return ", ".join(matching) if matching else text


# feature -> (palm_left/palm_right flat field label, hand_detail bullet
# label) for features that ARE a field, not a sub-mention within one.
_PLAIN_FEATURE_FIELDS: dict[str, tuple[str, str]] = {
    "life line": ("LIFE LINE", "Life Line"),
    "head line": ("HEAD LINE", "Head Line"),
    "heart line": ("HEART LINE", "Heart Line"),
    "fate line": ("FATE LINE", "Fate Line"),
    "thumb": ("THUMB", "Thumb"),
    "fingers": ("FINGERS", "Finger Lengths"),
}

# feature -> (flat field label, hand_detail bullet label or "" if none,
# needle) for sub-features named within a generic multi-purpose field
# (OTHER LINES may or may not name the sun line; MOUNTS may or may not
# name Venus/Jupiter specifically).
_SUB_FEATURES: tuple[tuple[str, str, str, str], ...] = (
    ("sun line", "OTHER LINES", "", "sun"),
    ("mount of venus", "MOUNTS", "Mounts", "venus"),
    ("mount of jupiter", "MOUNTS", "Mounts", "jupiter"),
)


def _gather_feature_texts(
    left_fields: dict[str, str],
    right_fields: dict[str, str],
    hd_fields: dict[str, str],
) -> dict[str, list[str]]:
    """{feature: [raw_text, ...]} -- every text from any source (LEFT,
    RIGHT, hand_detail) that represents or names that feature, before
    absence filtering."""
    texts: dict[str, list[str]] = {f: [] for f in _FEATURE_REGISTRY}

    for feature, (flat_label, bullet_label) in _PLAIN_FEATURE_FIELDS.items():
        for fields in (left_fields, right_fields):
            v = fields.get(flat_label)
            if v:
                texts[feature].append(v)
        v = hd_fields.get(bullet_label)
        if v:
            texts[feature].append(v)

    for fields in (left_fields, right_fields):
        v = fields.get("MARKS")
        if v:
            texts["markings/other features"].append(v)
    for bullet_label in ("Markings", "Other Features"):
        v = hd_fields.get(bullet_label)
        if v:
            texts["markings/other features"].append(v)

    for feature, flat_label, bullet_label, needle in _SUB_FEATURES:
        for fields in (left_fields, right_fields):
            v = fields.get(flat_label)
            if v and needle in v.lower():
                texts[feature].append(_extract_needle_clause(v, needle))
        if bullet_label:
            v = hd_fields.get(bullet_label)
            if v and needle in v.lower():
                texts[feature].append(_extract_needle_clause(v, needle))

    return texts


def _resolve_feature_quality(feature: str, raw_texts: list[str]) -> str | None:
    """None = no query -- either not observed by any source, or every
    mentioning source is absence-phrased. Otherwise the merged
    '{quality}' string for the variant-iii template (distinct per-source
    qualities joined with ' / ', per the probe-ratified merge rule).

    FAIL OPEN: a non-absent text that yields a degenerate quality (empty,
    or the bare word 'present') is queried with its own raw field text
    instead of being silently dropped -- junk retrieval is recoverable,
    silently dropped features are the S23 failure mode."""
    if not raw_texts:
        return None

    non_absent = [t for t in raw_texts if not _is_absence(t)]
    if not non_absent:
        return None

    qualities: list[str] = []
    for t in non_absent:
        q = _clean_quality_prefix(_extract_quality(t), feature)
        if not q or q.strip().lower() == "present":
            logger.warning(
                "palm_reading._resolve_feature_quality: fail-open for "
                "feature=%r -- quality extraction degenerate on %r, "
                "querying with raw field text instead.",
                feature, t,
            )
            q = t.rstrip(".")
        qualities.append(q.lower())

    seen: list[str] = []
    for q in qualities:
        if q not in seen:
            seen.append(q)
    return " / ".join(seen)


def _build_feature_query(feature: str, quality: str) -> str:
    """Ratified variant (iii), verbatim shape from the S67 probe."""
    noun = feature.split("/")[0]
    return (
        f"what does a {quality} {noun} signify — meaning and indications "
        f"of a {quality} {noun}"
    )


def _retrieve_per_feature(
    left_fields: dict[str, str],
    right_fields: dict[str, str],
    hd_fields: dict[str, str],
) -> tuple[dict[str, list[dict]], list[str]]:
    """Returns (per_feature_results, failed_features).
    per_feature_results is in _FEATURE_REGISTRY order, every feature
    present as a key (empty list if skipped or the search call failed) --
    this map, not just what's displayed, is the future R3 evidence
    structure, so every assignment is kept even when a chunk_id repeats
    across features."""
    texts_by_feature = _gather_feature_texts(left_fields, right_fields, hd_fields)
    results: dict[str, list[dict]] = {}
    failed: list[str] = []
    for feature in _FEATURE_REGISTRY:
        quality = _resolve_feature_quality(feature, texts_by_feature[feature])
        if quality is None:
            results[feature] = []
            continue
        query = _build_feature_query(feature, quality)
        try:
            results[feature] = search(
                query, n_results=_N_RESULTS_PER_FEATURE, book_name=_CHEIRO_BOOK
            )
        except Exception as exc:  # noqa: BLE001 -- one bad query must not kill the reading
            logger.warning(
                "palm_reading._retrieve_per_feature: search failed for "
                "feature=%r: %s", feature, exc,
            )
            failed.append(feature)
            results[feature] = []
    return results, failed


def _assemble_retrieved_passages(
    per_feature_results: dict[str, list[dict]],
) -> tuple[str, int]:
    """Groups passages under '### {feature}' headings, registry order. A
    chunk_id already displayed under an earlier feature is skipped for
    DISPLAY only (token economy) -- per_feature_results itself keeps
    every feature's full assignment untouched. Returns (assembled_text,
    total chunk assignments across all features, pre-dedupe -- used to
    decide the empty-retrieval low-confidence path)."""
    lines: list[str] = []
    seen_chunk_ids: set[str] = set()
    total = 0
    for feature, chunks in per_feature_results.items():
        total += len(chunks)
        display_chunks = [c for c in chunks if c["chunk_id"] not in seen_chunk_ids]
        if not display_chunks:
            continue
        lines.append(f"### {feature}")
        for c in display_chunks:
            lines.append(f"p.{c['page_ref']} (score: {c['score']})")
            lines.append(c["text"])
            lines.append("")
            seen_chunk_ids.add(c["chunk_id"])
    return "\n".join(lines).rstrip(), total


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
        hand_detail: Optional supplementary hand-photograph analysis --
                     appears verbatim in the user message as before, AND
                     (S67 R1) is now also parsed for per-feature RAG
                     retrieval, on the same footing as palm_left/
                     palm_right (see the LOCK LIFTED docstring note above).
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

    left_fields = _parse_fields(palm_left) if palm_left else {}
    right_fields = _parse_fields(palm_right) if palm_right else {}
    hd_fields = _parse_bullet_fields(hand_detail) if hand_detail else {}
    per_feature_results, failed_features = _retrieve_per_feature(
        left_fields, right_fields, hd_fields
    )
    if failed_features:
        logger.warning(
            "palm_reading.generate_palm_reading: retrieval failed for "
            "features: %s -- reading proceeds without them.",
            ", ".join(failed_features),
        )
    assembled_passages, total_chunks = _assemble_retrieved_passages(per_feature_results)

    system_prompt = _READING_SYSTEM_PROMPT
    if total_chunks == 0:
        logger.info("palm_reading.generate_palm_reading: empty RAG results -- proceeding with low-confidence caveat, not refusing.")
        system_prompt += _LOW_CONFIDENCE_ADDENDUM

    lines: list[str] = []
    if assembled_passages:
        lines += [
            "Retrieved passages (Cheiro's Language of the Hand):",
            "---",
            assembled_passages,
            "---",
        ]
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
    ) + " " + " ".join(
        c["text"] for chunks in per_feature_results.values() for c in chunks
    )

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
        {
            "book": c["book_name"],
            "page": c["page_ref"],
            "score": c["score"],
            "feature": feature,
        }
        for feature, chunks in per_feature_results.items()
        for c in chunks
    )

    return PalmReadingResult(
        reading_text=final_text,
        sources=sources,
        validation=validation,
        model=_READING_MODEL,
        retry_used=retry_used,
    )
