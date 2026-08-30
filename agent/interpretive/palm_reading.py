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

S69 F-H P5 (two-stage wiring, this module's single-call generation
RETIRED): the block that used to build `_READING_SYSTEM_PROMPT` +
`_LOW_CONFIDENCE_ADDENDUM`, assemble one whole-reading prompt, and make a
single free-composition generation call (with its own F2c retry) is
REPLACED by a call to `claim_extraction.extract_claims()` (Stage 1: one
per-feature extraction call, paraphrase-or-nothing, its own F2c retry per
feature) followed by `claim_voicing.voice_claims()` (Stage 2: one
closed-inventory voice call over Stage 1's surviving claims, its own F2c
retry). `generate_palm_reading()` keeps its exact pre-existing signature
and behavior contract -- it is now `prepare_palm_reading()` composed with
`complete_palm_reading()`, split at that seam for a future dogfood
checkpoint (P6) to inspect the Stage-1 claims inventory before voicing.

RETIRED, NOT DELETED (this prompt's own instruction: leave the functions
defined, delete only their INVOCATION -- a future close-out prompt owns
actual deletion):
  - V-1 (`_check_tag_completeness`) / V-2 (`_check_anchor_legality`): no
    longer called. Their whole-reading anchor-legality job is NATIVELY
    replaced, not merely re-implemented, by the two-stage architecture
    itself -- `claim_extraction.py`'s E-1 validator checks chunk_id
    legality PER FEATURE at extraction time (retiring accepted gaps (a)
    and (f) above, which were both consequences of V-2's UNION-only
    membership check), and `claim_voicing.py`'s own V-3 validator checks
    tag legality on Stage 2's OWN `{[C<n>], [OBS], [FLOW]}` tag
    vocabulary -- a DIFFERENT vocabulary than `CHUNK_ANCHOR_TAG_PATTERN`
    ever recognized (see `_STAGE2_TAG_PATTERN` / `_strip_stage2_tags`
    below: reusing `strip_generation_tags()` as-is on Stage-2 output
    would silently leave `[C1]`/`[FLOW]` tokens in the displayed text,
    since that pattern only ever recognized `[OBS]` or a full
    `[<book>_p<n>_c<n>]` chunk-id token).
  - `_check_feature_coverage` (F-A, S68): superseded by V-4 (claim
    coverage), which is STRICTLY STRONGER -- V-4 checks that every claim
    Stage 2 was actually OFFERED gets voiced at least once, a
    claim-level guarantee the old whole-reading coverage warning could
    only approximate via chunk-id set membership. No longer called;
    `ValidationReport.warnings` is kept for dataclass compatibility but
    is now always `()`.
  - `_run_ring1_checks` (the old eight-validator sequence spanning both
    display checks and V-1/V-2): no longer called. Its six DISPLAY
    checks (jargon, self-help register, unsupported dates, length,
    banned-feature mentions, exemplar echo) survive, unchanged, in the
    new `_run_display_checks()` below -- they still measure real display
    semantics on Stage 2's stripped output, and `_check_exemplar_echo`
    in particular stays meaningful since `claim_voicing._VOICE_SYSTEM_
    PROMPT` transplants the SAME `_EXEMPLAR_SENTENCES` tone-anchors this
    module already owns.

NOTED BEHAVIOR CHANGE (not a bug, a direct architectural consequence,
flagged here rather than silently shipped): the old single-call flow's
`_LOW_CONFIDENCE_ADDENDUM` path let the model free-compose a generic
reading from confirmed observations alone when retrieval returned zero
chunks for every feature. The two-stage architecture has no equivalent --
if every feature's gated chunk list is empty, `extract_claims` has
nothing to attempt (an empty, non-raising result) and `voice_claims`
then has nothing to voice (also an empty, non-raising result), so the
final reading is decline-block-plus-disclaimer only, no generic
free-composed prose. This is judged a deliberate, correct consequence of
retiring free composition (the entire point of F-H), not a regression to
patch here -- flagged for the close-out prompt's CLAUDE.md registration,
not silently absorbed.
"""

from __future__ import annotations

import os
import json
import logging
import re
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

from agent.interpretive import claim_extraction, claim_voicing
from agent.interpretive.claim_extraction import Claim
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

# Same flag, same env var, same comparison as frontend/app.py's own
# _DOGFOOD_CAPTURE (app.py:41) -- read independently here rather than
# threaded as a parameter through prepare_palm_reading/generate_palm_reading,
# since those signatures are a stable external contract and this module
# already runs in the same process/env as app.py. Governs ONLY the
# n_results fetch size below; does not change the one-call-per-feature
# contract (CLAUDE.md Locked Decisions) -- still exactly one search() call
# per feature, just a smaller n_results value in production.
_DOGFOOD_CAPTURE = os.environ.get("ASTRO_DOGFOOD_CAPTURE") == "1"

_FEATURE_REGISTRY: tuple[str, ...] = (
    "life line", "head line", "heart line", "fate line", "sun line",
    "thumb", "fingers", "mount of venus", "mount of jupiter",
    "mount of saturn", "mount of apollo", "mount of mercury",
    "mount of mars positive", "mount of mars negative", "mount of luna",
    "markings/other features",
)

# S81/S82 page-range gate -- ON. _search_with_page_filter pushes the
# feature's verified chapter range (data/cheiro_feature_pages.json) into
# the SAME single search() call as a page_ref=(start, end) Chroma
# where-clause filter -- one call per feature, satisfying the
# one-call-per-feature contract (CLAUDE.md Locked Decisions). Does NOT
# change _N_RESULTS_PER_FEATURE or the query template -- those are
# separate, untouched constants.
#
# EVIDENCE: diagnostics/onoff_range_gate_S82.md (commit 0334038), a
# three-arm OFF/ON/WIDE run over 8 of 10 registry features. Identical
# result sets on 6 of 8 (no-op there); corrective on head line (OFF
# returned the p123_c0 nomenclature chunk at rank 1 plus p135_c2
# life-line doctrine; ON returned three genuine head-line passages) and
# on fingers (1 of 3 OFF results out-of-chapter).
#
# WHY NOT DEEPER UNFILTERED RETRIEVAL INSTEAD: head line's WIDE n=10 arm
# held only 2 in-range chunks; the 8 out-of-range ones are other lines'
# doctrine that does not name its own subject in the text ("If the line
# leave the line of life...", "When the line is quite bare of
# branches..."), so chapter provenance is not recoverable from the text
# an LLM sees -- depth alone cannot substitute for the range gate here.
#
# SCOPE GUARD: palm-feature retrieval, Cheiro book only. Does not touch
# _N_RESULTS_PER_FEATURE, the query template, or any other book's search
# calls.
#
# ACCEPTED GAP: sun line resolved no quality in the onoff_range_gate_S82
# LRH fixture, so its gate behaviour is unmeasured there. Its range holds
# >= 3 chunks per diagnostics/census_feature_page_ranges_S82.md (commit
# a69549a) so it cannot starve, but that is inference, not measurement.
#
# REVERSION: set back to False for a byte-identical pre-S81 retrieval
# path; no other change required.
_FEATURE_PAGE_FILTER_ENABLED = True

_FEATURE_PAGE_RANGES_PATH = (
    Path(__file__).resolve().parent.parent.parent / "data" / "cheiro_feature_pages.json"
)


def _load_feature_page_ranges() -> dict[str, tuple[int, int] | None]:
    """Loads data/cheiro_feature_pages.json. A missing/malformed file, or a
    feature with a null start/end, degrades to unfiltered retrieval for
    that feature (never a crash, never a silent empty result) -- see
    _search_with_page_filter."""
    try:
        raw = json.loads(_FEATURE_PAGE_RANGES_PATH.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001 -- a bad map file must not break the module import
        logger.warning(
            "palm_reading._load_feature_page_ranges: failed to load %s: %s "
            "-- page-range filter will fall through to unfiltered search "
            "for every feature.",
            _FEATURE_PAGE_RANGES_PATH, exc,
        )
        return {}
    ranges: dict[str, tuple[int, int] | None] = {}
    for key, spec in raw.items():
        if key.startswith("_"):  # e.g. "_comment"
            continue
        start, end = spec.get("start"), spec.get("end")
        ranges[key] = (start, end) if start is not None and end is not None else None
    return ranges


_FEATURE_PAGE_RANGES: dict[str, tuple[int, int] | None] = _load_feature_page_ranges()

# ─── Deterministic rule-engine path (offline-verified-extraction pilot) ───
#
# OFF by default. When ON, the Stage-1 claim SOURCE changes -- and only
# that. `prepare_palm_reading` still parses, still retrieves, still runs
# the support gate; `complete_palm_reading` (Stage 2 voicing, display
# checks, decline block, DISCLAIMER, strip) is not touched at all by this
# flag. See `_prepare_claims_from_rules` for the exact substitution.
#
# Env override PALM_RULES_ENGINE=1 forces ON so an A/B dogfood run needs
# no code edit. Read through `_deterministic_rules_enabled()` at CALL
# time, never captured at import time -- same design requirement the palm
# UI gate carries (CLAUDE.md, S72): a test must be able to toggle it with
# monkeypatch.setattr without a module reload.
#
# SCOPE GUARD: this flag governs the claim source inside
# prepare_palm_reading() only. It does not alter retrieval, the support
# gate, the page-range gate, Stage 2, or any validator.
_DETERMINISTIC_RULES_ENABLED: bool = False


def _deterministic_rules_enabled() -> bool:
    """Env override wins over the module constant; the constant is read
    through the module globals so monkeypatch.setattr works."""
    if os.environ.get("PALM_RULES_ENGINE") == "1":
        return True
    return _DETERMINISTIC_RULES_ENABLED


# Phrase-normalization lexicon (see agent/interpretive/phrase_normalizer.py)
# -- config, not hardcoded inline. Same repo-root-derivation pattern as
# _FEATURE_PAGE_RANGES_PATH above; env-overridable so a future lexicon
# revision or an A/B test needs no code edit. Only consulted on the
# deterministic (`_deterministic_rules_enabled()`) path -- see
# `_prepare_claims_from_rules`.
_PALM_LEXICON_PATH = Path(os.getenv(
    "ASTRO_PALM_LEXICON_PATH",
    str(Path(__file__).resolve().parent.parent.parent / "data" / "palm_phrase_lexicon_v1.json"),
))


# THRESHOLD DISCIPLINE (CLAUDE.md Working Style #4).
# Justification: S67 probe-proven -- querying an absence-phrased field
# (e.g. "No clear marks visible") returns junk (markings tables, scores
# 0.33-0.47), not doctrine. A feature is skipped (no query) only when
# EVERY source that mentions it uses one of these phrases; a single
# non-absent mentioning source is enough to proceed to a real query.
# Scope guard: this module's per-feature gate only. Revisit trigger: a
# future pass-3 finding that one of these phrases is itself informative
# for some feature (none observed yet).
#
# F-B (S68 pass-3 Findings #1) UPDATE: this fixed-substring list MISSED
# legitimate word-order variants -- confirmed on real production data
# (diagnostics/dogfood_capture.md's 2026-07-18 RUN blocks). LEFT's real
# MARKS field, "No marks clearly visible.", was NOT caught (the entry
# below is "no clear marks" -- that exact word order -- and this text
# has "marks" BEFORE "clearly", not after), while RIGHT's differently-
# worded "No clear marks such as crosses..." WAS caught -- the SAME
# genuine per-hand absence finding was inconsistently classified,
# letting the feature slip past _is_genuine_negative_absence (which
# requires ALL sources absence-phrased) into a real query that returned
# junk (scores 0.348-0.365, barely above the 0.30 noise floor).
#
# Two-tier fix, not a rewrite -- _ABSENCE_PHRASES (TIER 1, below) is the
# OLD list VERBATIM, just promoted to compiled case-insensitive regex
# (zero behavior change: every string here is `re.escape`d, so each
# pattern matches exactly the same substring the old `in` check did).
# TIER 2 (_ABSENCE_PATTERNS_BY_FEATURE, defined after _SUPPORT_NEEDLES
# below, since it reuses that dict as its noun source) adds NEW
# per-feature noun-anchored "no <optional qualifier> <noun> <anything>
# visible" patterns for cases where the value text explicitly NAMES the
# feature (e.g. "No marks clearly visible."). TIER 1 stays feature-
# agnostic on purpose -- a field's own LABEL already establishes context
# (e.g. "LIFE LINE: Not clearly visible." never says "life" in its
# value), so these short generic markers still need no noun to fire.
_ABSENCE_PHRASES: tuple[re.Pattern, ...] = tuple(
    re.compile(re.escape(phrase), re.IGNORECASE)
    for phrase in (
        "not clearly visible", "no clear marks", "unremarkable",
        "not observed", "not visible", "none",
    )
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


def _is_absence(text: str, feature: str | None = None) -> bool:
    """TIER 1 (_ABSENCE_PHRASES) always runs, feature-agnostic. TIER 2
    (_ABSENCE_PATTERNS_BY_FEATURE, defined below _SUPPORT_NEEDLES) only
    runs when `feature` is given -- `feature=None` is the pre-F-B
    behavior, kept for scripts/probe_fc_retrieval.py's existing
    single-argument call (a diagnostics-only script, out of this
    prompt's scope to touch)."""
    if any(p.search(text) for p in _ABSENCE_PHRASES):
        return True
    if feature is not None:
        pattern = _ABSENCE_PATTERNS_BY_FEATURE.get(feature)
        if pattern is not None and pattern.search(text):
            return True
    return False


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
    ("mount of saturn", "MOUNTS", "Mounts", "saturn"),
    # alias: vision's own established mount vocabulary (this file's
    # system prompt, palm_processor.py) calls this "Mount of...the Sun",
    # not "Apollo" -- needle must match what vision actually emits.
    ("mount of apollo", "MOUNTS", "Mounts", "sun"),
    ("mount of mercury", "MOUNTS", "Mounts", "mercury"),
    # alias: vision emits "Upper Mount of Mars" / "Lower Mount of Mars"
    # (same system prompt), not "positive"/"negative".
    ("mount of mars positive", "MOUNTS", "Mounts", "upper"),
    ("mount of mars negative", "MOUNTS", "Mounts", "lower"),
    # alias: "moon" per instructing prompt -- corpus-attested too (see
    # _SUPPORT_NEEDLES below).
    ("mount of luna", "MOUNTS", "Mounts", "moon"),
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


# S69 F-H P5: claim_extraction.extract_claims / claim_voicing.voice_claims
# both expect ONE string per feature (their own module contracts), but
# _gather_feature_texts returns a LIST of raw per-source texts (one entry
# per LEFT/RIGHT/HAND_DETAIL mention). Joined with " / " -- the SAME
# separator _resolve_feature_quality below already uses to merge multiple
# non-absent qualities for one feature, reused here rather than inventing
# a second joining convention.
def _join_feature_texts(texts_by_feature: dict[str, list[str]]) -> dict[str, str]:
    return {feature: " / ".join(texts) for feature, texts in texts_by_feature.items() if texts}


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

    non_absent = [t for t in raw_texts if not _is_absence(t, feature)]
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
) -> tuple[dict[str, list[dict]], list[str], dict[str, list[tuple]]]:
    """Returns (per_feature_results, failed_features, full_candidates).
    per_feature_results is in _FEATURE_REGISTRY order, every feature
    present as a key (empty list if skipped or the search call failed) --
    this map, not just what's displayed, is the future R3 evidence
    structure, so every assignment is kept even when a chunk_id repeats
    across features.
    full_candidates maps feature -> [(rank, chunk_id, score), ...] for all
    30 results before window slicing when ASTRO_DOGFOOD_CAPTURE=1 (S83
    near-miss margin log); [] in production (flag off) -- no extra fetch
    cost paid outside dogfood capture.

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
    full_candidates: dict[str, list[tuple]] = {}
    failed: list[str] = []
    for feature in _FEATURE_REGISTRY:
        quality = _resolve_feature_quality(feature, texts_by_feature[feature])
        if quality is None:
            results[feature] = []
            full_candidates[feature] = []
            continue
        query = _build_feature_query(feature, quality)
        try:
            if _FEATURE_PAGE_FILTER_ENABLED:
                results[feature], full_candidates[feature] = _search_with_page_filter(feature, query)
            else:
                n_results = 30 if _DOGFOOD_CAPTURE else _N_RESULTS_PER_FEATURE
                all_results = search(
                    query, n_results=n_results, book_name=_CHEIRO_BOOK
                )
                results[feature] = all_results[:_N_RESULTS_PER_FEATURE]
                full_candidates[feature] = [
                    (i + 1, r["chunk_id"], r["score"])
                    for i, r in enumerate(all_results)
                ] if _DOGFOOD_CAPTURE else []
        except Exception as exc:  # noqa: BLE001 -- one bad query must not kill the reading
            logger.warning(
                "palm_reading._retrieve_per_feature: search failed for "
                "feature=%r: %s", feature, exc,
            )
            failed.append(feature)
            results[feature] = []
            full_candidates[feature] = []
    return results, failed, full_candidates


def _search_with_page_filter(feature: str, query: str) -> tuple[list[dict], list[tuple]]:
    """S82 page-range gate (flag-gated by _FEATURE_PAGE_FILTER_ENABLED,
    default OFF -- see that constant's own comment). Makes exactly ONE
    search() call per feature: a feature with no verified range
    (_FEATURE_PAGE_RANGES[feature] is None) searches book_name only; a
    feature with a verified range pushes it into the SAME call as a
    page_ref=(start, end) Chroma where-clause filter, enforced server-side
    rather than a Python-side post-filter over a widened pool.

    Returns (sliced_results, full_candidates). full_candidates is
    [(rank, chunk_id, score), ...] for all 30 results before window slicing
    when ASTRO_DOGFOOD_CAPTURE=1 (S83 near-miss margin log); [] in
    production (flag off).

    A range matching nothing in-chapter now yields an empty list for that
    feature -- this is not swallowed here; _retrieve_per_feature's existing
    empty-result handling routes it to the decline block gracefully. The
    empty case is logged at info level (a ratified graceful outcome, not
    a fault)."""
    n_results = 30 if _DOGFOOD_CAPTURE else _N_RESULTS_PER_FEATURE
    page_range = _FEATURE_PAGE_RANGES.get(feature)
    if page_range is None:
        all_results = search(query, n_results=n_results, book_name=_CHEIRO_BOOK)
    else:
        start, end = page_range
        all_results = search(
            query, n_results=n_results, book_name=_CHEIRO_BOOK,
            page_ref=(start, end),
        )
        if not all_results:
            logger.info(
                "palm_reading._search_with_page_filter: no chunk in verified range "
                "%s-%s for feature %r -- feature will decline (not an error).",
                start, end, feature,
            )
    sliced = all_results[:_N_RESULTS_PER_FEATURE]
    full_candidates = [
        (i + 1, r["chunk_id"], r["score"])
        for i, r in enumerate(all_results)
    ] if _DOGFOOD_CAPTURE else []
    return sliced, full_candidates


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
    "mount of saturn": ("saturn",),
    # both corpus-attested for this mount (cheiro_clean_v1.json p112:
    # "THE MOUNT OF THE SUN... also called the Mount of Apollo").
    "mount of apollo": ("apollo", "sun"),
    "mount of mercury": ("mercury",),
    # Cheiro's own prose (p113) calls these "the first"/"the second"
    # mount of this name, never "positive"/"negative" or "upper"/
    # "lower" -- no single-word needle in the corpus text can tell them
    # apart, so both share the same needle. Accepted imprecision, not
    # silently patched: a chunk mentioning either Mars mount will
    # support-gate-pass for both features. Flagged in diagnostics/
    # latest_run.md, not a new mechanism.
    "mount of mars positive": ("mars",),
    "mount of mars negative": ("mars",),
    # both corpus-attested (p113 "THE MOUNT OF LUNA"; p191 "Mount of
    # the Moon").
    "mount of luna": ("luna", "moon"),
    "markings/other features": (
        "mark", "star", "cross", "island", "square", "circle", "hair",
    ),
}

# F-B (S68 pass-3 Findings #1) TIER 2: per-feature noun-anchored absence
# patterns, reusing _SUPPORT_NEEDLES as the SAME single source of truth
# for each feature's noun (not a new, separately-maintained noun list --
# "mark"/"life"/"venus" etc. already mean "this word names the feature"
# everywhere else in this module). "marking" is added ONLY for the
# markings feature (`_ABSENCE_NOUN_EXTRAS` below) -- a natural inflection
# of "mark" (confirmed on real production data: HAND_DETAIL's own
# "There are no unusual markings or features visible on the hand."),
# not a generalizable pattern worth adding to _SUPPORT_NEEDLES itself
# (that dict scores CHUNK relevance, a different, unrelated use).
#
# Pattern shape: "no" + 0-3 filler words + (noun, optional trailing "s")
# + 0-6 filler words + "visible" -- deliberately requires the noun
# BETWEEN "no" and "visible", per-FEATURE (not a generic "no...visible"
# match). This is the conservative-by-construction guard the design
# calls for: real production LIFE/HEAD/HEART LINE text reads "no
# breaks, chains, forks, or islands visible" (line-QUALITY detail, not
# feature absence) -- since "life"/"head"/"heart" never appear in that
# clause, and this module checks each feature against ONLY its own
# noun, that sentence correctly does NOT match for any of those three
# features, even though "island" (a DIFFERENT feature's -- markings' --
# own needle) is literally present in the text. Verified against this
# exact live sentence (diagnostics/dogfood_capture.md's 2026-07-18 RUN
# blocks), not a synthetic case.
_ABSENCE_NOUN_EXTRAS: dict[str, tuple[str, ...]] = {
    "markings/other features": ("marking",),
}


def _build_absence_noun_pattern(needles: tuple[str, ...]) -> re.Pattern:
    """F-E (S70): filler-word hops -- including the mandatory connector
    immediately before the noun -- tolerate an optional leading [,;]
    (list-phrased fields like "No crosses, stars, grilles, squares, or
    moles clearly visible" -- a comma is not \\s, so the pre-F-E hops
    (?:\\s+\\w+) could not cross one; e.g. "squares" is the only needle
    in that sentence reachable by \\bnoun\\b -- "crosses" fails since
    \\b cannot fire between "cross" and the following "es", both \\w --
    so the connector right before the noun match must ALSO cross the
    comma preceding "squares"). An optional [,;] is also tolerated
    immediately after the matched noun, before the post-noun filler
    resumes. Repetition counts ({0,3}/{0,6}) UNCHANGED."""
    noun_alt = "|".join(re.escape(n) for n in needles)
    return re.compile(
        rf"\bno\b(?:[,;]?\s+\w+){{0,3}}[,;]?\s+(?:{noun_alt})s?\b[,;]?"
        rf"(?:[,;]?\s+\w+){{0,6}}\s+visible\b",
        re.IGNORECASE,
    )


_ABSENCE_PATTERNS_BY_FEATURE: dict[str, re.Pattern] = {
    feature: _build_absence_noun_pattern(needles + _ABSENCE_NOUN_EXTRAS.get(feature, ()))
    for feature, needles in _SUPPORT_NEEDLES.items()
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
    non-absent quality was observed (e.g. "Barely visible" is not caught
    by _ABSENCE_PHRASES or _ABSENCE_PATTERNS_BY_FEATURE) even if no
    chunk ends up supporting it -- that is a doctrine-coverage gap, not
    a negative finding."""
    if not raw_texts:
        return False
    return all(_is_absence(t, feature) for t in raw_texts)


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


# S69 F-H P5: Stage 2 (claim_voicing.py) tags its own output with a
# DIFFERENT vocabulary ({[C<n>], [OBS], [FLOW]}) than CHUNK_ANCHOR_TAG_
# PATTERN above recognizes (only [OBS] or a full [<book>_p<n>_c<n>]
# chunk-id token) -- strip_generation_tags() would silently leave
# Stage-2's own tags in the displayed text if reused as-is. Duplicated
# (not imported) from claim_voicing._VOICE_TAG_PATTERN -- reaching into
# another module's PRIVATE (underscore) pattern would be worse than a
# cited duplicate; same "duplicate + cite" convention claim_extraction.py
# itself already used for this module's own _READING_TIMEOUT_SECONDS.
_STAGE2_TAG_PATTERN = re.compile(r"\[(?:C\d+|OBS|FLOW)\]")


def _strip_stage2_tags(text: str) -> str:
    """Stage-2 analog of strip_generation_tags() -- same whitespace
    cleanup logic, different tag vocabulary. CHUNK_ANCHOR_TAG_PATTERN /
    strip_generation_tags() are left untouched (retired-but-defined, see
    the module docstring's S69 F-H P5 note) -- a future close-out pass,
    not this one, decides whether to delete or merge them.

    Raises:
        RuntimeError: the strip operation itself fails for any reason --
                      same fail-loud contract as strip_generation_tags().
    """
    try:
        stripped = _STAGE2_TAG_PATTERN.sub("", text)
        stripped = re.sub(r"[ \t]{2,}", " ", stripped)
        stripped = re.sub(r"[ \t]+\n", "\n", stripped)
        stripped = re.sub(r"[ \t]+$", "", stripped)
        return stripped
    except Exception as exc:
        raise RuntimeError(
            f"palm_reading._strip_stage2_tags: failed to strip "
            f"voice tags from generation output: {exc}"
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


def _run_display_checks(
    stripped_text: str,
    context_corpus: str,
    unsupported_features: tuple[str, ...],
) -> list[str]:
    """S69 F-H P5: the six 'display' checks that survive the two-stage
    wiring -- see the module docstring's RETIRED-NOT-DELETED note for why
    V-1/V-2 (_check_tag_completeness/_check_anchor_legality) are NOT
    called here. Runs on the STRIPPED Stage-2 output (_strip_stage2_tags,
    not strip_generation_tags -- different tag vocabulary). Unlike
    _run_ring1_checks, there is no separate raw-tagged input surface to
    preserve: nothing downstream needs to see claim_voicing's own
    [C<n>]/[OBS]/[FLOW] tags after this point -- that contract is
    claim_voicing.py's own V-3/V-4/V-5's business, already validated
    inside voice_claims() itself."""
    failures: list[str] = []
    failures += _check_jargon(stripped_text)
    failures += _check_self_help_register(stripped_text)
    failures += _check_unsupported_dates(stripped_text, context_corpus)
    failures += _check_length(stripped_text)
    failures += _check_banned_feature_mentions(stripped_text, unsupported_features)
    failures += _check_exemplar_echo(stripped_text)
    return failures


def _compute_decline_features(
    supported_features: tuple[str, ...],
    unsupported_features: tuple[str, ...],
    extraction_failed_features: tuple[str, ...],
    claims: tuple[Claim, ...],
) -> tuple[str, ...]:
    """S69 F-H P5: decline set = union of (a) gate-unsupported features,
    (b) features Stage 1 (extract_claims) failed to extract at all after
    its own retry, and (c) gate-supported features whose Stage-1 claims
    are ALL excluded_from_voice OR whose claims list is simply empty (a
    legitimate Stage-1 outcome, per claim_extraction.py's own tests) --
    "honest decline over silence" for the zero-claim-but-supported case,
    per this prompt's own instruction. Registry order, deduped via a
    `seen` set then re-derived by filtering _FEATURE_REGISTRY (not
    insertion order) -- same convention supported_features/
    unsupported_features already use."""
    claims_by_feature: dict[str, list[Claim]] = {}
    for c in claims:
        claims_by_feature.setdefault(c.feature, []).append(c)

    seen: set[str] = set()
    for feature in unsupported_features:
        seen.add(feature)
    for feature in extraction_failed_features:
        seen.add(feature)
    for feature in supported_features:
        feature_claims = claims_by_feature.get(feature, [])
        if not feature_claims:
            logger.info(
                "palm_reading._compute_decline_features: feature %r was "
                "gate-supported but produced zero Stage-1 claims -- "
                "declining honestly rather than silently omitting it.",
                feature,
            )
            seen.add(feature)
        elif all(c.excluded_from_voice for c in feature_claims):
            seen.add(feature)

    return tuple(f for f in _FEATURE_REGISTRY if f in seen)


def _build_sources_from_claims(
    reading_text_tagged: str,
    claims: tuple[Claim, ...],
    gated_results: dict[str, list[dict]],
) -> tuple[dict, ...]:
    """S69 F-H P5: sources rebuilt per-claim, not per-gated-chunk -- the
    OLD sources list included EVERY chunk fed to the (single) generation
    prompt regardless of whether it was actually used; this is a
    deliberate tightening, not an oversight. Only claim_ids Stage 2
    ACTUALLY CITED (a [C<n>] tag present in the final `reading_text_
    tagged`) contribute a source -- claims dropped by claim_voicing's own
    input filter (excluded_from_voice, corrective-overflow) or never
    cited in a failing draft are excluded. Deduped by (chunk_id, feature),
    in stable order = order of first citation in the text (the same order
    a reader encounters them)."""
    claims_by_id = {c.claim_id: c for c in claims}
    chunk_lookup = {
        (feature, c["chunk_id"]): c
        for feature, chunks in gated_results.items()
        for c in chunks
    }

    seen: set[tuple[str, str]] = set()
    sources: list[dict] = []
    for match in _STAGE2_TAG_PATTERN.finditer(reading_text_tagged):
        tag = match.group(0)
        if not tag.startswith("[C"):
            continue
        claim = claims_by_id.get(tag[1:-1])
        if claim is None:
            continue
        key = (claim.chunk_id, claim.feature)
        if key in seen:
            continue
        chunk = chunk_lookup.get((claim.feature, claim.chunk_id))
        if chunk is None:
            continue
        seen.add(key)
        sources.append({
            "book": chunk["book_name"],
            "page": chunk["page_ref"],
            "score": chunk["score"],
            "feature": claim.feature,
        })
    return tuple(sources)


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
    # S69 F-H P5 additions (additive only, all default so any pre-P5
    # construction site keeps working unmodified -- same convention
    # reading_text_tagged's own default already established).
    #   claims: the FULL Stage-1 extraction inventory (claim_extraction.
    #     ExtractionResult.claims verbatim) -- every claim, including
    #     ones excluded_from_voice or dropped by claim_voicing's
    #     corrective-overflow cap, kept here for transparency/future
    #     tooling (e.g. P6's dogfood checkpoint), not just what made it
    #     into the final voiced reading.
    #   stage1_retry_features: registry-order tuple of features whose
    #     Stage-1 extraction call needed its own F2c retry.
    #   stage2_retry_used: whether Stage 2's single whole-reading F2c
    #     retry fired.
    #   retry_used above is COMPAT: true if EITHER stage retried, so any
    #   pre-P5 caller reading retry_used alone still gets a meaningful
    #   answer ("was anything retried at all"), just coarser than the two
    #   new fields.
    claims: tuple[Claim, ...] = ()
    stage1_retry_features: tuple[str, ...] = ()
    # S78 E2 step 2b: per-feature Stage-1 diagnostic dicts (call_count,
    # retry_used, attempt_1_status/attempt_1_claim_count, attempt_2_status/
    # attempt_2_claim_count, final_outcome, status, error/failures, etc. --
    # verbatim claim_extraction.ExtractionResult.diagnostics["features"]),
    # carried through so the happy-path dogfood capture can reach them --
    # previously only reachable via the checkpoint-declined capture path
    # (prep.diagnostics directly), never from a completed PalmReadingResult.
    # dict, not Mapping, matching this file's existing convention (e.g.
    # `sources: tuple[dict, ...]` above, `PalmReadingPrep.diagnostics: dict`
    # below) -- Mapping is not imported anywhere in this module.
    stage1_feature_diagnostics: dict[str, dict[str, object]] = field(default_factory=dict)
    stage2_retry_used: bool = False
    # S70 (retry attribution): the FIRST-attempt failure list that drove
    # Stage 2's retry -- claim_voicing.voice_claims' own diagnostics
    # dict's "first_attempt_failures" key, verbatim, empty tuple when
    # absent (a clean first draft, no retry needed). Same additive-
    # defaulted convention as reading_text_tagged/claims/stage1_retry_
    # features/stage2_retry_used above -- any pre-S70 construction site
    # keeps working unmodified. Distinct from `validation.failures`
    # (the FINAL verdict, on whichever draft actually shipped): this
    # field answers "what was wrong on attempt 1" even when the retry
    # fully cleared it and the final result passed cleanly --
    # `stage2_retry_used=True` alone doesn't say WHY the retry fired;
    # this field does. Motivated directly by pass-5 preflight's own
    # documented gap (diagnostics/pass5_preflight_S70.md's post-F-G and
    # post-F-G3 addenda): a clean final PASS with stage2_retry_used=True
    # left no way to tell whether the retry was exemplar-echo-related or
    # something else entirely.
    stage2_first_attempt_failures: tuple[str, ...] = ()


@dataclass(frozen=True)
class PalmReadingPrep:
    """S69 F-H P5 two-phase seam: everything `prepare_palm_reading()`
    computes before Stage 2 ever runs -- retrieval, the support gate, and
    Stage 1 (claim_extraction.extract_claims) itself. `complete_palm_
    reading()` consumes this to run Stage 2 + display checks + decline +
    DISCLAIMER + strip. Exists so a FUTURE prompt (P6) can insert a human
    checkpoint on the Stage-1 claims inventory between the two calls --
    not used for that here, just the seam.

    diagnostics carries Stage-1's own diagnostics dict verbatim under
    "stage1" (per-feature call_count/retry_used/overlap_scores/exclusion_
    ledger, see claim_extraction.ExtractionResult.diagnostics) PLUS two
    keys this module's own complete_palm_reading() needs but that aren't
    naturally part of a "prep" field list: "stage1_failed_features"
    (tuple, extract_claims' own failed_features) and
    "stage1_retry_features" (tuple, registry-order, derived from the
    per-feature diagnostics -- computed once here rather than re-derived
    at complete-time)."""
    gated_results: dict[str, list[dict]]
    supported_features: tuple[str, ...]
    unsupported_features: tuple[str, ...]
    claims: tuple[Claim, ...]
    texts_by_feature: dict[str, str]
    diagnostics: dict = field(default_factory=dict)


def _enabled_features_from_rules(rules) -> frozenset[str]:
    """The ontology feature set the rule engine can ACTUALLY consume, from
    the loaded rule set itself -- never a hardcoded list, so adding a rule
    chapter widens the extractor's allow-list with no edit here.

    DEVIATION, flagged not silent (project convention): the instructing
    prompt specifies "the set of ontology features that appear as
    antecedent `.feature`". This also unions in `.comparator_feature`.
    Reason: a comparative antecedent (`condition_type == "comparative"`)
    reads `magnitudes[comparator_feature]`, and magnitudes are derived by
    `to_tokens()` from the payload -- so withholding a comparator-only
    feature would silently starve the very rule that needs it, which is
    the exact silent-failure class this rewire exists to remove. MEASURED
    NO-OP on the current rule set: both comparator features ("Line of
    Head", "Line of Heart") already appear as antecedent `.feature`, so
    the derived set is byte-identical either way today.
    """
    features: set[str] = set()
    for rule in rules:
        for antecedent in rule.antecedents:
            if antecedent.feature:
                features.add(antecedent.feature)
            if antecedent.comparator_feature:
                features.add(antecedent.comparator_feature)
    return frozenset(features)


def rule_engine_enabled_features() -> frozenset[str]:
    """Convenience wrapper over `_enabled_features_from_rules` that loads
    the rule set itself -- for callers/tests that want the allow-list
    without running a reading. `_prepare_claims_from_rules` does NOT use
    this (it derives from the rule set it already loaded, so one run never
    reads the rule files twice)."""
    from agent.interpretive import palm_rules_table  # local -- see _prepare_claims_from_rules

    return _enabled_features_from_rules(palm_rules_table.load_rule_set())


def _observation_record_diagnostics(record, enabled_features) -> dict:
    """Plain-dict, JSON-serializable projection of the FULL
    `ObservationRecord` -- the diagnostic surface a silent feature has to
    be traceable through.

    Captures what the payload alone cannot answer: `tokens` (what became
    a token), `unmapped` (the LLM saw it but no ontology token existed for
    it), `raw_prose` (what the LLM was given at all), `dropped_disabled`
    (extracted fine, withheld by `enabled_features`) and
    `unmappable_prose_features` (prose labels with no ontology counterpart
    -- never sent to the LLM). "LLM saw nothing" and "no token existed for
    what it saw" are distinguishable from this block; from the payload
    alone they are not.

    `dropped_disabled` is ALWAYS empty on `_prepare_claims_from_rules`'s
    call path (see that function's ALL-FEATURES UNBLOCK docstring note):
    `enabled_features` there is `observation_extractor.
    all_aliased_features()`, the full set the extractor can ever produce,
    so nothing it captures can fall outside it. A feature having no rule
    behind it now shows up as zero fired rules, not as a withheld feature
    here.

    ROUTING: this rides inside `engine_diagnostics`, exactly as
    `suppression_log` already does -- so it reaches
    `prep.diagnostics["rules_engine"]` AND
    `stage1.features["_rules_engine"]` (and thus the dogfood capture /
    S83 net) with no new channel. It is NEVER passed to Stage 2:
    `complete_palm_reading` hands `voice_claims` claims + texts only, and
    nothing in this dict is read there.
    """
    return {
        "enabled_features": sorted(enabled_features),
        "features": {
            feature: {
                "tokens": dict(fobs.tokens),
                "unmapped": [dict(u) for u in fobs.unmapped],
                "raw_prose": fobs.raw_prose,
            }
            for feature, fobs in record.features.items()
        },
        "dropped_disabled": list(record.dropped_disabled),
        "unmappable_prose_features": [dict(u) for u in record.unmappable_prose_features],
    }


_EMPTY_OBSERVATION_RECORD_DIAGNOSTICS: dict = {
    "enabled_features": [],
    "features": {},
    "dropped_disabled": [],
    "unmappable_prose_features": [],
}


def _json_safe_targets(targets: dict[str, dict[str, object]]) -> dict[str, dict[str, object]]:
    """Converts any set/frozenset leaf value in `targets` to a SORTED list so
    engine_diagnostics["targets"] stays JSON-serializable (Pattern D
    readiness, S98) -- applied ONLY at this diagnostics-export boundary; the
    real `targets` dict passed to palm_rules_table.match() is untouched, so
    the engine's set-membership semantics stay intact everywhere else. A
    no-op today (every stored value is still a scalar); becomes load-bearing
    once extract_relations starts emitting set-valued Convergence (Pattern D
    step 3)."""
    return {
        feature: {
            attr: sorted(value) if isinstance(value, (set, frozenset)) else value
            for attr, value in attrs.items()
        }
        for feature, attrs in targets.items()
    }


def _prepare_claims_from_rules(
    raw_texts_by_feature: dict[str, list[str]],
    client=None,
    targets: dict[str, dict[str, str]] | None = None,
    proximity_observations: dict[str, dict[str, str]] | None = None,
    mount_development: dict[str, dict[str, str]] | None = None,
) -> tuple[tuple[Claim, ...], dict]:
    """Deterministic replacement for `claim_extraction.extract_claims` as
    the Stage-1 claim SOURCE (flag-gated, see
    `_deterministic_rules_enabled`). Returns (claims, engine_diagnostics).

    Chain: palm_rules_table.load_rule_set ->
    observation_extractor.extract_observation (the ONE LLM call on this
    path -- prose -> capture-complete `ObservationRecord`; its
    `enabled_features` allow-list is `observation_extractor.
    all_aliased_features()`, NOT derived from the loaded rule set -- see
    ALL-FEATURES UNBLOCK below) ->
    observation_extractor.to_vision_payload (record -> the
    `{feature: {attribute: {value, confidence}}}` shape, allow-list
    applied here) -> observation_to_tokens.to_tokens ->
    palm_rules_table.match / resolve_priority ->
    rule_to_claim.claims_from_rules. `proximity_observations` (built by
    the caller, see `prepare_palm_reading`) merges into the flat
    `observation` dict immediately after `to_tokens`, before `match` --
    see the tripwire comment at that merge site for why it cannot be
    folded into the `to_vision_payload`/`to_tokens` leg of this chain.

    FAIL-CLOSED, no silent LLM fallback -- but SCOPED, not blanket. Four
    boundaries, deliberately different:
      1. rule load: broad catch -> honest decline (a missing/malformed
         rule dir is an operational condition). The extractor's
         `enabled_features` allow-list is derived here too, but from
         `observation_extractor.all_aliased_features()` (every ontology
         feature the LLM call can ever produce), NOT from the loaded rule
         set -- see the ALL-FEATURES UNBLOCK note below.
      2. `extract_observation`: catches RuntimeError (LLM/API failure) and
         ValueError (unparseable LLM response) ONLY -- the two failures
         that module documents. Anything else (e.g. a TypeError from a
         changed signature) PROPAGATES.
      3. the record -> payload -> tokens adapter seam: NOT caught at all.
         A TypeError/ValueError here can only mean the extractor's return
         contract and this call site disagree -- exactly the break that
         the previous blanket `except Exception` masked as "engine
         produced zero claims" for the whole of this branch's life (10
         tests passed OFF, the ON path silently declined every run). It
         must fail loudly in tests, not decline.
      4. match / resolve_priority / claims_from_rules: broad catch ->
         honest decline (unchanged).
    Every caught exception is recorded as `error` + `failed_stage` in the
    diagnostics, so even a broad catch cannot hide WHERE it broke.

    Zero claims is an already-supported, already-tested pipeline state --
    `voice_claims` makes zero LLM calls on an empty inventory and
    `_compute_decline_features` declines every supported feature -- so the
    caller gets an honest decline-only reading. Deliberately NOT a
    fallback to `extract_claims`: a silent fallback would make engine
    breakage invisible, which is the whole point of running this A/B.

    Imports are LOCAL, not module-level: `observation_extractor` and
    `observation_to_tokens` both read data/ontology_registry.json at
    import time, and a flag-OFF run must not acquire that dependency (or
    its failure mode) merely by importing this module.

    ALL-FEATURES UNBLOCK: `enabled_features` passed to `extract_observation`
    / `to_vision_payload` is `observation_extractor.all_aliased_features()`
    -- every ontology feature the LLM extraction call can ever produce --
    not the narrower rule-derived set (`_enabled_features_from_rules`,
    still available standalone via `rule_engine_enabled_features()` for
    introspection, just no longer fed into this seam). Rules currently only
    exist for a subset of those features; the rest are captured and reach
    `observation`/diagnostics same as any other feature, but fire no rules
    -- an honest decline visible in the record, rather than a feature
    silently withheld before the engine ever saw it. `dropped_disabled` is
    therefore always empty on this path: nothing the extractor can produce
    falls outside its own allow-list by construction.
    """
    engine_diagnostics: dict = {"enabled": True, "failed": False}

    def _fail_closed(exc: Exception, stage: str, record_diagnostics: dict):
        logger.error(
            "palm_reading._prepare_claims_from_rules: deterministic rule "
            "engine failed at stage %r (%s: %s) -- failing closed to zero "
            "claims; the LLM extraction path is NOT used as a fallback.",
            stage, type(exc).__name__, exc,
        )
        engine_diagnostics.update({
            "failed": True,
            "failed_stage": stage,
            "error": f"{type(exc).__name__}: {exc}",
            "observation": {},
            "dropped_tokens": [],
            "fired_rule_ids": [],
            "surviving_rule_ids": [],
            # suppression_log key always present, even on failure, so a
            # reader never has to distinguish "no suppressions" from
            # "diagnostics dropped the key". Same for observation_record.
            "suppression_log": [],
            "observation_record": record_diagnostics,
            "citations": {},
            "dropped_rule_ids": [],
            "phrase_promotions": [],
            "targets": {},
            "proximity_observations": {},
            "mount_development": {},
        })
        return (), engine_diagnostics

    try:
        from agent.interpretive import (  # local -- see docstring
            observation_extractor,
            observation_to_tokens,
            palm_rules_table,
            phrase_normalizer,
            rule_to_claim,
        )

        rules = palm_rules_table.load_rule_set()
        # ALL-FEATURES UNBLOCK (see docstring): NOT
        # _enabled_features_from_rules(rules) -- that narrower,
        # rule-derived set stays available standalone via
        # rule_engine_enabled_features(), just no longer feeds this seam.
        enabled_features = observation_extractor.all_aliased_features()
    except Exception as exc:  # noqa: BLE001 -- fail-closed boundary 1, see docstring
        return _fail_closed(exc, "rule_load", dict(_EMPTY_OBSERVATION_RECORD_DIAGNOSTICS))

    try:
        record = observation_extractor.extract_observation(
            raw_texts_by_feature, enabled_features=set(enabled_features), client=client
        )
    except (RuntimeError, ValueError) as exc:  # fail-closed boundary 2 -- NARROW
        return _fail_closed(
            exc, "observation_extraction",
            {**_EMPTY_OBSERVATION_RECORD_DIAGNOSTICS,
             "enabled_features": sorted(enabled_features)},
        )

    try:
        promotions = phrase_normalizer.normalize(record, _PALM_LEXICON_PATH)
    except RuntimeError as exc:  # fail-closed boundary 2b -- NARROW, same pattern as boundary 2
        # `record` is guaranteed unmutated here: phrase_normalizer.normalize
        # only raises RuntimeError out of its own lexicon load step, which
        # runs before any promotion is applied -- so the real extraction
        # diagnostics (not the empty placeholder) are still meaningful.
        return _fail_closed(
            exc, "phrase_normalization",
            _observation_record_diagnostics(record, enabled_features),
        )

    record_diagnostics = _observation_record_diagnostics(record, enabled_features)

    # Boundary 3: NO try/except by design (see docstring). A contract
    # mismatch between extract_observation's return type and this seam
    # must raise, not decline.
    vision_payload = observation_extractor.to_vision_payload(record, enabled_features)
    observation, magnitudes = observation_to_tokens.to_tokens(vision_payload)

    # P (proximity degree) merges into the FLAT observation AFTER to_tokens on purpose:
    # 'touching' is NOT in the registry value pool, so routing it through to_tokens'
    # _VALID_TRIPLES would silently drop it and kill H_027. attribute_value_binding does
    # NOT fix this (to_tokens never reads it). Do not move this merge upstream of to_tokens.
    # P-wins over any LLM-emitted Proximity: P is the deterministic degree parser.
    for feature, attrs in (proximity_observations or {}).items():
        observation.setdefault(feature, {})["Proximity"] = attrs["Proximity"]

    # S117: mount Development grades merge into the FLAT observation the
    # SAME way and for the SAME reason as Proximity immediately above --
    # extract_mount_development's per-mount menu enforcement already
    # happened upstream (observation_extractor._MOUNT_DEVELOPMENT_MENUS),
    # independent of to_tokens'/attribute_value_binding's global gate, so
    # this merge must land AFTER to_tokens, not be routed through it.
    # Development (deterministic) wins over any LLM-emitted Development
    # value on collision, mirroring "P-wins over any LLM-emitted
    # Proximity" above exactly.
    for feature, attrs in (mount_development or {}).items():
        observation.setdefault(feature, {})["Development"] = attrs["Development"]

    try:
        fired = palm_rules_table.match(observation, magnitudes, rules, targets=targets)
        survivors, suppression_log = palm_rules_table.resolve_priority(fired)
        claims, rule_diagnostics = rule_to_claim.claims_from_rules(survivors, magnitudes=magnitudes)
    except Exception as exc:  # noqa: BLE001 -- fail-closed boundary 4, see docstring
        return _fail_closed(exc, "rule_matching", record_diagnostics)

    engine_diagnostics.update({
        "observation_record": record_diagnostics,
        "observation": observation,
        "targets": _json_safe_targets(targets or {}),
        "proximity_observations": proximity_observations or {},
        "mount_development": mount_development or {},
        "dropped_tokens": magnitudes.get("_dropped", []),
        "fired_rule_ids": [r.rule_id for r in fired],
        "surviving_rule_ids": [r.rule_id for r in survivors],
        "suppression_log": suppression_log,
        # source_quote lives HERE and nowhere else -- rule_to_claim keeps
        # it off the Claim object precisely so 19th-century book prose
        # never reaches claim_voicing's prompt (claim_voicing.py's own
        # "chunk text never appears in the prompt" invariant).
        "citations": rule_diagnostics.get("citations", {}),
        "dropped_rule_ids": rule_diagnostics.get("dropped_rule_ids", []),
        # RESOLVED (rule_to_claim.py, commit d4c748d): rule_to_claim
        # now maps Claim.feature through _TOPIC_GROUP_TO_FEATURE before
        # it ever reaches this module, so it IS a real _FEATURE_REGISTRY
        # label ("head line", not "line_head") -- fail-closed at that
        # module's own load time (_assert_topic_groups_mapped), so a
        # future rule chapter with an unmapped topic_group breaks loudly
        # there, not silently here. Consequence #1 this comment used to
        # flag (_compute_decline_features mismatching every registry
        # feature) is therefore also resolved, and this module's own
        # jurisdiction-narrowing step (_prepare_deterministic_prep, just
        # above the caller) depends directly on that reliability. This
        # diagnostic key stays as a live CI-visible tripwire regardless
        # -- see test_claim_features_outside_registry_is_recorded.
        # Consequence #2 REMAINS OPEN, unrelated to and NOT fixed by this
        # task: _build_sources_from_claims still looks each claim's
        # chunk_id up in gated_results (this run's retrieval), which a
        # rule-resolved chunk_id (from the corpus file, not this run's
        # retrieval) will generally miss, so `sources` still comes back
        # empty for rule-fired claims -- the real citations still live in
        # the "citations" key above. Out of this task's scope (support-
        # gate jurisdiction only); tracked separately.
        "claim_features_outside_registry": sorted(
            {c.feature for c in claims} - set(_FEATURE_REGISTRY)
        ),
        # AI-assisted mapping must never be invisible (CLAUDE.md Working
        # Style #5) -- every phrase->token promotion this run made, for the
        # dogfood capture / S83 net, same routing as suppression_log above.
        "phrase_promotions": promotions,
    })
    return claims, engine_diagnostics


def _prepare_deterministic_prep(
    raw_texts_by_feature: dict[str, list[str]],
    texts_by_feature: dict[str, str],
    gated_results: dict[str, list[dict]],
    supported_features: tuple[str, ...],
    unsupported_features: tuple[str, ...],
    full_candidates: dict[str, list],
    client=None,
    targets: dict[str, dict[str, str]] | None = None,
    proximity_observations: dict[str, dict[str, str]] | None = None,
    mount_development: dict[str, dict[str, str]] | None = None,
) -> PalmReadingPrep:
    """Builds the SAME PalmReadingPrep shape the LLM Stage-1 path builds,
    with `claims` sourced from the deterministic rule engine. Everything
    else on the prep -- gated_results, the support-gate tuples,
    texts_by_feature -- is passed through untouched, so
    `complete_palm_reading` needs no knowledge of this path and is not
    edited by this flag at all.

    DIAGNOSTICS ROUTING (the prompt's AI-reviewing-AI visibility
    requirement): the engine block, `suppression_log` included, is written
    to BOTH
      - prep.diagnostics["rules_engine"] -- for a caller holding the prep
        (e.g. the S70 P6b checkpoint step), and
      - prep.diagnostics["stage1"]["features"]["_rules_engine"] -- the
        one channel that already reaches `PalmReadingResult` (via
        `complete_palm_reading`'s existing `.get("stage1", {}).get(
        "features", {})` read, unmodified), so the dogfood capture and
        the S83 failure-capture net see it with no frontend change.
    The `_`-prefixed pseudo-feature key follows the same convention
    `observation_to_tokens`'s own `magnitudes["_dropped"]` uses. It is
    read defensively by every consumer (`app._format_stage1_feature_
    diagnostics_lines` / `_run_had_failure` are all `.get()`-based), and
    `final_outcome` is deliberately set to a string containing "failed"
    on engine failure so S83's threshold-free capture net fires on a
    broken engine without any edit to frontend/app.py.

    Per-feature retrieval `candidates` (the S83 near-miss margin log) are
    merged in exactly as the LLM path does -- retrieval still ran on this
    path, so dropping that record would be a silent loss.
    """
    claims, engine_diagnostics = _prepare_claims_from_rules(
        raw_texts_by_feature, client=client, targets=targets,
        proximity_observations=proximity_observations,
        mount_development=mount_development,
    )
    engine_diagnostics["final_outcome"] = (
        "rules_engine_failed" if engine_diagnostics.get("failed") else "rules_engine_ok"
    )

    # JURISDICTION FIX (ratified design decision): the retrieval support
    # gate's authority covers RETRIEVAL-sourced claims only. A feature
    # with a SURVIVING rule claim (post resolve_priority -- `claims` here
    # is exactly that, per rule_to_claim.claims_from_rules) is
    # self-grounded by its own citation (source_quote/source_page in the
    # engine_diagnostics["citations"] side-channel) and needs no
    # retrieval chunk to voice, so it does not belong in EITHER gate
    # tuple -- same "belongs in neither" shape _is_genuine_negative_
    # absence already established for the honest-absence case, extended
    # here rather than replaced. This is the ONE authoritative narrowing
    # point: every downstream consumer (_check_banned_feature_mentions
    # via _build_display_extra_validators/_run_display_checks,
    # _compute_decline_features, and PalmReadingResult.supported_
    # features/unsupported_features itself) reads prep.supported_
    # features/prep.unsupported_features and NOTHING upstream of this
    # assignment, so narrowing here covers all three by construction. A
    # feature with BOTH a surviving rule claim and real retrieval support
    # is removed from BOTH tuples too (rule-sourced jurisdiction wins
    # outright, not merely on conflict) -- Claim.feature is a reliable
    # _FEATURE_REGISTRY token here (rule_to_claim._TOPIC_GROUP_TO_FEATURE,
    # fail-closed at that module's own load time), so no further mapping
    # is needed. _apply_support_gate's own per-retrieval-feature scoring
    # is untouched -- this only narrows its OUTPUT tuples, never how a
    # feature without a surviving rule claim gets classified.
    features_with_surviving_rule_claims = {c.feature for c in claims}
    supported_features = tuple(
        f for f in supported_features if f not in features_with_surviving_rule_claims
    )
    unsupported_features = tuple(
        f for f in unsupported_features if f not in features_with_surviving_rule_claims
    )

    stage1_features: dict[str, dict] = {
        feature: {"candidates": candidates}
        for feature, candidates in full_candidates.items()
    }
    stage1_features["_rules_engine"] = engine_diagnostics

    return PalmReadingPrep(
        gated_results=gated_results,
        supported_features=supported_features,
        unsupported_features=unsupported_features,
        claims=claims,
        texts_by_feature=texts_by_feature,
        diagnostics={
            "stage1": {"features": stage1_features},
            # No LLM extraction ran, so there is no per-feature
            # extraction failure and no Stage-1 retry to report. A failed
            # engine is reported through the engine block's own
            # failed/final_outcome keys, NOT by fabricating a
            # per-feature extraction-failure list this path never
            # computes -- and zero claims already drives
            # _compute_decline_features to decline every supported
            # feature, which is the honest user-visible outcome.
            "stage1_failed_features": (),
            "stage1_retry_features": (),
            "rules_engine": engine_diagnostics,
        },
    )


def _flatten_proximity_degrees(
    proximity_observations: dict[str, dict[str, dict[str, object]]]
) -> dict[str, dict[str, str]]:
    """Drops extract_relations()'s proximity {value, confidence} wrapper
    down to the bare {feature: {"Proximity": <degree-string>}} shape
    merge_relational_targets() (and, downstream, the flat `observation`
    dict) both expect -- confidence is not consumed on this path."""
    return {
        feature: {"Proximity": attrs["Proximity"]["value"]}
        for feature, attrs in proximity_observations.items()
        if "Proximity" in attrs
    }


def _assemble_relational_targets(contacts: dict[str, list[dict]]) -> dict[str, dict[str, object]]:
    """Bridge (S107): map each captured free-verb contact to a typed token via
    contact_mapper.map_contact and file token!=None into a targets dict, reusing
    observation_extractor._store_relationship (the one filing primitive:
    cardinality + relation_target_registry gate). Policy (ratified): files ALL
    resolved tokens regardless of confidence/clarity -- preserves byte-identical
    equivalence with the retired RELATIONSHIP path (which had neither axis).
    Unresolved (token=None) contacts are quarantined + logged, never guessed.
    NO LLM here -- the LLM fallback on token=None is a separate later task; this
    helper is its future insertion point (fallback wraps, never overrides, this)."""
    from agent.interpretive.contact_mapper import map_contact  # local import -- avoids obs_extractor<->contact_mapper cycle
    from agent.interpretive import observation_extractor          # local -- matches this file's existing observation_extractor import convention (prepare_palm_reading)
    targets: dict[str, dict[str, object]] = {}
    for feature, contact_list in (contacts or {}).items():
        for c in contact_list:
            try:
                mapped = map_contact(c)
            except Exception as exc:  # noqa: BLE001 -- a bad contact must quarantine, never crash the reading
                logger.error("S107 bridge: map_contact raised on %r (%s) -- quarantined.", c, exc)
                continue
            if mapped.get("token") is None:
                logger.info("S107 bridge: unresolved contact %r -- %s (quarantined).", c, mapped.get("reason"))
                continue
            observation_extractor._store_relationship(
                targets, feature, mapped["token"], mapped["target"], None,  # mount=None: a commencement join carries no separate mount
            )
    return targets


# S109 fallback audit dispositions logged for human review -- the AI-over-AI
# checkpoint (CLAUDE.md Working Style #5). Deliberately excludes ONLY
# "already_resolved_no_llm_needed" (purely deterministic, no AI decision
# was made). "position_unresolved" (S109 amendment, ratified): an LLM DID
# resolve a canonical join-family verb here, but the vision model gave no
# usable position ("at start"/"mid-course"/"at end"), so the join-vs-meet
# token stays honestly unresolved -- logged for VISIBILITY/measurement
# only. No token is ever fired for it, and no second vision call is made
# to recover a position; this is a pure logging widening, not a behavior
# change.
_FALLBACK_LOGGED_DISPOSITIONS = frozenset({
    "resolved", "llm_unclear", "hallucination",
    "batch_call_failed", "batch_malformed_response",
    "position_unresolved",
})


def _log_fallback_audits(audits: list[dict]) -> None:
    """Emits one structured WARNING log line per audit record whose
    disposition represents an actual AI-involved decision. NOT a
    capture-net file/API -- that is a separate, not-yet-built task
    (logging only, an interim human-review surface until that lands)."""
    for record in audits:
        if record.get("disposition") not in _FALLBACK_LOGGED_DISPOSITIONS:
            continue
        logger.warning(
            "S109 fallback audit: raw_verb=%r llm_choice=%r final_token=%r disposition=%r",
            record.get("raw_verb"), record.get("llm_canonical_choice"),
            record.get("final_token"), record.get("disposition"),
        )


def _assemble_relational_targets_with_fallback(
    left_contacts: dict[str, list[dict]],
    right_contacts: dict[str, list[dict]],
    client,
) -> tuple[dict[str, dict[str, object]], dict[str, dict[str, object]], list[dict]]:
    """S109: client-gated rescue wrapper around _assemble_relational_targets.
    _assemble_relational_targets itself is UNCHANGED (S107, no-LLM,
    determinism-gate path) -- this is an ADDITIVE sibling, never a
    replacement of it.

    Flattens BOTH hands' contacts into ONE list, keeping an index-aligned
    parallel list of (hand, feature) so results can be re-filed -- contact
    dicts carry target/verb/position/clarity but NOT their own feature
    (feature is the upstream dict key), so the parallel index is
    mandatory. Makes exactly ONE contact_llm_fallback.
    resolve_unresolved_contacts call for the whole reading: that function
    internally re-runs map_contact first, so deterministically-resolvable
    contacts (including S106-inflected forms) cost zero LLM and only
    genuine residual token=None contacts ever enter the LLM batch -- the
    FULL flat list is passed through, never pre-filtered here (S108's own
    contract already does that filtering correctly).

    Every result with token != None is filed into the correct hand's
    targets dict under its (hand, feature) via observation_extractor.
    _store_relationship(..., mount=None) -- the SAME filing primitive
    _assemble_relational_targets itself uses, so cardinality/registry-gate
    behavior is unchanged whether a token came from the deterministic
    tables or the LLM rescue. token == None stays quarantined (the
    resolver's own honest-silence contract) -- never guessed, never
    logged again here (resolve_unresolved_contacts already logged its own
    per-item quarantine reasoning; this function's caller logs the
    AUDIT record, a separate concern from the resolver's own internal
    logging).

    Returns (left_targets, right_targets, audits) -- audits is the FULL
    per-contact audit list from resolve_unresolved_contacts, in
    flattening order, for the caller to log via _log_fallback_audits."""
    from agent.interpretive.contact_llm_fallback import resolve_unresolved_contacts
    from agent.interpretive import observation_extractor  # local -- matches this file's existing convention

    flat_contacts: list[dict] = []
    flat_locations: list[tuple[str, str]] = []  # (hand, feature), index-aligned with flat_contacts
    for hand, contacts in (("left", left_contacts), ("right", right_contacts)):
        for feature, contact_list in (contacts or {}).items():
            for c in contact_list:
                flat_contacts.append(c)
                flat_locations.append((hand, feature))

    results, audits = resolve_unresolved_contacts(flat_contacts, client)

    # Attach hand/feature to each audit via the aligned flat_locations index --
    # in-place mutation is intended: audits is a fresh list local to this
    # call with a single downstream consumer (the caller's capture-net log),
    # so there's no key-collision or shared-state risk. setdefault so a
    # future producer that already supplies its own hand/feature is not
    # overwritten.
    for (hand, feature), audit in zip(flat_locations, audits):
        if audit is not None:
            audit.setdefault("hand", hand)
            audit.setdefault("feature", feature)

    left_targets: dict[str, dict[str, object]] = {}
    right_targets: dict[str, dict[str, object]] = {}
    for (hand, feature), result in zip(flat_locations, results):
        if result.get("token") is None:
            continue
        bucket = left_targets if hand == "left" else right_targets
        observation_extractor._store_relationship(
            bucket, feature, result["token"], result["target"], None,  # mount=None: a commencement join carries no separate mount
        )

    return left_targets, right_targets, audits


def prepare_palm_reading(
    palm_left: str | None,
    palm_right: str | None,
    hand_detail: str | None = None,
    client: OpenAI | None = None,
) -> PalmReadingPrep:
    """S69 F-H P5: parse -> retrieve -> support gate -> Stage 1
    (claim_extraction.extract_claims). Same ValueError input guard as
    generate_palm_reading() (unchanged) -- this is where palm_left/
    palm_right are first validated, before any parsing happens.

    This is the Stage-1 boundary the deterministic rule engine swaps into
    (`_deterministic_rules_enabled`, default OFF): when the flag is ON,
    everything above the `extract_claims` call runs identically and only
    the claim SOURCE changes -- see `_prepare_deterministic_prep`. When
    the flag is OFF this function behaves exactly as it did before the
    flag existed.

    Raises:
        ValueError: Both palm_left and palm_right are None.
        RuntimeError: extract_claims' own fail-closed condition -- every
                      feature that had gated chunks failed extraction
                      (both calls each) -- propagates UNCAUGHT, per this
                      prompt's own ERRORS section (fail-closed, no
                      reading possible from zero extractable claims).
    """
    if palm_left is None and palm_right is None:
        raise ValueError(
            "palm_reading.prepare_palm_reading: at least one of "
            "palm_left/palm_right must be provided -- hand_detail alone "
            "is insufficient input by design."
        )

    left_fields = _parse_fields(palm_left) if palm_left else {}
    right_fields = _parse_fields(palm_right) if palm_right else {}
    hd_fields = _parse_bullet_fields(hand_detail) if hand_detail else {}
    per_feature_results, failed_retrieval_features, full_candidates = _retrieve_per_feature(
        left_fields, right_fields, hd_fields
    )
    if failed_retrieval_features:
        logger.warning(
            "palm_reading.prepare_palm_reading: retrieval failed for "
            "features: %s -- reading proceeds without them.",
            ", ".join(failed_retrieval_features),
        )

    raw_texts_by_feature = _gather_feature_texts(left_fields, right_fields, hd_fields)
    gated_results, supported_features, unsupported_features = _apply_support_gate(
        per_feature_results, raw_texts_by_feature
    )
    texts_by_feature = _join_feature_texts(raw_texts_by_feature)

    if _deterministic_rules_enabled():
        from agent.interpretive import observation_extractor  # local -- see _prepare_claims_from_rules
        # Generalization step 2b (S98): both hands' directional + convergence
        # + proximity signal now come from ONE call each to the unified,
        # registry-driven extract_relations() (Generalization step 2a),
        # instead of 3 separate bespoke calls per hand. Right-hand priority
        # preserved (right merged after left) -- targets' directional and
        # convergence attribute keys stay disjoint, matching old behavior.
        left_rel = observation_extractor.extract_relations(palm_left or "")
        right_rel = observation_extractor.extract_relations(palm_right or "")
        # S107 bridge / S109 LLM-fallback rescue: CONTACTS-derived typed
        # targets merge alongside the existing (directional/convergence/
        # typed-RELATIONSHIP) targets -- merge_relational_targets is
        # variadic and cardinality-aware, so this is a pure additive
        # merge, not a replacement. client-gated: with a client, S109's
        # _assemble_relational_targets_with_fallback handles BOTH hands in
        # ONE LLM call (0 calls if nothing needs rescuing) and returns
        # audits to log; with client=None, the S107 no-LLM path runs per
        # hand exactly as before -- byte-identical to pre-S109 behavior in
        # that branch (see the determinism gate in this task's own test
        # suite). A fallback-assembly failure degrades to the
        # deterministic-only result rather than breaking the reading.
        fallback_audits: list[dict] = []
        if client is not None:
            try:
                left_ct, right_ct, fallback_audits = _assemble_relational_targets_with_fallback(
                    left_rel["contacts"], right_rel["contacts"], client,
                )
            except Exception as exc:  # noqa: BLE001 -- a fallback failure must degrade, never break the reading
                logger.error(
                    "palm_reading.prepare_palm_reading: S109 LLM fallback "
                    "assembly failed (%s: %s) -- degrading to the "
                    "deterministic-only S107 path for this reading.",
                    type(exc).__name__, exc,
                )
                left_ct = _assemble_relational_targets(left_rel["contacts"])
                right_ct = _assemble_relational_targets(right_rel["contacts"])
                fallback_audits = []
        else:
            left_ct = _assemble_relational_targets(left_rel["contacts"])
            right_ct = _assemble_relational_targets(right_rel["contacts"])
        _log_fallback_audits(fallback_audits)
        # S109 capture-net wiring: side by side with the WARNING log above,
        # not a replacement -- one reading_id per prepare_palm_reading call,
        # ephemeral (no storage lock implication, never persisted elsewhere).
        reading_id = uuid.uuid4().hex
        try:
            from agent.interpretive import capture_net  # local -- matches this file's existing convention
            capture_net.map_fallback_audits(fallback_audits, reading_id)
        except Exception as exc:  # noqa: BLE001 -- belt-and-suspenders: capture_net is already fail-safe internally, but a capture failure must never break a reading
            logger.warning(
                "palm_reading.prepare_palm_reading: capture-net wiring "
                "failed (%s: %s) -- reading proceeds unaffected.",
                type(exc).__name__, exc,
            )
        targets = observation_extractor.merge_relational_targets(
            left_rel["targets"],
            right_rel["targets"],
            left_ct,
            right_ct,
        )
        try:
            proximity_observations = observation_extractor.merge_relational_targets(
                _flatten_proximity_degrees(left_rel["proximity"]),
                _flatten_proximity_degrees(right_rel["proximity"]),
            )
        except Exception as exc:  # noqa: BLE001 -- fail-closed, mirrors
            # _prepare_claims_from_rules' own posture: a P-parse failure
            # must not crash the reading, only degrade to no proximity
            # signal (same as targets' own no-crash contract).
            logger.error(
                "palm_reading.prepare_palm_reading: proximity-degree parse "
                "failed (%s: %s) -- proceeding with no proximity signal.",
                type(exc).__name__, exc,
            )
            proximity_observations = {}
        try:
            # S117: per-mount DEVELOPMENT grades -- a pure deterministic
            # parse of each hand's raw text (observation_extractor.
            # extract_mount_development), same calling convention as
            # extract_relations(palm_left or "")/extract_relations(
            # palm_right or "") above. translate_mount_development maps
            # each hand's result onto ontology feature names before the
            # merge; merge_relational_targets is reused unchanged for the
            # left/right merge (Development is a plain scalar attribute,
            # never registered in relation_cardinality as "multi", so
            # _is_multi's False branch applies -- right-hand wins on
            # collision, same convention as targets/proximity above).
            mount_development = observation_extractor.merge_relational_targets(
                observation_extractor.translate_mount_development(
                    observation_extractor.extract_mount_development(palm_left or "")
                ),
                observation_extractor.translate_mount_development(
                    observation_extractor.extract_mount_development(palm_right or "")
                ),
            )
        except Exception as exc:  # noqa: BLE001 -- fail-closed, mirrors
            # proximity_observations' own posture immediately above: a
            # Development-parse failure must not crash the reading, only
            # degrade to no mount-development signal.
            logger.error(
                "palm_reading.prepare_palm_reading: mount-development parse "
                "failed (%s: %s) -- proceeding with no mount-development signal.",
                type(exc).__name__, exc,
            )
            mount_development = {}
        return _prepare_deterministic_prep(
            raw_texts_by_feature,
            texts_by_feature,
            gated_results,
            supported_features,
            unsupported_features,
            full_candidates,
            client=client,
            targets=targets,
            proximity_observations=proximity_observations,
            mount_development=mount_development,
        )

    extraction_result = claim_extraction.extract_claims(
        gated_results, texts_by_feature, client=client
    )

    # S83 near-miss margin log: merge full ranked candidate list (up to 30)
    # into per-feature diagnostics before returning; no behavior change.
    for feature, candidates in full_candidates.items():
        if feature not in extraction_result.diagnostics.get("features", {}):
            extraction_result.diagnostics.setdefault("features", {})[feature] = {}
        extraction_result.diagnostics["features"][feature]["candidates"] = candidates

    stage1_retry_features = tuple(
        f for f in _FEATURE_REGISTRY
        if extraction_result.diagnostics.get("features", {}).get(f, {}).get("retry_used")
    )

    return PalmReadingPrep(
        gated_results=gated_results,
        supported_features=supported_features,
        unsupported_features=unsupported_features,
        claims=extraction_result.claims,
        texts_by_feature=texts_by_feature,
        diagnostics={
            "stage1": extraction_result.diagnostics,
            "stage1_failed_features": extraction_result.failed_features,
            "stage1_retry_features": stage1_retry_features,
        },
    )


def _build_display_extra_validators(
    context_corpus: str,
    unsupported_features: tuple[str, ...],
) -> tuple:
    """S70 F-G2: one strip-wrapped closure per `_run_display_checks`
    check, fed to `claim_voicing.voice_claims`'s `extra_validators` seam
    (F-G1) so a display-check failure on Stage 2's FIRST draft becomes a
    correction instruction on Stage 2's own retry, instead of only
    surfacing at the outer `_run_display_checks` backstop below (which
    has no retry of its own). Each closure strips claim_voicing's own tag
    vocabulary via `_strip_stage2_tags` before running its single check --
    this mirrors EXACTLY the text state `_run_display_checks` itself
    checks (stripped, BEFORE `decline_block`/`DISCLAIMER` are appended --
    those are only ever assembled once, after `voice_claims` returns, so
    there is no per-draft divergence to replicate here: every draft
    `voice_claims` internally considers, first or retry, is checked in
    exactly this same pre-decline/pre-disclaimer, tags-stripped state).
    One closure per check, not one mega-closure, so each check's own
    failure string(s) survive distinctly into the retry correction
    message (`claim_voicing._build_retry_messages` joins the merged list,
    but each check still contributes its own recognizable substring)."""
    def _jargon(tagged_draft: str) -> list[str]:
        return _check_jargon(_strip_stage2_tags(tagged_draft))

    def _self_help(tagged_draft: str) -> list[str]:
        return _check_self_help_register(_strip_stage2_tags(tagged_draft))

    def _dates(tagged_draft: str) -> list[str]:
        return _check_unsupported_dates(_strip_stage2_tags(tagged_draft), context_corpus)

    def _length(tagged_draft: str) -> list[str]:
        return _check_length(_strip_stage2_tags(tagged_draft))

    def _banned(tagged_draft: str) -> list[str]:
        return _check_banned_feature_mentions(_strip_stage2_tags(tagged_draft), unsupported_features)

    def _echo(tagged_draft: str) -> list[str]:
        return _check_exemplar_echo(_strip_stage2_tags(tagged_draft))

    return (_jargon, _self_help, _dates, _length, _banned, _echo)


def complete_palm_reading(
    prep: PalmReadingPrep,
    client: OpenAI | None = None,
) -> PalmReadingResult:
    """S69 F-H P5: Stage 2 (claim_voicing.voice_claims) + display checks
    + decline block + DISCLAIMER + strip. Consumes a PalmReadingPrep from
    prepare_palm_reading() (or the S70 P6b checkpoint step that inspects/
    acks (ACK-ONLY — claims are never edited; S70 ruling) `prep.claims`
    first).

    S70 F-G2: display checks feed Stage 2's single internal retry (the
    F-G1 seam, `claim_voicing.voice_claims`'s `extra_validators` param);
    this outer layer remains fail-closed with no additional retry -- hard
    cap 2 Stage-2 calls unchanged. `_build_display_extra_validators`
    builds one strip-wrapped closure per `_run_display_checks` check
    (jargon/self-help/unsupported-dates/length/banned-feature-mention/
    exemplar-echo) from THIS function's own `context_corpus`/
    `prep.unsupported_features`, passed to `voice_claims` as
    `extra_validators` -- a failure on Stage 2's first draft now feeds
    that check's own failure string into Stage 2's correction retry, the
    same as a V-3/V-4/V-5 failure would. The `_run_display_checks` call
    just below is UNCHANGED -- it still re-runs the identical six checks
    against whichever draft actually ships (first or retry), as the
    deterministic fail-closed backstop: a draft failing at the seam
    either gets corrected by the retry, or fails closed here exactly as
    it did before F-G2 (no double-jeopardy in outcome -- only one of
    those two things happens to a given failing draft, never both).
    F-G RISK (CLAUDE.md's F-G entry, OLD single-call architecture): the
    "stability" self-help-blacklist composition habit has a fundamentally
    different failure surface in Stage 2's closed-inventory voice pass;
    pass-5 preflight (`diagnostics/pass5_preflight_S70.md`) already
    surfaced one concrete instance of this class (verbatim exemplar
    echo) that F-G2 now feeds back into the retry -- a live dogfood pass
    remains the measure of whether the F-G risk recurs more broadly.

    Raises:
        RuntimeError: claim_voicing.voice_claims' own fail condition --
                      an API exception on either its first or retry call
                      -- propagates UNCAUGHT, per this prompt's ERRORS
                      section.
    """
    context_corpus = " ".join(prep.texts_by_feature.values()) + " " + " ".join(
        c["text"] for chunks in prep.gated_results.values() for c in chunks
    )
    extra_validators = _build_display_extra_validators(context_corpus, prep.unsupported_features)

    voice_result = claim_voicing.voice_claims(
        prep.claims, prep.texts_by_feature, client=client, extra_validators=extra_validators
    )

    stripped = _strip_stage2_tags(voice_result.reading_text_tagged)

    display_failures = _run_display_checks(stripped, context_corpus, prep.unsupported_features)

    failures = tuple(voice_result.validation_failures) + tuple(display_failures)
    validation = ValidationReport(passed=not failures, failures=failures, warnings=())

    decline_features = _compute_decline_features(
        prep.supported_features,
        prep.unsupported_features,
        prep.diagnostics.get("stage1_failed_features", ()),
        prep.claims,
    )
    decline_block = _build_decline_block(decline_features)

    final_text = stripped.rstrip()
    if decline_block:
        final_text += "\n\n" + decline_block
    final_text += "\n\n" + DISCLAIMER

    sources = _build_sources_from_claims(
        voice_result.reading_text_tagged, prep.claims, prep.gated_results
    )

    stage1_retry_features = prep.diagnostics.get("stage1_retry_features", ())
    stage1_feature_diagnostics = prep.diagnostics.get("stage1", {}).get("features", {})
    stage2_retry_used = voice_result.retry_used
    stage2_first_attempt_failures = tuple(
        voice_result.diagnostics.get("first_attempt_failures", ())
    )

    return PalmReadingResult(
        reading_text=final_text,
        reading_text_tagged=voice_result.reading_text_tagged,
        sources=sources,
        validation=validation,
        model=claim_voicing._VOICE_MODEL,
        retry_used=bool(stage1_retry_features) or stage2_retry_used,
        supported_features=prep.supported_features,
        unsupported_features=prep.unsupported_features,
        claims=prep.claims,
        stage1_retry_features=stage1_retry_features,
        stage1_feature_diagnostics=stage1_feature_diagnostics,
        stage2_retry_used=stage2_retry_used,
        stage2_first_attempt_failures=stage2_first_attempt_failures,
    )


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

    S69 F-H P5: this is now `prepare_palm_reading()` composed with
    `complete_palm_reading()` -- same signature, same behavior contract,
    no fork. The SAME `client` is used for both Stage 1 (extraction) and
    Stage 2 (voicing), matching the pre-P5 single-call flow's one-client
    contract. See `prepare_palm_reading`/`complete_palm_reading`'s own
    docstrings for the two-stage pipeline detail, and the module
    docstring's S69 F-H P5 section for what was retired and why.

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
        the caller's signal for whether to display it. ValidationReport.
        warnings is now ALWAYS `()` (F-A's `_check_feature_coverage` is
        retired, superseded by claim_voicing's own V-4 claim-coverage
        check -- see the module docstring). `retry_used` is COMPAT (true
        if EITHER stage retried); `stage1_retry_features`/
        `stage2_retry_used` are the new, more precise fields.

    Raises:
        ValueError: Both palm_left and palm_right are None (hand_detail
                    alone is insufficient input by design).
        RuntimeError: extract_claims' all-features-failed condition, or
                      voice_claims' API-call-failure condition -- both
                      propagate uncaught (fail-closed, no reading).
    """
    prep = prepare_palm_reading(palm_left, palm_right, hand_detail, client=client)
    return complete_palm_reading(prep, client=client)
