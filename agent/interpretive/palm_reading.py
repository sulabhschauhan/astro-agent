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

ACCEPTED GAPS (V1, S68 F-C close-out; gap (f) added by S68 F-A
close-out): six gaps registered under CLAUDE.md's "Known Source
Divergences / Accepted Gaps (V1)" section, each ALSO carrying its own
informational comment at the named code site (the 3-place convention:
CLAUDE.md, code-site comment, this note):
  (a) V-2 anchor legality is union-only (`_check_anchor_legality`) --
      RATIFIED FINAL, covered by the Ring 3 pass-4 human spot-check.
  (b) V-1 tag completeness is position-only (`_check_tag_completeness`)
      -- the untagged-sentence-sandwiched-between-two-tags gap, open by
      design (sentence-splitter improvisation is explicitly banned).
  (c) Heart-line corpus gap (`_retrieve_per_feature`) -- p.157-158 have
      zero chunks; positive-configuration doctrine never ranks in
      retrieval for this feature; non-harmful under A1 ([OBS] fallback).
  (d) `CHUNK_ANCHOR_TAG_PATTERN` couples to the current ingestion id
      schema (`*_p<n>_c<n>`) -- a re-ingested corpus with a different id
      shape would silently break tagging.
  (e) `valid_chunk_ids_count` in the F5 dogfood capture (frontend/app.py)
      is captured as "unavailable" -- not exposed on PalmReadingResult;
      pass-4's denominator comes from a reconstruction probe instead.
  (f) Coverage shared-chunk false-positive (`_check_feature_coverage`)
      -- a chunk_id gated under TWO features marks BOTH addressed when
      cited once; a direct consequence of gap (a)'s union-only V-2
      semantics. RATIFIED FINAL, same disposition as (a): covered by the
      SAME Ring 3 pass-4 human anchor-fidelity spot-check.
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
    across features.

    ACCEPTED GAP (S68 F-C close-out, CLAUDE.md "Known Source Divergences
    / Accepted Gaps (V1)" register, item (c)): "heart line" queries this
    corpus's p.156-162 chapter, but a deterministic metadata lookup
    (`diagnostics/fc_heartline_corpus_S68.md`) found p.157-158 have ZERO
    chunks (a chunking-pipeline gap, not a retrieval-tuning one), and
    positive-configuration doctrine that DOES exist (`p159_c2`, `p160_c1`
    -- e.g. "a happy, tranquil nature, good fortune, and happiness in
    affection") never ranked in this feature's embedding retrieval
    across the S68 probe's runs; `p159_c2`'s "...reaching the base of
    the first\\nfinger" line-wrap also defeats a literal substring check
    for that doctrine, independent of ranking. Non-harmful under A1: a
    chunk that never gets retrieved can never be cited, so the model
    falls back to `[OBS]`-tagged observation for this feature rather
    than fabricating a citation -- this gap is a coverage LOSS (thinner
    heart-line interpretation), not a grounding-safety risk. V1.1
    candidate fix: corpus re-ingestion/chunk-repair (see CLAUDE.md's
    V1.1 register) -- not attempted here (diagnostics-only probe, no
    production code touched)."""
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
    decide the empty-retrieval low-confidence path).

    A1 (S68 F-C): each passage's header line now leads with its full
    chunk_id in bracket form, e.g. "[cheiroslanguageo00chei_1_p134_c2]
    p.134 (score: 0.58)" -- this is the verbatim template the model is
    asked to copy back as a [<chunk_id>] anchor tag (see
    _OUTPUT_FORMAT_BLOCK / CHUNK_ANCHOR_TAG_PATTERN below)."""
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
            lines.append(f"[{c['chunk_id']}] p.{c['page_ref']} (score: {c['score']})")
            lines.append(c["text"])
            lines.append("")
            seen_chunk_ids.add(c["chunk_id"])
    return "\n".join(lines).rstrip(), total


# ─── R3: deterministic per-feature support gate + decline mechanism ────
#
# R1 retrieves 3 chunks per observed feature but never checks whether a
# chunk actually SAYS anything about that feature -- a chunk can be
# returned purely on embedding-similarity score while being about a
# different topic entirely (this is exactly how pass-2's fate-line
# doctrine-inversion finding happened: a retrieved chunk with a
# plausible score but no real fate-line content). R3 adds a pure-Python
# gate between R1's retrieval and prompt assembly: a chunk only
# "supports" its feature if it both scores above a noise floor AND
# actually names the feature (or a close synonym) in its text.

# Needles are deliberately SHORT, single-word forms for OCR robustness.
# This corpus is OCR-scanned and unreliable at the word level -- e.g.
# pass-1's p.163 chunk renders "life" as "hfe" in one instance ("The
# line of fate may rise from the line of hfe, the wrist, the Mount of
# Luna..."). A short needle can still register a match against another,
# correctly-OCR'd occurrence of the same word elsewhere in a longer
# passage, whereas a longer/stricter multi-word phrase requirement would
# be more likely to be defeated by a single garbled word anywhere in it.
_SUPPORT_NEEDLES: dict[str, tuple[str, ...]] = {
    "life line": ("life",),
    "head line": ("head",),
    "heart line": ("heart",),
    "fate line": ("fate",),
    "sun line": ("sun",),
    "thumb": ("thumb",),
    "fingers": ("finger",),
    "mount of venus": ("venus",),
    "mount of jupiter": ("jupiter",),
    "markings/other features": (
        "mark", "star", "cross", "island", "square", "circle", "hair",
    ),
}

# THRESHOLD DISCIPLINE (CLAUDE.md Working Style #4).
# Justification: S67 R1 probe (commit 0a738c3) measured a negative-
# control ceiling of 0.2192 (an unrelated "steam engine boiler
# maintenance" query) and a minimum genuine-doctrine score of 0.3954
# across the probed features -- 0.30 sits in the empty band between
# corpus noise and every observed real hit. This floor is a NOISE CUT
# only; the needle check (not the score) is the actual relevance
# discriminator. Scope guard: this gate only -- does not alter any
# other module's score handling. Revisit trigger: pass-3 claim ledgers
# showing a content-verified chunk excluded by this floor.
_SUPPORT_SCORE_FLOOR = 0.30


def _chunk_supports_feature(chunk: dict, feature: str) -> bool:
    """A chunk supports its feature iff its text (lowercased) contains at
    least one of the feature's needles AND its score clears the noise
    floor. Plain substring containment (not word-boundary) -- deliberate,
    and asymmetric with _check_banned_feature_mentions below on purpose
    (S67 R2 rider, accepted deviation, documented not changed):

    - HERE (chunk side): the text being matched is OCR-scanned corpus
      content, genuinely unreliable at the word level (confirmed: pass-1's
      p.163 chunk renders "life" as "hfe" -- "The line of fate may rise
      from the line of hfe, the wrist..."). The failure direction to
      avoid is a FALSE NEGATIVE: wrongly excluding a genuinely relevant
      chunk because OCR mangled the exact word boundary somewhere in it.
      Plain substring containment is the more permissive choice, and
      permissive is correct here -- a chunk that slips through on a loose
      match still has to clear the score floor too, and even then it's
      only entering RAG context for the LLM, not being asserted directly.
    - THERE (_check_banned_feature_mentions, LLM-output side): the text
      being matched is the model's OWN fluent, non-OCR'd English. There
      is no garbling risk to guard against -- the risk is the opposite
      one, ordinary-English word COLLISION (e.g. "remarkable" containing
      "mark", "sunny" containing "sun"). The failure direction to avoid
      there is a FALSE POSITIVE: wrongly failing an otherwise-clean
      reading over an unrelated word. Word-boundary matching is the
      stricter, correct choice for that check specifically."""
    needles = _SUPPORT_NEEDLES.get(feature, ())
    text_low = chunk["text"].lower()
    return chunk["score"] >= _SUPPORT_SCORE_FLOOR and any(n in text_low for n in needles)


def _is_genuine_negative_absence(feature: str, raw_texts: list[str]) -> bool:
    """True for R1's "mentioned but confirmed absent" pathway (e.g. every
    hand reporting "No clear marks visible") -- a genuine "you don't
    have this" finding, not a doctrine-coverage gap, so it has nothing
    to decline. False when the feature was never mentioned by ANY hand
    at all (e.g. "mount of jupiter" with no hand_detail) -- that case
    DOES belong in unsupported_features/the decline block, since it was
    genuinely never interpretable. Also False whenever a real,
    non-absent quality was observed (e.g. "Barely visible" is not one
    of R1's _ABSENCE_PHRASES) even if no chunk ends up supporting it --
    that is a doctrine-coverage gap, not a negative finding."""
    if not raw_texts:
        return False
    return all(_is_absence(t) for t in raw_texts)


def _apply_support_gate(
    per_feature_results: dict[str, list[dict]],
    texts_by_feature: dict[str, list[str]],
) -> tuple[dict[str, list[dict]], tuple[str, ...], tuple[str, ...]]:
    """Gates R1's per-feature map down to chunks that actually SUPPORT
    their feature. Returns (gated_results, supported_features,
    unsupported_features) -- both feature tuples in _FEATURE_REGISTRY
    order. unsupported_features covers every feature with zero
    surviving chunks EXCEPT the genuine-negative-absence case (see
    _is_genuine_negative_absence) -- those simply don't appear in
    either tuple, since there is nothing to support and nothing to
    decline."""
    gated: dict[str, list[dict]] = {}
    supported: list[str] = []
    unsupported: list[str] = []
    for feature in _FEATURE_REGISTRY:
        chunks = per_feature_results.get(feature, [])
        surviving = [c for c in chunks if _chunk_supports_feature(c, feature)]
        gated[feature] = surviving
        if surviving:
            supported.append(feature)
        elif not _is_genuine_negative_absence(feature, texts_by_feature.get(feature, [])):
            unsupported.append(feature)
    return gated, tuple(supported), tuple(unsupported)


# Human-friendly display names for the decline block -- only
# "markings/other features" needs translation, every other registry key
# is already plain English.
_FEATURE_DISPLAY_NAMES: dict[str, str] = {
    "markings/other features": "markings and other features",
}


def _feature_display_name(feature: str) -> str:
    return _FEATURE_DISPLAY_NAMES.get(feature, feature)


# Python-owned decline text (CLAUDE.md "formatter owns demotion strings"
# principle, applied here) -- the LLM is never asked to write this; see
# the system prompt's "STRICT SCOPE" rule below, which explicitly tells
# it not to.
_DECLINE_BLOCK_TEMPLATE = (
    "A note on what I have not interpreted: the classical texts I work "
    "from do not clearly address the following as they appear in your "
    "hands: {features}. Rather than guess, I have left these out of "
    "your reading."
)


def _build_decline_block(unsupported_features: tuple[str, ...]) -> str:
    if not unsupported_features:
        return ""
    names = ", ".join(_feature_display_name(f) for f in unsupported_features)
    return _DECLINE_BLOCK_TEMPLATE.format(features=names)


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
#
# S67 R2 REWRITE: F2c (165484c)'s original "## Voice" model sentences --
# "A deep, unbroken line of life promises long life, good health, and
# vitality." / "Such a fate line denotes success won by personal merit."
# -- fixed voice (P3) but, per Ring 3 pass 2's finding, were themselves
# the doctrine-inversion vector: their CONTENT (a quality->trait claim,
# "success won by personal merit") got transplanted verbatim onto a
# barely-visible fate line in every pass-2 run, the opposite of what the
# one classical passage on fate-line strength actually says. The
# exemplars below replace those two sentences with ones that illustrate
# ONLY Cheiro's declarative cadence -- they describe the general act of
# reading hands, never a specific line/mount quality or what it denotes,
# so there is no doctrine content left in them to leak. See
# _EXEMPLAR_SENTENCES / _check_exemplar_echo below for the deterministic
# guard that now backs this up (fed to the same F2c retry loop).
#
# A1 (S68 F-C, design-chat ratified): _OUTPUT_FORMAT_BLOCK is a plain
# string (not an f-string) folded into _READING_SYSTEM_PROMPT's own
# f-string below via {_OUTPUT_FORMAT_BLOCK} -- same pattern as
# _LANGUAGE_JARGON_BLOCK/_STRICT_CONTEXT_RULE, so its literal
# "{feature}" text is never mistaken for an f-string substitution site.
_OUTPUT_FORMAT_BLOCK = """## Output format (chunk-anchor tags)
Every sentence in your reading must end with exactly one tag, placed immediately after the sentence's closing punctuation with NO space before the bracket:
- "[OBS]" -- for observation-only sentences: restating what the confirmed hand description(s) say, the left/right innate-potential-vs-current-trajectory synthesis convention, or a voice/tone sentence carrying no interpretive claim of its own. Never put trait or doctrine content in an [OBS] sentence.
- "[<chunk_id>]" -- one or more, written back to back with no space between them, for any sentence that paraphrases doctrine from a specific retrieved passage. Copy the chunk_id EXACTLY as shown in that passage's own "[chunk_id] p.NNN (score: ...)" label above -- character for character, never invented or abbreviated. A chunk you cite this way MUST belong to the SAME "### {feature}" section your sentence is about.
Example: "The deep, unbroken life line promises long life and vitality.[cheiroslanguageo00chei_1_p134_c1]"
Tag every sentence, including the opening and closing ones. These tags are a machine-readable annotation only -- they are stripped before the reading is shown to the client, so they are not the "citations" the rule below forbids; that rule is about your visible prose, not this tag."""

_READING_SYSTEM_PROMPT = f"""You are a Cheiro-tradition palmist writing a single, one-shot palm reading for a client who has just uploaded photo(s) of their hand(s).

## Your knowledge
You have been provided with relevant passages from Cheiro's Language of the Hand -- the classical source for this reading. Ground your interpretation in these passages; do not draw on any other astrological or palmistry tradition.

## How you read
- Synthesize the provided hand description(s) into one cohesive, direct reading -- speak as a confident palmist, not an academic.
- When BOTH hands are present: the left hand reveals innate potential and character, the right hand reveals the native's current life trajectory -- synthesize both into a single unified reading, not two separate paragraphs.
- When only one hand is present, read that hand alone -- do not speculate about the missing hand.
- Do not cite book names, page numbers, or passage numbers in your prose -- deliver the reading directly. (The chunk-id tag required at the end of every sentence, per the Output format section below, is a separate machine-readable annotation, not a citation in your prose -- it is stripped before display.)
- If the retrieved passages do not clearly support a feature in the description, say so honestly -- do not fabricate.
- Where a retrieved passage speaks directly to a described feature, apply that passage's specific teaching rather than a generic gloss -- do not let a feature you have textual support for get the same vague treatment as one you don't.
- STRICT SCOPE (S67 R3): base this reading ONLY on the features named by a "### {{feature}}" heading in the provided passages section below -- do not name, allude to, or interpret any OTHER palm feature, even if it appears in the hand description(s) below. If a feature has no heading there, it is out of scope for this reading; a separate note about anything left out is appended after your response completes -- do not write your own version of that note.
- This is a ONE-SHOT reading: do not ask clarifying questions, do not introduce yourself, and do not reference any prior conversation -- there is none.

## Voice
Write in Cheiro's declarative register: direct, confident assertions in period-appropriate diction, addressed straight to the reader. This is a palmist reading a hand, not a therapist offering affirmation -- speak with the authority of someone who has read thousands of hands and states plainly what each one shows.
Model sentences (voice and cadence ONLY -- do not reuse or adapt ANY part of their wording, not even a short fragment; they contain no interpretive content of their own): "I have examined many hands in my years of practice, and each one tells its own story to those who know how to read it." / "The hand rarely lies to the palmist who reads it honestly." Every interpretive claim in your actual reading must come from the provided passages and the confirmed hand description(s) below -- these two sentences exist only to model tone, never as a source of content.
FORBIDDEN words and phrasings (never use these, in any form): stability, fulfillment, fulfilling, favorable, journey, navigate, navigating, empower, empowerment, and any "this suggests you are the kind of person who..." self-help framing.

{_OUTPUT_FORMAT_BLOCK}

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


# ─── A1: chunk-anchor tag format + strip layer (S68 F-C, design-chat) ──
#
# Every sentence in the raw generation output must end with exactly one
# tag -- "[OBS]" for observation-only prose, or one-or-more adjacent
# "[<chunk_id>]" anchors for a sentence paraphrasing doctrine from a
# specific retrieved passage (see _OUTPUT_FORMAT_BLOCK above, folded
# into _READING_SYSTEM_PROMPT). CHUNK_ANCHOR_TAG_PATTERN is the SINGLE
# source of truth for what a tag token looks like -- strip_generation_
# tags() below uses it, and it is a PUBLIC module attribute specifically
# so a future anchor-legality validator (a separate prompt, not this
# one) can import the exact same pattern rather than re-deriving it and
# risking drift between the two.
#
# NOT built here: any check that a sentence actually HAS a trailing tag,
# that an anchored sentence's cited chunk_id actually belongs to its
# feature section, or that [OBS] sentences carry no doctrine content --
# those are anchor-LEGALITY checks, explicitly deferred to the next
# prompt. This layer only knows how to find and remove tag tokens; the
# existing Ring 1 validators below are untouched and still run on the
# raw (tagged) draft exactly as before A1.
#
# Pattern shape: "[OBS]" literally, or "[<chunk_id>]" where chunk_id
# matches this corpus's real id shape (<book_name>_p<page>_c<index>,
# e.g. cheiroslanguageo00chei_1_p134_c2) -- deliberately narrower than a
# bare "\\[\\w+\\]" to minimize false-positive collision with ordinary
# bracketed prose the model might otherwise emit.
#
# ACCEPTED GAP (S68 F-C close-out, CLAUDE.md "Known Source Divergences /
# Accepted Gaps (V1)" register, item (d)): this pattern is COUPLED to the
# current ingestion pipeline's id-generation convention (`*_p<n>_c<n>`,
# see `ingestion/chunker.py`). A future re-ingestion of this corpus (or
# any corpus onboarded with a different chunk_id shape) would silently
# break tagging -- the model's citations would still be well-formed per
# its own output but would never match this pattern, so V-1/V-2 would
# treat every citation as untagged residue / an unknown id rather than
# failing loud with a schema-mismatch error. V1.1 register: any corpus
# re-ingestion/chunk-repair work (see the heart-line corpus gap above)
# MUST revisit this pattern in the SAME change, not as a follow-up.
CHUNK_ANCHOR_TAG_PATTERN = re.compile(r"\[(?:OBS|[A-Za-z0-9_]+_p\d+_c\d+)\]")


def strip_generation_tags(text: str) -> str:
    """Removes every [OBS] / [<chunk_id>] tag from `text`, producing the
    clean display text. Pure regex on CHUNK_ANCHOR_TAG_PATTERN -- text
    with no tags at all (e.g. any pre-A1 caller, or a test stub written
    before this contract existed) passes through unchanged, since there
    is nothing for the pattern to match; that is a legitimate no-op, not
    degraded behavior.

    Raises:
        RuntimeError: the strip operation itself fails for any reason
                      (e.g. non-string input) -- fails loud rather than
                      risk silently shipping tagged text to display.
    """
    try:
        stripped = CHUNK_ANCHOR_TAG_PATTERN.sub("", text)
        # Tags are attached directly to sentence-final punctuation with no
        # leading space (per the prompt contract), so removing one leaves
        # no stray space behind in the common case; this pass only cleans
        # up incidental multi-space/trailing-space runs a removed tag
        # might leave when it wasn't the very last token on its line.
        stripped = re.sub(r"[ \t]{2,}", " ", stripped)
        stripped = re.sub(r"[ \t]+\n", "\n", stripped)
        stripped = re.sub(r"[ \t]+$", "", stripped)
        return stripped
    except Exception as exc:
        raise RuntimeError(
            f"palm_reading.strip_generation_tags: failed to strip "
            f"chunk-anchor tags from generation output: {exc}"
        ) from exc


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


def _check_banned_feature_mentions(
    text: str, unsupported_features: tuple[str, ...]
) -> list[str]:
    """S67 R3: fires if the reading names an UNSUPPORTED feature's needle
    anywhere. Word-boundary matching is MANDATORY here (unlike the
    support gate's plain substring check, see _chunk_supports_feature) --
    a false positive here fails an otherwise-clean reading, so "sun"
    must not fire on "sunday"/"sunny", and "mark" must not fire on
    "marked"/"remarkable". Same style as _JARGON_PATTERN above."""
    failures: list[str] = []
    low = text.lower()
    for feature in unsupported_features:
        needles = _SUPPORT_NEEDLES.get(feature, ())
        if not needles:
            continue
        pattern = re.compile(
            r"\b(" + "|".join(re.escape(n) for n in needles) + r")\b",
            re.IGNORECASE,
        )
        if pattern.search(low):
            failures.append(f"unsupported feature mentioned: {feature}")
    return failures


# S67 R2: the two "## Voice" model sentences, verbatim, as the
# exemplar-echo guard's comparison set. Deliberately NOT derived from
# _READING_SYSTEM_PROMPT by parsing -- kept as an explicit, independent
# constant so a future prompt edit can't silently desync the two
# without a human noticing (the SENSITIVE_TO convention this module
# already uses elsewhere for prompt_builder.py cross-references).
_EXEMPLAR_SENTENCES: tuple[str, ...] = (
    "I have examined many hands in my years of practice, and each one "
    "tells its own story to those who know how to read it.",
    "The hand rarely lies to the palmist who reads it honestly.",
)

# THRESHOLD DISCIPLINE (CLAUDE.md Working Style #4).
# Justification: pass-2's observed leaked span from the OLD exemplar
# ("Such a fate line denotes success won by personal merit") was
# "denotes success won by personal merit" -- exactly 6 words. That is
# the shortest confirmed leak, so it sets the window; anything smaller
# risks colliding with ordinary English phrasing that has nothing to do
# with exemplar leakage. Scope guard: compares reading_text against the
# exemplar sentences ONLY, never the retrieved passages -- quoting
# doctrine from a retrieved chunk is desired behavior (the system
# prompt explicitly asks for it), not leakage. Revisit trigger: a
# pass-3 ledger showing a PARAPHRASED (sub-6-word-overlap) inversion --
# that would mean this guard's textual-overlap approach has hit its
# ceiling and needs a different mechanism (R2.x), not a smaller n.
_EXEMPLAR_ECHO_NGRAM = 6

_PUNCT_PATTERN = re.compile(r"[^\w\s]")


def _normalize_for_echo_check(text: str) -> list[str]:
    """Lowercase, strip punctuation, collapse whitespace -> word tokens.
    Shared by both the exemplar sentences (precomputed once at import)
    and every reading_text checked against them, so an overlap that
    differs only in case/punctuation/whitespace still registers."""
    text = _PUNCT_PATTERN.sub("", text.lower())
    return text.split()


def _ngrams(tokens: list[str], n: int) -> list[tuple[str, ...]]:
    """Positional order (a list, not a set) -- _check_exemplar_echo below
    relies on this to report the FIRST (leftmost) overlapping window in
    reading_text, not an arbitrary one from hash-order iteration."""
    return [tuple(tokens[i:i + n]) for i in range(len(tokens) - n + 1)]


_EXEMPLAR_NGRAMS: frozenset[tuple[str, ...]] = frozenset().union(
    *(
        _ngrams(_normalize_for_echo_check(sentence), _EXEMPLAR_ECHO_NGRAM)
        for sentence in _EXEMPLAR_SENTENCES
    )
)


def _check_exemplar_echo(text: str) -> list[str]:
    """S67 R2: fires if reading_text contains any contiguous 6-word span
    (normalized) also present in an exemplar sentence -- the guard
    against F2c's exemplar-leakage failure mode (Ring 3 pass 2's
    fate-line doctrine inversion). Compares against _EXEMPLAR_SENTENCES
    only, never retrieved chunks (see THRESHOLD DISCIPLINE above)."""
    tokens = _normalize_for_echo_check(text)
    for ngram in _ngrams(tokens, _EXEMPLAR_ECHO_NGRAM):
        if ngram in _EXEMPLAR_NGRAMS:
            return [f"exemplar_echo: {' '.join(ngram)}"]
    return []


# ─── A1 V-1/V-2: chunk-anchor Ring 1 validators (S68 F-C, design-chat) ──
#
# Both operate on the RAW generation draft (the text that becomes
# PalmReadingResult.reading_text_tagged once the draft settles) -- the
# SAME `text` parameter the pre-existing six checks above already
# receive, BEFORE strip_generation_tags() runs. Deterministic, no LLM
# judgment, per CHUNK_ANCHOR_TAG_PATTERN (the single source of truth for
# tag shape, shared with strip_generation_tags() and importable by any
# future caller -- CONSTRAINTS section of the instructing design).


def _check_tag_completeness(text: str) -> list[str]:
    """A1 V-1: every sentence in `text` must terminate in a tag matching
    CHUNK_ANCHOR_TAG_PATTERN or the literal "[OBS]". Deterministic,
    regex-POSITION-based partitioning ONLY -- no prose sentence-splitter,
    no NLP dependency (per the instructing design's explicit
    prohibition). Catches:
      (a) text empty/whitespace-only -- the PRIMARY guard: "anchor
          contract not exercised" -- this is what a construction site
          relying on PalmReadingResult.reading_text_tagged's dataclass
          default of "" would trip if that value were ever fed back
          through Ring 1 (generate_palm_reading() itself never does
          this -- it always passes the real draft -- but the check
          exists at this layer so the guard holds regardless of caller).
      (b) untagged residue AFTER THE LAST recognized tag in the text --
          the one position where "no tag will ever follow" is
          structurally certain from tag positions alone, with no NLP.

    KNOWN GAP (documented, not silently absorbed): an untagged sentence
    sandwiched BETWEEN two valid tags (e.g. "...[OBS] untagged sentence
    here. Another sentence.[OBS]") is NOT caught -- distinguishing "one
    legitimate multi-clause thought that only needed one trailing tag"
    from "two sentences, only the second earned its tag" requires
    sentence-boundary detection, which this design explicitly forbids
    building. Only whole-text-untagged and trailing-residue are
    decidable from tag positions alone; this is the honest boundary of
    a position-only check, not an oversight.
    """
    try:
        if not text or not text.strip():
            return [
                "anchor_completeness: anchor contract not exercised "
                "(reading_text_tagged is empty or whitespace-only)"
            ]

        matches = list(CHUNK_ANCHOR_TAG_PATTERN.finditer(text))
        if not matches:
            residue = text.strip()
            return [f"anchor_completeness: sentence-final residue with no tag: {residue!r}"]

        trailing_residue = text[matches[-1].end():].strip()
        if trailing_residue:
            return [f"anchor_completeness: sentence-final residue with no tag: {trailing_residue!r}"]

        return []
    except Exception as exc:
        raise RuntimeError(
            f"palm_reading._check_tag_completeness: validator crashed -- "
            f"failing the run loud rather than passing silently: {exc}"
        ) from exc


def _check_anchor_legality(text: str, valid_chunk_ids: frozenset[str]) -> list[str]:
    """A1 V-2: every cited chunk_id in `text` must be a member of
    `valid_chunk_ids` -- the union of every chunk_id present ANYWHERE in
    gated_results (all features combined), the SAME dict the generation
    prompt's passages were assembled from (single source of truth, no
    re-retrieval).

    DESIGN-CHAT ESCALATION, per the instructing design's own fallback
    clause ("if section boundaries are NOT deterministically recoverable
    ... implement union-of-all-gated-sets membership only ... then STOP
    and report the section-attribution gap"): this IS that fallback.
    The stricter per-feature-section requirement ("a cited chunk must
    belong to the SAME '### {feature}' section the citing sentence is
    about") needs a deterministic sentence -> feature mapping, and the
    GENERATED reading has no structural feature markers of its own --
    the "### {feature}" headings exist only in the INPUT passages shown
    to the model (see _assemble_retrieved_passages), never in its
    free-flowing one-paragraph-or-few output prose (the system prompt
    explicitly asks for "one cohesive, direct reading ... not two
    separate paragraphs", not per-feature sections). Recovering
    sentence -> feature attribution from that output format is NOT
    deterministic without a heuristic splitter, which this prompt's
    instructions explicitly forbid improvising. RESULT: this check is
    union-only. It still kills FABRICATED chunk_ids (never gated for
    any feature, any run) and STALE chunk_ids (gated for a prior
    run/different retrieval, not this one) -- it CANNOT catch a real,
    gated chunk_id cited under the WRONG feature's sentence. That gap
    was escalated here for a design-chat ruling.

    RULING FINAL (S68 F-C close-out, CLAUDE.md "Known Source Divergences
    / Accepted Gaps (V1)" register, item (a)): this is a PERMANENT
    accepted gap, not an open escalation awaiting a future validator.
    The wrong-feature-citation case is covered by the Ring 3 pass-4
    human anchor-fidelity spot-check (claim -> cited-chunk faithfulness,
    sampled by a person against the tagged draft) instead of a
    mechanical check -- re-open only if pass-4 evidence shows this gap
    is being missed at a rate that no longer justifies a human
    spot-check over a real (heuristic-splitter) fix.
    """
    try:
        cited: set[str] = set()
        for match in CHUNK_ANCHOR_TAG_PATTERN.finditer(text):
            token = match.group(0)[1:-1]  # strip surrounding [ ]
            if token == "OBS":
                continue
            cited.add(token)
        unknown = sorted(cited - valid_chunk_ids)
        if unknown:
            return [f"anchor_legality: unknown/malformed chunk_id(s): {', '.join(unknown)}"]
        return []
    except Exception as exc:
        raise RuntimeError(
            f"palm_reading._check_anchor_legality: validator crashed -- "
            f"failing the run loud rather than passing silently: {exc}"
        ) from exc


def _check_feature_coverage(
    tagged_text: str,
    gated_results: dict[str, list[dict]],
    supported_features: tuple[str, ...],
) -> list[str]:
    """F-A (S68): supported-feature coverage check -- WARNING-class, not
    a Ring 1 failure. A supported feature counts as ADDRESSED iff at
    least one sentence in `tagged_text` cites a chunk_id belonging to
    that feature's own gated_results set. Pure set operations on the
    anchor tags (same extraction as V-2/_check_anchor_legality, [OBS]
    excluded) -- no keyword matching on the prose, no thresholds.

    Membership surface is gated_results (the full per-feature assignment
    map), NOT the deduped display passages -- _assemble_retrieved_
    passages skips repeat chunk_ids for DISPLAY only, so a chunk shared
    across features may only ever appear under an earlier feature's
    heading; crediting from the full gated set keeps coverage satisfiable
    regardless of which heading displayed the chunk.

    LANDMARK EXCLUSION -- enforced by construction: [OBS] tags contribute
    nothing to the cited set, so an observation-only mention like
    "curves around the base of the thumb" (a life-line landmark
    reference, tagged [OBS] or citing a life-line chunk) can never mark
    the thumb addressed. The pass-3 false-positive-coverage case
    (Findings #2's landmark ledger note) is excluded without any prose
    inspection at all.

    RING 3 PASS-4 EVIDENCE (design-chat lock): these warnings surface in
    ValidationReport.warnings and are scoring evidence for the human
    rubric -- a warning-bearing run cannot score P4 clean.

    ACCEPTED GAP (V1, shared-chunk false-positive boundary, F-A close-out
    S68, CLAUDE.md "Known Source Divergences / Accepted Gaps (V1)"
    register item (f)): a chunk_id gated under TWO features marks BOTH
    addressed when cited once, regardless of which feature the citing
    sentence is actually about -- a direct consequence of gap (a)'s
    (_check_anchor_legality) union-only V-2 anchor semantics (no
    sentence -> feature attribution exists to disambiguate). Direction
    of error: a real omission can go un-warned; a warning is never
    spurious for a genuinely-cited feature.

    RULING FINAL, same disposition as gap (a): a PERMANENT accepted gap,
    not an open escalation. Backstopped by the SAME Ring 3 pass-4 human
    anchor-fidelity spot-check (claim -> cited-chunk faithfulness) that
    covers gap (a)'s wrong-feature-citation case -- re-open only if
    pass-4 evidence shows this specific boundary being missed at a rate
    that no longer justifies a human spot-check over a real (sentence ->
    feature attribution) fix.
    """
    try:
        cited: set[str] = set()
        for match in CHUNK_ANCHOR_TAG_PATTERN.finditer(tagged_text):
            token = match.group(0)[1:-1]  # strip surrounding [ ]
            if token == "OBS":
                continue
            cited.add(token)
        warnings: list[str] = []
        for feature in supported_features:
            feature_ids = {c["chunk_id"] for c in gated_results.get(feature, [])}
            if not feature_ids & cited:
                warnings.append(f"coverage: {feature} supported but never cited")
        return warnings
    except Exception as exc:
        raise RuntimeError(
            f"palm_reading._check_feature_coverage: validator crashed -- "
            f"failing the run loud rather than passing silently: {exc}"
        ) from exc


def _run_ring1_checks(
    text: str,
    context_corpus: str,
    unsupported_features: tuple[str, ...] = (),
    valid_chunk_ids: frozenset[str] = frozenset(),
) -> list[str]:
    """All eight Ring 1 validators, run in a fixed order. Shared by the
    first draft and the S66 F2c retry draft -- same checks, same order,
    both passes. A1 (S68 F-C) appended V-1 (_check_tag_completeness) and
    V-2 (_check_anchor_legality) at the end of the pre-existing six --
    their logic/order is UNTOUCHED; V-1 runs before V-2 (legality is
    meaningless to check on incomplete tagging).

    A1 INPUT-SURFACE SPLIT (S68 F-C, design-chat ruling): `text` is the
    raw TAGGED draft (the same value that becomes PalmReadingResult.
    reading_text_tagged) -- but the two input surfaces measure different
    things, so they read different text:
      - The six pre-A1 "display" checks (jargon, self-help register,
        unsupported dates, length, banned-feature mentions, exemplar
        echo) measure what the user will actually SEE, so they run on
        `stripped` (strip_generation_tags(text), computed ONCE here, not
        per-check) -- confirmed bug this fixes: anchor tags are
        whitespace-delimited tokens on the raw draft (measure-first
        proof: diagnostics/latest_run.md), so left untouched they
        inflate _check_length's word count against the 700-word rail
        and perturb _check_exemplar_echo's n-gram token adjacency.
      - V-1/_check_tag_completeness and V-2/_check_anchor_legality
        measure the anchor CONTRACT itself, not display semantics, so
        they keep reading `text` (tagged, unchanged) -- stripping first
        would make V-1 vacuously pass (no tags left to be incomplete)
        and V-2 unobservable (no chunk_id citations left to validate).
    """
    stripped = strip_generation_tags(text)
    failures: list[str] = []
    failures += _check_jargon(stripped)
    failures += _check_self_help_register(stripped)
    failures += _check_unsupported_dates(stripped, context_corpus)
    failures += _check_length(stripped)
    failures += _check_banned_feature_mentions(stripped, unsupported_features)
    failures += _check_exemplar_echo(stripped)
    failures += _check_tag_completeness(text)
    failures += _check_anchor_legality(text, valid_chunk_ids)
    return failures


@dataclass(frozen=True)
class ValidationReport:
    passed: bool
    failures: tuple[str, ...]
    # F-A (S68): coverage warnings (_check_feature_coverage) -- additive
    # default, same frozen-dataclass pattern as PalmReadingResult.
    # reading_text_tagged, so pre-F-A construction sites keep working
    # unmodified. `passed` semantics UNCHANGED: failures only -- warnings
    # never block display, never flip passed.
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True)
class PalmReadingResult:
    reading_text: str
    sources: tuple[dict, ...]
    validation: ValidationReport
    model: str
    retry_used: bool
    # S67 R3: registry-order tuples from the support gate. A feature can
    # appear in NEITHER when it's a genuine negative-absence finding
    # (see _is_genuine_negative_absence) -- nothing to support, nothing
    # to decline.
    supported_features: tuple[str, ...]
    unsupported_features: tuple[str, ...]
    # A1 (S68 F-C): the raw generation output BEFORE tag-stripping --
    # every sentence's trailing [OBS]/[chunk_id] tag(s) intact, no
    # decline_block/DISCLAIMER appended (those are Python-owned strings
    # the LLM never tagged). Additive only -- reading_text above remains
    # the existing clean-display key, now populated via
    # strip_generation_tags() rather than passed through verbatim. Feeds
    # a FUTURE anchor-legality validator; this prompt does not itself
    # validate the tags' legality. Defaults to "" (not None -- this
    # field's type is str, never optional) so any construction site that
    # predates A1 (e.g. tests/test_app_dogfood_capture.py's direct
    # PalmReadingResult(...) fixture, unrelated to this prompt's scope)
    # keeps working unmodified; generate_palm_reading() itself always
    # supplies the real value explicitly, never relies on this default.
    reading_text_tagged: str = ""


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
        A1 (S68 F-C): reading_text is now built via strip_generation_
        tags() rather than passed through verbatim; reading_text_tagged
        carries the same final draft BEFORE stripping (no decline_block/
        DISCLAIMER appended either), for a future anchor-legality
        validator to inspect.
        F-A (S68): validation.warnings carries supported-feature coverage
        misses from the FINAL draft (_check_feature_coverage) -- a
        first-draft miss feeds the same single F2c retry (retry_used
        reports it identically), but a final-draft miss is fail-open:
        warnings never enter failures and never flip passed.

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

    # S67 R3: gate R1's raw retrieval down to chunks that actually
    # support their feature. gated_results (not per_feature_results) is
    # what feeds the prompt, sources, and context_corpus from here on.
    texts_by_feature = _gather_feature_texts(left_fields, right_fields, hd_fields)
    gated_results, supported_features, unsupported_features = _apply_support_gate(
        per_feature_results, texts_by_feature
    )

    # A1 V-2: single source of truth for anchor-legality membership -- the
    # SAME gated_results dict the generation prompt's passages were
    # assembled from below, no re-retrieval. Union across ALL features
    # (see _check_anchor_legality's own docstring for why this is
    # union-only, not per-feature-section -- a documented, escalated gap).
    valid_chunk_ids = frozenset(
        c["chunk_id"] for chunks in gated_results.values() for c in chunks
    )

    assembled_passages, total_chunks = _assemble_retrieved_passages(gated_results)

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
        c["text"] for chunks in gated_results.values() for c in chunks
    )

    failures = _run_ring1_checks(
        reading_text, context_corpus, unsupported_features, valid_chunk_ids
    )
    # F-A (S68): coverage runs ALONGSIDE Ring 1's eight validators, never
    # inside _run_ring1_checks -- its misses are warning-class (fail-open
    # on the final draft), a different disposition than the fail-closed
    # eight. Reads the tagged draft (contract surface, like V-1/V-2).
    coverage_misses = _check_feature_coverage(
        reading_text, gated_results, supported_features
    )
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
    # F-A (S68): coverage misses FEED the same single retry (same 2-call
    # hard cap, same deterministic-reviewer-only mechanism -- a
    # coverage-only retry sets retry_used=True via this existing path, no
    # new flags), but on the FINAL draft they land in ValidationReport.
    # warnings, never failures -- fail-open, display never blocked.
    if failures or coverage_misses:
        retry_used = True
        retry_messages = messages + [
            {"role": "assistant", "content": reading_text},
            {
                "role": "user",
                "content": (
                    "Your draft failed these checks: "
                    + "; ".join(failures + coverage_misses) + ". "
                    "Rewrite the reading correcting ONLY these issues. Same "
                    "facts, same structure."
                ),
            },
        ]
        reading_text = _call(retry_messages)
        failures = _run_ring1_checks(
            reading_text, context_corpus, unsupported_features, valid_chunk_ids
        )
        coverage_misses = _check_feature_coverage(
            reading_text, gated_results, supported_features
        )

    validation = ValidationReport(
        passed=not failures,
        failures=tuple(failures),
        warnings=tuple(coverage_misses),
    )

    # A1: raw tagged draft preserved verbatim (pre-decline, pre-disclaimer,
    # pre-strip) for reading_text_tagged, captured BEFORE any of the
    # display-text post-processing below touches reading_text.
    reading_text_tagged = reading_text

    # S67 R3: Python-owned decline block for observed-but-unsupported
    # features, appended AFTER validation runs (same reasoning as
    # DISCLAIMER below) but BEFORE it.
    decline_block = _build_decline_block(unsupported_features)
    # A1: strip chunk-anchor tags before building the clean display text --
    # decline_block/DISCLAIMER are Python-owned strings the LLM never
    # tagged, so they are appended AFTER stripping, not before.
    final_text = strip_generation_tags(reading_text).rstrip()
    if decline_block:
        final_text += "\n\n" + decline_block
    # DISCLAIMER appended AFTER validation runs -- its own wording/any
    # incidental year-like strings must never trip the validators above.
    final_text += "\n\n" + DISCLAIMER

    sources = tuple(
        {
            "book": c["book_name"],
            "page": c["page_ref"],
            "score": c["score"],
            "feature": feature,
        }
        for feature, chunks in gated_results.items()
        for c in chunks
    )

    return PalmReadingResult(
        reading_text=final_text,
        reading_text_tagged=reading_text_tagged,
        sources=sources,
        validation=validation,
        model=_READING_MODEL,
        retry_used=retry_used,
        supported_features=supported_features,
        unsupported_features=unsupported_features,
    )
