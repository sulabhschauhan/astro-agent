"""
frontend/app.py
Streamlit UI — Vedic astrology assistant (Parashara RAG agent).
"""

import hashlib
import logging
import re
import sys
import os
import datetime
from pathlib import Path

# SessionManager writes to data/sessions/ (relative path) — must be project root
_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(_ROOT))
os.chdir(_ROOT)

import streamlit as st

from agent.chart_calculator import calculate_chart, format_kundali_context, geocode_place_candidates
from agent.session_manager import SessionManager
from agent.astrosage_parser import parse_astrosage_pdf, _PRIORITY_ORDER
from PIL import Image
from agent.palm_processor import validate_palm_image, describe_palm_image, describe_hand_detail_image
from agent.interpretive.palm_reading import (
    generate_palm_reading, prepare_palm_reading, complete_palm_reading, _FEATURE_PAGE_RANGES,
    _N_RESULTS_PER_FEATURE,
)
from agent.interpretive.claim_extraction import CitationByChunk, CitationByRule
from agent.infra.orchestrator import answer_question
from agent.interpretive.answer_renderer import render_answer

logger = logging.getLogger(__name__)

# ─── S66 F5: opt-in local dogfood capture ──────────────────────────────────────
# Read once at module scope (re-evaluated every Streamlit script rerun, same
# as any other module-level statement here). Local-only, gitignored (see
# .gitignore) -- never committed. Derived text ONLY: image bytes, image
# hashes, pdf_context, and any AstroSage content are deliberately EXCLUDED
# (no-storage lock ruling 2026-07-12).
_DOGFOOD_CAPTURE  = os.environ.get("ASTRO_DOGFOOD_CAPTURE") == "1"
# Option Z (S71) / S72 gate: palm-side user flow disabled by
# default in V1. All palm-side modules remain imported and
# testable; only UI render blocks in this file are gated. V1.1
# re-enable is a config flip (ASTRO_PALM_ENABLED=1).
_PALM_ENABLED = os.environ.get("ASTRO_PALM_ENABLED", "0") == "1"
_DOGFOOD_LOG_PATH = _ROOT / "diagnostics" / "dogfood_capture.md"


def _format_stage1_feature_diagnostics_lines(feature_diagnostics: dict) -> list:
    """S78 E2 step 2c: shared formatter for the `stage1_feature_diagnostics`
    capture block -- called from both _capture_dogfood_run (happy path) and
    _capture_checkpoint_declined (declined path) so the two capture forms
    stay format-identical, per this prompt's parity requirement (a future
    audit can compare RUN vs CHECKPOINT-DECLINED blocks apples-to-apples).
    Reads every per-feature field defensively via .get() -- older captures
    (pre-S78 step-2a) may carry `diag` dicts without the new
    attempt_1_status/attempt_1_claim_count/attempt_2_status/
    attempt_2_claim_count/final_outcome keys at all.

    S78 E2 step 2d: attempt_1_failures/attempt_2_failures continuation
    lines -- the 2026-07-27T15:04:44 dogfood run reproduced a
    outcome=failed_both thumb row with no visible reason (attempt_1=
    validation_failed/0 attempt_2=validation_failed/0), even though
    claim_extraction.py's diag dict already carries the actual E-1/E-2/E-3
    messages under first_attempt_failures/failures -- just never emitted
    here. Only appended when the corresponding attempt's status indicates
    a real failure (validation_failed/error) AND the message list is
    non-empty, so success/empty outcomes stay exactly as compact as before.

    Measurement-only addition: attempt_1_raw_count/attempt_2_raw_count
    (claim_extraction.py's PRE-VALIDATION claims-list length, None when no
    response was parsed at all) are rendered as an OBSERVED "(raw=N)"
    suffix per attempt, so a validated_empty/0 outcome shows whether the
    model emitted zero claims (raw=0) or emitted some that all failed
    validation (raw>0) -- previously indistinguishable from this line
    alone. Read via .get() with a "?" fallback for the same pre-existing-
    capture-compatibility reason as the other fields here.

    ROOT-CAUSE FIX (diagnosed this session): the deterministic rule
    engine's diagnostics ride the SAME `stage1_feature_diagnostics` dict
    under the pseudo-feature key "_rules_engine" (palm_reading.py's
    `_prepare_deterministic_prep`), but its payload shape is entirely
    different from an LLM-extraction feature's (observation_record,
    fired_rule_ids, observation, dropped_tokens, suppression_log, ... vs.
    attempt_1_status/attempt_2_status/...). Before this fix, the generic
    branch below read those absent LLM-ledger keys via .get() and silently
    emitted a content-free "outcome=... attempt_1=unknown/? (raw=?)
    attempt_2=unknown/? (raw=?)" line for it -- never crashing (the
    .get() defensiveness worked as designed), but also never surfacing
    the actual engine payload anywhere in the capture. Detected via
    diag's own "observation_record" key (only the engine entry ever has
    one) rather than the "_rules_engine" feature-name string, so a future
    rename of the pseudo-feature key can't silently defeat this branch."""
    if not feature_diagnostics:
        return ["stage1_feature_diagnostics: NONE"]
    lines = ["stage1_feature_diagnostics:"]
    for feature in sorted(feature_diagnostics):
        diag = feature_diagnostics[feature]

        if isinstance(diag, dict) and "observation_record" in diag:
            try:
                outcome = diag.get("final_outcome", "unknown")
                failed = diag.get("failed", "unknown")
                lines.append(f"  {feature}: outcome={outcome} failed={failed}")
                if "failed_stage" in diag:
                    lines.append(f"    failed_stage: {diag['failed_stage']}")
                record = diag.get("observation_record", {}) or {}
                lines.append(f"    enabled_features: {sorted(record.get('enabled_features', []))}")
                lines.append(f"    fired_rule_ids: {diag.get('fired_rule_ids', [])}")
                lines.append(f"    surviving_rule_ids: {diag.get('surviving_rule_ids', [])}")
                # S119 Step 3/4: the authoritative jurisdiction record --
                # the _FEATURE_REGISTRY tokens the surviving rules map to,
                # i.e. exactly which features the retrieval support gate
                # was overruled on. Reading it beside the rule ids is what
                # makes a "why wasn't this declined?" question answerable
                # from the capture alone. Same .get()-defaulted style as
                # every other line here, so an older capture without the
                # key still renders.
                lines.append(f"    surviving_rule_features: {diag.get('surviving_rule_features', [])}")
                lines.append(f"    suppression_log: {diag.get('suppression_log', [])}")
                lines.append(f"    dropped_tokens: {diag.get('dropped_tokens', [])}")
                lines.append(f"    observation: {diag.get('observation', {})}")
                lines.append(f"    targets: {diag.get('targets', {})}")
                lines.append(f"    proximity_observations: {diag.get('proximity_observations', {})}")
                lines.append(f"    phrase_promotions: {diag.get('phrase_promotions', [])}")
                lines.append(f"    citations: {diag.get('citations', {})}")
                lines.append(f"    dropped_rule_ids: {diag.get('dropped_rule_ids', [])}")
                lines.append(f"    claim_features_outside_registry: {diag.get('claim_features_outside_registry', [])}")
                lines.append("    observation_record:")
                record_features = record.get("features", {}) or {}
                if record_features:
                    for rec_feature in sorted(record_features):
                        fobs = record_features[rec_feature]
                        raw_prose = str(fobs.get("raw_prose", ""))
                        if len(raw_prose) > 200:
                            raw_prose = raw_prose[:200] + "..."
                        lines.append(
                            f"      {rec_feature}: tokens={fobs.get('tokens', {})} "
                            f"unmapped={fobs.get('unmapped', [])} raw_prose=\"{raw_prose}\""
                        )
                else:
                    lines.append("      NONE")
            except Exception as exc:  # noqa: BLE001 -- must never crash the capture
                lines.append(f"  {feature}: EMIT_ERROR: {exc}")
            continue

        outcome = diag.get("final_outcome", "unknown")
        a1_status = diag.get("attempt_1_status", "unknown")
        a1_count = diag.get("attempt_1_claim_count", "?")
        a1_raw = diag.get("attempt_1_raw_count", "?")
        a2_status = diag.get("attempt_2_status", "unknown")
        a2_count = diag.get("attempt_2_claim_count", "?")
        a2_raw = diag.get("attempt_2_raw_count", "?")
        lines.append(
            f"  {feature}: outcome={outcome} attempt_1={a1_status}/{a1_count} (raw={a1_raw}) "
            f"attempt_2={a2_status}/{a2_count} (raw={a2_raw})"
        )
        if a1_status in ("validation_failed", "error"):
            attempt_1_failures = diag.get("first_attempt_failures", ())
            if attempt_1_failures:
                capped = [
                    msg if len(msg) <= 200 else msg[:200] + "..."
                    for msg in attempt_1_failures
                ]
                lines.append(f"    attempt_1_failures: {'; '.join(capped)}")
        if a2_status in ("validation_failed", "error"):
            attempt_2_failures = diag.get("failures", ())
            if attempt_2_failures:
                capped = [
                    msg if len(msg) <= 200 else msg[:200] + "..."
                    for msg in attempt_2_failures
                ]
                lines.append(f"    attempt_2_failures: {'; '.join(capped)}")
    return lines


def _format_source_line(src: dict, include_feature: bool = False) -> str:
    """One "Classical sources" line, shared by the dogfood capture and the
    Streamlit panel so the two never drift (same parity reason
    _format_stage1_feature_diagnostics_lines exists).

    S119 Step 5: a BY-RULE source has score=None -- there was no retrieval,
    so there is no similarity score to report. The score clause is then
    OMITTED ENTIRELY; a user must never be shown "score: None", which reads
    as a broken measurement rather than as an inapplicable one. A by-chunk
    (retrieval) source renders exactly as it always did.

    `rule_id` is included when present so a reader can trace a displayed
    claim back to the rule that made it. `source_quote` is NOT rendered
    here -- the UI shows it on its own line (see the caller), and the
    capture records it separately."""
    parts = []
    if src.get("score") is not None:
        parts.append(f"score: {src['score']}")
    if src.get("rule_id"):
        parts.append(f"rule: {src['rule_id']}")
    if include_feature:
        parts.append(f"feature: {src.get('feature')}")
    suffix = f" ({', '.join(parts)})" if parts else ""
    return f"{src['book']}, p.{src['page']}{suffix}"


def _citation_column(claim) -> str:
    """S119 Step 4: the citation-IDENTITY column shared by all four
    claims_inventory renders (2 dogfood-capture writers, 2 Streamlit
    captions).

    Was `claim.chunk_id`. Since Step 2 a rule-sourced claim carries
    chunk_id=None, which rendered as the bare string "None" -- reading as
    missing data rather than as "cited by rule". `citation_ref` gives the
    chunk_id verbatim for retrieval claims (that column is unchanged for
    them) and rule:<rule_id>@p<page> for rule claims. The source_quote is
    not part of that form, so no book prose enters any capture.

    Falls back to the raw chunk_id if the accessor is unavailable, so a
    capture is never lost to a formatting error."""
    try:
        return str(claim.citation_ref)
    except Exception:
        return str(claim.chunk_id)


# ─── S119 Step 4: wrong_source, per citation kind ──────────────────────
#
# THE BUG THIS REPLACES: the check in _run_had_failure used to be
# `re.search(r"_p(\d+)_", claim.chunk_id)` for EVERY claim. Since S119
# Step 2 a rule-sourced claim carries `chunk_id=None`, so that call raised
# TypeError straight into the surrounding `except Exception: continue` --
# the wrong_source trigger silently stopped evaluating rule claims
# altogether. Silent, because that except was there to swallow a malformed
# chunk_id, not an entire citation kind.
#
# WHY RULE CLAIMS ARE NOT PAGE-RANGE CHECKED (measured, not assumed --
# this is the trap in "just use source_page instead"): the rule files'
# `source_page` and `_FEATURE_PAGE_RANGES` are DIFFERENT COORDINATE
# SYSTEMS. Rule pages are anchored to data/cheiro/cheiro_clean_v1.json
# (the page-level corpus the authoring gate verifies against);
# _FEATURE_PAGE_RANGES comes from data/cheiro_feature_pages.json, in the
# chunk corpus' `page_ref` numbering used by the retrieval page-range
# gate. They coincide for head/heart/life/most mounts, but the fate file
# sits at source_page 103-105 against a "fate line" range of (162, 165) --
# so range-checking rule pages would tag wrong_source on ALL 16 fate rules
# on every run that fires one. Measured this session; see
# diagnostics/latest_run.md (S119 Step 4).
#
# The page-range check exists to catch a RETRIEVAL claim citing a chunk
# from the wrong chapter. That failure mode cannot occur for a rule claim,
# whose citation is the rule's own authored, gate-verified span
# (scripts/gate_rule_citations.py: NOT_FOUND_ANYWHERE 0/99). The rule-claim
# analogue of "wrong source" is a citation that is missing or unusable,
# which is what _rule_claim_citation_is_broken checks.


def _rule_claim_citation_is_broken(claim) -> bool:
    """True only for a RULE-sourced claim whose citation cannot identify
    its source: no source_page, or an empty/whitespace source_quote. A
    by-chunk (retrieval) claim always returns False -- this function has
    no opinion about it. Never raises."""
    try:
        citation = claim.citation
    except Exception:
        # A claim with neither a chunk_id nor a rule citation cannot be
        # sourced at all -- that IS the broken case, not a reason to skip.
        return True
    if not isinstance(citation, CitationByRule):
        return False
    return citation.source_page is None or not str(citation.source_quote or "").strip()


def _retrieval_claim_page(claim) -> int | None:
    """The page a BY-CHUNK claim's chunk_id encodes, or None when there is
    nothing to range-check (a rule claim, a malformed chunk_id). Behavior
    for by-chunk claims is byte-identical to the old inline regex."""
    try:
        citation = claim.citation
    except Exception:
        return None
    if not isinstance(citation, CitationByChunk):
        return None
    try:
        match = re.search(r"_p(\d+)_", citation.chunk_id)
        if match is None:
            return None
        return int(match.group(1))
    except Exception:
        return None


def _run_had_failure(reading) -> tuple[bool, list[str]]:
    """S83: categorical, threshold-free gate for the dogfood capture net --
    clean runs write nothing, only a fired reason tag earns a capture.
    Every check reads an existing PalmReadingResult field directly; no new
    detectors, no thresholds. Fail-safe: any internal error here returns
    (True, ["capture_error"]) so a bug in this helper can never cost a
    capture that should have happened."""
    try:
        tags = set()

        if reading.unsupported_features:
            tags.add("silence")
        for diag in reading.stage1_feature_diagnostics.values():
            outcome = str(diag.get("final_outcome", ""))
            if "empty" in outcome:
                tags.add("silence")
            if "failed" in outcome:
                tags.add("all_rejected")

        for claim in reading.claims:
            if claim.excluded_from_voice:
                continue
            if _rule_claim_citation_is_broken(claim):
                tags.add("wrong_source")
                continue
            page = _retrieval_claim_page(claim)
            if page is None:
                continue
            feature_range = _FEATURE_PAGE_RANGES.get(claim.feature)
            if not feature_range:
                continue
            start, end = feature_range
            if not (start <= page <= end):
                tags.add("wrong_source")

        if reading.retry_used or reading.stage2_retry_used:
            tags.add("instability")
        if not reading.validation.passed or reading.validation.failures:
            tags.add("instability")

        return (bool(tags), sorted(tags))
    except Exception:
        return (True, ["capture_error"])


def _capture_dogfood_run(palm_left, palm_right, hand_detail, reading) -> None:
    """
    Append one markdown block to diagnostics/dogfood_capture.md for a
    successful generate_palm_reading() call (regardless of Ring 1
    validation outcome -- pass/fail is itself captured data).

    Args:
        palm_left/palm_right/hand_detail: confirmed description strings
            passed to generate_palm_reading(), or None if that hand/photo
            was not confirmed for this run.
        reading: the PalmReadingResult returned by generate_palm_reading().
    """
    any_fired, tags = _run_had_failure(reading)
    if not any_fired:
        return

    lines = [f"## RUN {datetime.datetime.now().isoformat()}", ""]
    lines.append("### capture_reason")
    lines.append(", ".join(tags))
    lines.append("")

    lines.append("### Confirmed descriptions")
    if palm_left:
        lines.append("#### LEFT")
        lines.append(palm_left)
    if palm_right:
        lines.append("#### RIGHT")
        lines.append(palm_right)
    if hand_detail:
        lines.append("#### HAND_DETAIL")
        lines.append(hand_detail)
    lines.append("")

    lines.append("### reading_text")
    lines.append(reading.reading_text)
    lines.append("")

    # A1 (S68 F-C F5): raw tagged draft (anchors intact, pre-decline/
    # pre-DISCLAIMER) alongside the stripped/display form above -- Ring 3
    # pass 4 scores claim->anchor fidelity from THIS form; the stripped
    # reading_text alone can't show which claim backs which sentence.
    # S69 F-H (P6a): tag vocabulary is now Stage 2's {[C<n>], [OBS],
    # [FLOW]} (claim_id / observation / connective-flow markers), NOT
    # the single-call architecture's old {[OBS], [<chunk_id>]} -- the
    # claims_inventory section below is what resolves a [C<n>] tag back
    # to its chunk_id/feature. Wrapped in its own try/except (not just
    # the outer call-site safety net) so a failure capturing this NEW
    # field alone can never also cost the pre-existing capture lines
    # around it.
    lines.append("### READING (TAGGED)")
    try:
        lines.append(reading.reading_text_tagged)
    except Exception as exc:
        lines.append(f"[capture error: reading_text_tagged unavailable: {exc}]")
    lines.append("")

    lines.append("### sources")
    # score is already round(..., 4) at the source (ingestion/query_engine.py)
    # -- same value the UI renders, not reformatted here. S67 R1 added a
    # "feature" tag to every source dict; captured here so Ring 3 pass 3's
    # P1 claim ledger can score per-feature support directly from this
    # capture instead of forensically re-deriving it (pass-2's gap).
    #
    # S119 Step 5: a BY-RULE source carries score=None (no retrieval
    # happened), so the score clause is omitted rather than rendered as
    # the literal "score: None" -- see _format_source_line.
    for src in reading.sources:
        lines.append(f"- {_format_source_line(src, include_feature=True)}")
    lines.append("")

    # S67 R3: registry-order supported/unsupported feature verdicts,
    # captured verbatim (tuple repr) -- the other half of the P1
    # claim-ledger evidence the source lines' feature tags feed into.
    lines.append("### feature_support")
    lines.append(f"supported_features: {reading.supported_features}")
    lines.append(f"unsupported_features: {reading.unsupported_features}")
    lines.append("")

    # S69 F-H P5 / S70 P6a: full Stage-1 extraction inventory
    # (claim_extraction.Claim, verbatim from reading.claims), including
    # claims excluded_from_voice -- the full inventory (not just what
    # made it into the voiced reading) is the point, per P6a instructions.
    # One line per claim, tuple order (registry order, per claim_
    # extraction.py); claim_text has internal newlines flattened to a
    # single space so each claim stays one grep-able line.
    lines.append("### claims_inventory")
    if reading.claims:
        for claim in reading.claims:
            claim_text_oneline = claim.claim_text.replace("\n", " ")
            lines.append(
                f"{claim.claim_id} | {claim.feature} | {_citation_column(claim)} | "
                f"{claim.valence} | {claim.excluded_from_voice} | "
                f"{claim.exclusion_reason} | {claim.condition_text} | "
                f"{claim_text_oneline}"
            )
    else:
        lines.append("claims_inventory: EMPTY")
    lines.append("")

    lines.append("### ring1_validation")
    lines.append(f"passed: {reading.validation.passed}")
    lines.append(f"failures: {reading.validation.failures}")
    # S67 F2c added retry_used to PalmReadingResult but F5's original
    # capture never recorded it -- Ring 3 pass 2 could not tell whether
    # any of its 3 captured runs needed the validator-fed retry. Captured
    # here, alongside the other Ring 1 outcome fields.
    lines.append(f"retry_used: {reading.retry_used}")
    # S69 F-H P5 / S70 P6a: retry_used above is COMPAT (true if EITHER
    # stage retried) -- these two give the per-stage breakdown.
    stage1_retry_features_str = (
        ", ".join(reading.stage1_retry_features)
        if reading.stage1_retry_features
        else "NONE"
    )
    lines.append(f"stage1_retry_features: {stage1_retry_features_str}")
    # S78 E2 step 2c: per-feature Stage-1 diagnostic breakdown -- unblocks
    # e2_stage1_retry_audit.md open question #1 (whether a retried feature's
    # 2nd attempt landed in failed_features or a legitimately-empty claims
    # list), previously only reachable via the checkpoint-declined path.
    try:
        lines.extend(_format_stage1_feature_diagnostics_lines(reading.stage1_feature_diagnostics))
    except Exception as exc:
        logger.warning("app._capture_dogfood_run: stage1_feature_diagnostics capture failed: %s", exc)
        lines.append("stage1_feature_diagnostics: EMIT_ERROR")
    lines.append(f"stage2_retry_used: {reading.stage2_retry_used}")
    # S70: retry attribution -- WHAT drove Stage 2's retry, distinct from
    # merely knowing THAT it retried (stage2_retry_used above). Closes the
    # exact gap the "ring1_failures" comment above flags ("today only
    # retry_used implies a first-draft failure existed without saying
    # what it was") for the Stage-2-retry case specifically: a run that
    # ends up clean (stage2_retry_used=True, validation.passed=True) still
    # records here what the first draft actually failed on.
    stage2_first_attempt_failures_str = (
        "; ".join(reading.stage2_first_attempt_failures)
        if reading.stage2_first_attempt_failures
        else "NONE"
    )
    lines.append(f"stage2_first_attempt_failures: {stage2_first_attempt_failures_str}")

    # S70 P6a: semicolon-joined single-line form of the SAME
    # ValidationReport.failures tuple already captured above as a repr'd
    # line -- verbatim from reading.validation.failures.
    validation_failures_str = (
        "; ".join(reading.validation.failures)
        if reading.validation.failures
        else "NONE"
    )
    lines.append(f"validation_failures: {validation_failures_str}")

    # A1 (S68 F-C F5): one-line-per-failure form of the SAME
    # ValidationReport.failures tuple already captured above as a single
    # repr'd line -- today only retry_used implies a first-draft failure
    # existed without saying what it was; this makes V-1/V-2 violations
    # (and any display-check failure) grep-able per-run hard data, not a
    # replacement for the existing "failures:" line.
    lines.append("ring1_failures:")
    try:
        if reading.validation.failures:
            lines.extend(reading.validation.failures)
        else:
            lines.append("none")
    except Exception as exc:
        lines.append(f"[capture error: ring1_failures unavailable: {exc}]")

    # S70 P6a: the old "valid_chunk_ids_count: unavailable" line/comment
    # block (S68 F-C F5, accepted gap (e)) is RETIRED here -- the
    # claims_inventory section above now captures each claim's chunk_id
    # directly, closing the anchor-membership gap that line worked
    # around. CLAUDE.md's accepted-gap register update is a separate
    # close-out prompt's job, not done here.
    lines.append("")

    # S83 near-miss margin log: full ranked candidate list (up to 30) before
    # window slicing, one line per feature. No threshold, no behavior change --
    # logging only. Format: {feature}: window={N} candidates=[(rank, chunk_id, score), ...]
    lines.append("### near_miss_margin")
    try:
        has_data = False
        for feature in sorted(reading.stage1_feature_diagnostics):
            diag = reading.stage1_feature_diagnostics[feature]
            candidates = diag.get("candidates", [])
            if candidates:
                has_data = True
                formatted = ", ".join(
                    f"({rank}, {chunk_id}, {score})"
                    for rank, chunk_id, score in candidates
                )
                lines.append(
                    f"  {feature}: window={_N_RESULTS_PER_FEATURE} "
                    f"candidates=[{formatted}]"
                )
        if not has_data:
            lines.append("near_miss_margin: NOT CAPTURED")
    except Exception as exc:
        logger.warning("app._capture_dogfood_run: near_miss_margin capture failed: %s", exc)
        lines.append("near_miss_margin: EMIT_ERROR")
    lines.append("")

    _DOGFOOD_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(_DOGFOOD_LOG_PATH, "a", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def _capture_checkpoint_declined(prep) -> None:
    """
    S70 P6b: append a "## CHECKPOINT-DECLINED" markdown block to
    diagnostics/dogfood_capture.md when the DOGFOOD-path Stage-1 claims
    checkpoint is declined -- the claims are discarded and Stage 2
    (voicing) is never called, so there is no PalmReadingResult, no
    reading_text, and no ring1_validation for this run; only the
    claims_inventory section (same pipe-delimited format _capture_
    dogfood_run() writes, P6a) plus the Stage-1 retry/failed-feature
    diagnostics are captured.

    Args:
        prep: the PalmReadingPrep the user declined to ack (from
            prepare_palm_reading()).
    """
    lines = [f"## CHECKPOINT-DECLINED {datetime.datetime.now().isoformat()}", ""]

    lines.append("### claims_inventory")
    if prep.claims:
        for claim in prep.claims:
            claim_text_oneline = claim.claim_text.replace("\n", " ")
            lines.append(
                f"{claim.claim_id} | {claim.feature} | {_citation_column(claim)} | "
                f"{claim.valence} | {claim.excluded_from_voice} | "
                f"{claim.exclusion_reason} | {claim.condition_text} | "
                f"{claim_text_oneline}"
            )
    else:
        lines.append("claims_inventory: EMPTY")
    lines.append("")

    stage1_retry_features = prep.diagnostics.get("stage1_retry_features", ())
    stage1_failed_features = prep.diagnostics.get("stage1_failed_features", ())
    lines.append(
        f"stage1_retry_features: "
        f"{', '.join(stage1_retry_features) if stage1_retry_features else 'NONE'}"
    )
    lines.append(
        f"stage1_failed_features: "
        f"{', '.join(stage1_failed_features) if stage1_failed_features else 'NONE'}"
    )
    # S78 E2 step 2c: same field/format as _capture_dogfood_run's block --
    # parity between the two capture paths is the point. Reads
    # prep.diagnostics directly (matching how this function already reaches
    # every other field here) since the declined path has no
    # PalmReadingResult yet.
    try:
        lines.extend(_format_stage1_feature_diagnostics_lines(
            prep.diagnostics.get("stage1", {}).get("features", {})
        ))
    except Exception as exc:
        logger.warning("app._capture_checkpoint_declined: stage1_feature_diagnostics capture failed: %s", exc)
        lines.append("stage1_feature_diagnostics: EMIT_ERROR")
    lines.append("")

    _DOGFOOD_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(_DOGFOOD_LOG_PATH, "a", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


# ─── Page config (must be first Streamlit call) ───────────────────────────────

st.set_page_config(
    page_title="Astro Agent",
    page_icon="🪐",
    layout="wide",
)

# ─── Session state defaults ───────────────────────────────────────────────────

if "session_mgr" not in st.session_state:
    st.session_state.session_mgr = SessionManager()
if "chart" not in st.session_state:
    st.session_state.chart = None
if "kundali_str" not in st.session_state:
    st.session_state.kundali_str = ""
if "chart_ready" not in st.session_state:
    st.session_state.chart_ready = False
if "messages" not in st.session_state:
    st.session_state.messages = []
if "pdf_context" not in st.session_state:
    st.session_state.pdf_context = None
if "_astrosage_pdf_name" not in st.session_state:
    st.session_state["_astrosage_pdf_name"] = None
if "palm_left_str" not in st.session_state:
    st.session_state.palm_left_str = None
if "palm_left_hash" not in st.session_state:
    st.session_state.palm_left_hash = None
if "palm_left_status" not in st.session_state:
    st.session_state.palm_left_status = None
if "palm_right_str" not in st.session_state:
    st.session_state.palm_right_str = None
if "palm_right_hash" not in st.session_state:
    st.session_state.palm_right_hash = None
if "palm_right_status" not in st.session_state:
    st.session_state.palm_right_status = None
if "place_error" not in st.session_state:
    st.session_state.place_error = None
if "selected_place" not in st.session_state:
    st.session_state.selected_place = None
if "place_candidates" not in st.session_state:
    st.session_state.place_candidates = []
if "palm_left_confirmed" not in st.session_state:
    st.session_state.palm_left_confirmed = False
if "palm_right_confirmed" not in st.session_state:
    st.session_state.palm_right_confirmed = False
if "palm_nondominant_only" not in st.session_state:
    st.session_state.palm_nondominant_only = False
if "_palm_left_image_name" not in st.session_state:
    st.session_state["_palm_left_image_name"] = None
if "_palm_right_image_name" not in st.session_state:
    st.session_state["_palm_right_image_name"] = None
if "palm_left_bytes" not in st.session_state:
    st.session_state.palm_left_bytes = None
if "palm_right_bytes" not in st.session_state:
    st.session_state.palm_right_bytes = None
if "palm_left_hand_confirmed" not in st.session_state:
    st.session_state.palm_left_hand_confirmed = False
if "palm_right_hand_confirmed" not in st.session_state:
    st.session_state.palm_right_hand_confirmed = False
if "palm_left_needs_reupload" not in st.session_state:
    st.session_state.palm_left_needs_reupload = False
if "palm_right_needs_reupload" not in st.session_state:
    st.session_state.palm_right_needs_reupload = False
if "palm_left_regen_warning" not in st.session_state:
    st.session_state.palm_left_regen_warning = None
if "palm_right_regen_warning" not in st.session_state:
    st.session_state.palm_right_regen_warning = None
if "spouse_pdf_context" not in st.session_state:
    st.session_state.spouse_pdf_context = None
if "_spouse_pdf_name" not in st.session_state:
    st.session_state["_spouse_pdf_name"] = None
if "hand_detail_str" not in st.session_state:
    st.session_state.hand_detail_str = None
if "_hand_detail_image_name" not in st.session_state:
    st.session_state["_hand_detail_image_name"] = None
if "hand_detail_hash" not in st.session_state:
    st.session_state.hand_detail_hash = None
if "hand_detail_bytes" not in st.session_state:
    st.session_state.hand_detail_bytes = None
if "hand_detail_confirmed" not in st.session_state:
    st.session_state.hand_detail_confirmed = False
if "palm_reading_result" not in st.session_state:
    st.session_state.palm_reading_result = None
# S70 P6b: PalmReadingPrep from prepare_palm_reading(), set only on the
# DOGFOOD checkpoint path while awaiting ack/decline -- None otherwise.
# Every site that clears palm_reading_result above also clears this (S65
# 4a missed-clear-site precedent).
if "palm_prep" not in st.session_state:
    st.session_state.palm_prep = None

# ─── Sidebar ──────────────────────────────────────────────────────────────────

with st.sidebar:
    st.header("Birth Details")

    # ── Step 1: place search (outside form) ──────────────────────────────────
    _place_input = st.text_input(
        "Place of Birth", value="Calcutta, India", placeholder="Mumbai, India",
        key="place_search_text",
    )
    if st.button("Search", key="search_place_btn"):
        _cands = geocode_place_candidates(_place_input)
        st.session_state.place_candidates = _cands
        st.session_state.place_error = None
        if not _cands:
            st.session_state.selected_place = None
            st.session_state.place_error = (
                f"'{_place_input}' not found — try a major nearby city "
                "e.g. 'Mumbai, India' or 'New Delhi, India'."
            )
        elif len(_cands) == 1:
            st.session_state.selected_place = _cands[0]["display_name"]

    if st.session_state.place_error:
        st.error(st.session_state.place_error)
    elif len(st.session_state.place_candidates) > 1:
        _labels = [c["display_name"] for c in st.session_state.place_candidates]
        _choice = st.radio("Select location:", _labels, key="place_radio")
        st.session_state.selected_place = _choice
    elif st.session_state.selected_place:
        st.caption(f"Place confirmed: {st.session_state.selected_place}")

    # ── Step 2: birth details form ────────────────────────────────────────────
    with st.form("birth_form"):
        name = st.text_input("Name", value="Sulabh Singh Chauhan")
        col1, col2, col3 = st.columns(3)
        with col1:
            day   = st.selectbox("Day",   list(range(1, 32)), index=5)
        with col2:
            month = st.selectbox("Month", [
                "January","February","March","April","May","June",
                "July","August","September","October","November","December",
            ], index=3)
        with col3:
            year  = st.selectbox("Year",  list(range(2025, 1939, -1)), index=37)
        dob = f"{day} {month} {year}"
        tob = st.text_input("Time of Birth (IST)", value="00:30", placeholder="HH:MM", key="birth_time_input")
        submitted = st.form_submit_button(
            "Calculate Kundali",
            disabled=st.session_state.selected_place is None,
        )

    if submitted:
        time_val = st.session_state.get("birth_time_input", "")
        if not time_val:
            st.sidebar.warning("Please enter time of birth.")
            st.stop()
        if time_val:
            if not re.match(r'^\d{2}:\d{2}$', time_val):
                st.error("Invalid format — enter time as HH:MM (e.g. 14:30)")
                st.stop()
            hh, mm = int(time_val.split(":")[0]), int(time_val.split(":")[1])
            if not (0 <= hh <= 23 and 0 <= mm <= 59):
                st.error("Invalid time — hours 00-23, minutes 00-59")
                st.stop()
        place = st.session_state.selected_place
        missing = [f for f, v in [("Name", name), ("Place", place or "")] if not v.strip()]
        if missing:
            st.error(f"Required: {', '.join(missing)}")
        else:
            try:
                with st.spinner("Calculating your chart..."):
                    chart = calculate_chart(name.strip(), dob, tob, place)
                st.session_state.chart       = chart
                st.session_state.kundali_str = format_kundali_context(chart)
                st.session_state.chart_ready = True
                st.session_state.place_error = None
            except ValueError as e:
                if "geocode" in str(e).lower() or "cannot geocode" in str(e).lower():
                    st.session_state.place_error = (
                        f"'{place}' not found — try a major nearby city "
                        "e.g. 'Mumbai, India' or 'New Delhi, India'."
                    )
                    st.sidebar.error(st.session_state.place_error)
                else:
                    st.sidebar.error(f"Chart error: {e}")
                st.session_state.chart_ready = False
                st.stop()
            except Exception as e:
                st.sidebar.error(f"Unexpected error: {e}")
                st.session_state.chart_ready = False
                st.stop()

    if st.session_state.chart_ready:
        with st.expander("Kundali Summary"):
            st.text(st.session_state.kundali_str)

    st.divider()
    st.caption(f"Session ID: `{st.session_state.session_mgr.session_id[:8]}…`")
    if st.button("Clear Chat", use_container_width=True):
        st.session_state.messages    = []
        st.session_state.session_mgr = SessionManager()
        st.rerun()


# ─── Main area ────────────────────────────────────────────────────────────────

# T4 architecture / T4 V1 boundaries lock (CLAUDE.md Session 65): display-
# layer withholding ONLY -- pdf_context (the full parsed string threaded to
# ask()) is NOT modified, and astrosage_parser.py is NOT modified; the RAG/
# LLM path still sees these sections in full. Pratyantar: suppressed per
# the +/-37-day-drift/wrong-lord posture (same root cause as
# prompt_builder.py's kundali-slot carry-forward) -- Pratyantar-level date
# claims aren't reliable enough to show a user as if they were precise.
# Lal Kitab: post-V1 hard gate (CLAUDE.md "Post-V1 design gate: Lal Kitab
# remedy tier", Session 61) -- remedies are out of V1 scope entirely,
# withheld here rather than partially surfaced. Scope guard: this
# frozenset governs ONLY the "Your AstroSage Report" display expander
# below -- no other code path reads it. Revisit trigger: Lal Kitab V1.1
# unlock (gated on that carry-forward's required steps) or a future
# Pratyantar-precision fix.
_WITHHELD_SECTIONS = frozenset({"Pratyantar", "Lal Kitab"})

_SECTION_HEADER_RE = re.compile(
    r"^\[(" + "|".join(re.escape(n) for n in _PRIORITY_ORDER) + r")\]$",
    re.MULTILINE,
)


def _split_astrosage_sections(pdf_context: str) -> list[tuple[str, str]]:
    """
    Split parse_astrosage_pdf()'s combined output into (name, content) pairs
    for verbatim display.

    SENSITIVE_TO astrosage_parser.py's parse_astrosage_pdf() combined-output
    format: `"ASTROSAGE PDF DATA:\\n" + "\\n\\n".join(f"[{name}]\\n{content}"
    for name, content in sections.items())`. Section names auto-track the
    parser via _PRIORITY_ORDER -- only the join format ("[Name]\\ncontent",
    "\\n\\n" separator) remains a manual coupling. This splitter locates each
    known "[Name]" header line and slices the text between headers as that
    section's body; bracketed lines inside a section's own content that
    don't match a known name are left alone. If astrosage_parser.py's join
    format ever changes, this splitter breaks with it -- re-verify against
    the source before trusting this function after any astrosage_parser.py
    edit.

    Fail-soft: if no known "[Name]" headers are found, returns the full
    string (with the "ASTROSAGE PDF DATA:\\n" prefix stripped) unsplit
    under a single "AstroSage Report" label and logs a warning -- never
    raises.
    """
    parts = _SECTION_HEADER_RE.split(pdf_context)
    # parts[0] is whatever precedes the first header (the "ASTROSAGE PDF
    # DATA:" prefix line, not a real section) -- discarded. Remaining
    # parts alternate name, content, name, content, ...
    if len(parts) < 3:
        logger.warning(
            "app.py: no '[Name]' section headers found in AstroSage "
            "pdf_context — displaying unsplit (degraded, not crashing)."
        )
        return [("AstroSage Report", pdf_context.removeprefix("ASTROSAGE PDF DATA:\n"))]

    pairs: list[tuple[str, str]] = []
    for i in range(1, len(parts), 2):
        name = parts[i].strip()
        content = parts[i + 1].strip() if i + 1 < len(parts) else ""
        pairs.append((name, content))
    return pairs


st.title("Parashara — Vedic Astrology")

_upload_expander_title = (
    "Upload context (PDF + palms)" if _PALM_ENABLED
    else "Upload context (PDF)"
)
with st.expander(_upload_expander_title, expanded=False):
    # ── PDF ───────────────────────────────────────────────────────────────────
    uploaded_pdf = st.file_uploader("AstroSage PDF (optional)", type=["pdf"])
    if uploaded_pdf is not None:
        if st.session_state["_astrosage_pdf_name"] != uploaded_pdf.name:
            with st.spinner("Parsing AstroSage PDF…"):
                _pdf_parse_result = parse_astrosage_pdf(uploaded_pdf.read())
            if _pdf_parse_result:
                st.session_state.pdf_context = _pdf_parse_result
                st.session_state["_astrosage_pdf_name"] = uploaded_pdf.name
                st.success("AstroSage data loaded.")
            else:
                st.session_state.pdf_context = None
                st.warning("Could not extract sections — check this is an AstroSage PDF.")
    elif st.session_state["_astrosage_pdf_name"] is not None:
        st.session_state.pdf_context = None
        st.session_state["_astrosage_pdf_name"] = None

    if _PALM_ENABLED:
        # ── Left palm ─────────────────────────────────────────────────────────────
        uploaded_left = st.file_uploader(
            "Left hand (innate potential)", type=["jpg", "jpeg", "png"], key="palm_left_uploader",
        )
        if uploaded_left is not None:
            if st.session_state["_palm_left_image_name"] != uploaded_left.name:
                _lb = uploaded_left.read()
                _lh = hashlib.md5(_lb).hexdigest()
                st.session_state.palm_left_needs_reupload = False
                st.session_state.palm_left_regen_warning  = None
                with st.spinner("Validating left palm…"):
                    _vr = validate_palm_image(_lb, "left")
                if _vr["hard_reject"]:
                    st.error(_vr["reject_message"])
                    st.session_state.palm_left_str       = None
                    st.session_state.palm_left_hash      = None
                    st.session_state.palm_left_status    = None
                    st.session_state.palm_left_bytes     = None
                    st.session_state.palm_reading_result = None
                    st.session_state.palm_prep           = None
                elif st.session_state.palm_right_hash == _lh:
                    st.error("Same image uploaded for both hands — please upload each hand separately")
                    st.session_state.palm_left_str       = None
                    st.session_state.palm_left_hash      = None
                    st.session_state.palm_left_status    = None
                    st.session_state.palm_left_bytes     = None
                    st.session_state.palm_reading_result = None
                    st.session_state.palm_prep           = None
                else:
                    if _vr["warn"]:
                        st.warning(_vr["warn_message"])
                    st.session_state.palm_left_hash           = _lh
                    st.session_state.palm_left_status         = _vr
                    st.session_state.palm_left_bytes          = _lb
                    st.session_state.palm_left_hand_confirmed = False
                    try:
                        with st.spinner("Reading palm…"):
                            _desc = describe_palm_image(_lb, "left")
                        st.session_state.palm_left_str            = _desc
                        st.session_state["_palm_left_image_name"] = uploaded_left.name
                        st.session_state.palm_left_confirmed      = False
                        st.success("Left palm described — review below")
                    except RuntimeError as e:
                        st.error(f"Could not read palm image: {e}")
                        st.session_state.palm_left_str       = None
                        st.session_state.palm_reading_result = None
                        st.session_state.palm_prep           = None
        elif st.session_state.palm_left_hash is not None or st.session_state.palm_left_needs_reupload:
            st.session_state.palm_left_str            = None
            st.session_state.palm_left_hash           = None
            st.session_state.palm_left_status         = None
            st.session_state.palm_left_bytes          = None
            st.session_state.palm_left_confirmed      = False
            st.session_state.palm_left_hand_confirmed = False
            st.session_state.palm_left_needs_reupload = False
            st.session_state.palm_left_regen_warning  = None
            st.session_state["_palm_left_image_name"] = None
            st.session_state.palm_reading_result      = None
            st.session_state.palm_prep                = None

        # ── Left palm: preview, tips, hand confirmation ─────────────────────────────
        if uploaded_left is not None and st.session_state.palm_left_bytes is not None:
            st.image(st.session_state.palm_left_bytes, caption="Left palm", width=150)
            for _tip in (st.session_state.palm_left_status or {}).get("geometry_tips", []):
                st.caption(_tip)
            if st.session_state.palm_left_regen_warning:
                st.warning(st.session_state.palm_left_regen_warning)
            if not st.session_state.palm_left_hand_confirmed:
                st.write("Is this your **Left** hand?")
                _lcy, _lcn = st.columns(2)
                with _lcy:
                    if st.button("Yes", key="left_hand_yes"):
                        st.session_state.palm_left_hand_confirmed = True
                        st.rerun()
                with _lcn:
                    if st.button("No (swap)", key="left_hand_no"):
                        try:
                            if st.session_state.palm_right_hash is not None:
                                (st.session_state.palm_left_str, st.session_state.palm_right_str) = \
                                    (st.session_state.palm_right_str, st.session_state.palm_left_str)
                                (st.session_state.palm_left_hash, st.session_state.palm_right_hash) = \
                                    (st.session_state.palm_right_hash, st.session_state.palm_left_hash)
                                (st.session_state.palm_left_status, st.session_state.palm_right_status) = \
                                    (st.session_state.palm_right_status, st.session_state.palm_left_status)
                                (st.session_state.palm_left_bytes, st.session_state.palm_right_bytes) = \
                                    (st.session_state.palm_right_bytes, st.session_state.palm_left_bytes)
                                (st.session_state.palm_left_confirmed, st.session_state.palm_right_confirmed) = \
                                    (st.session_state.palm_right_confirmed, st.session_state.palm_left_confirmed)
                                st.session_state.palm_left_hand_confirmed  = True
                                st.session_state.palm_right_hand_confirmed = True

                                # Regenerate descriptions so hand-framing matches each
                                # slot's new (post-swap) image. On failure, the swapped
                                # string above stays as a fallback — it describes these
                                # bytes already, just with the original hand's framing.
                                with st.spinner("Updating palm readings…"):
                                    try:
                                        st.session_state.palm_left_str = describe_palm_image(
                                            st.session_state.palm_left_bytes, "left"
                                        )
                                        st.session_state.palm_left_regen_warning = None
                                        st.session_state.palm_left_confirmed     = False
                                        st.session_state.palm_reading_result     = None
                                        st.session_state.palm_prep               = None
                                    except RuntimeError:
                                        st.session_state.palm_left_regen_warning = (
                                            "Could not regenerate the left palm reading after "
                                            "swapping — it may reference the wrong hand. "
                                            "Consider re-uploading this image."
                                        )
                                        st.session_state.palm_reading_result = None
                                        st.session_state.palm_prep           = None
                                    try:
                                        st.session_state.palm_right_str = describe_palm_image(
                                            st.session_state.palm_right_bytes, "right"
                                        )
                                        st.session_state.palm_right_regen_warning = None
                                        st.session_state.palm_right_confirmed     = False
                                        st.session_state.palm_reading_result      = None
                                        st.session_state.palm_prep                = None
                                    except RuntimeError:
                                        st.session_state.palm_right_regen_warning = (
                                            "Could not regenerate the right palm reading after "
                                            "swapping — it may reference the wrong hand. "
                                            "Consider re-uploading this image."
                                        )
                                        st.session_state.palm_reading_result = None
                                        st.session_state.palm_prep           = None
                            else:
                                st.session_state.palm_left_str            = None
                                st.session_state.palm_left_hash           = None
                                st.session_state.palm_left_status         = None
                                st.session_state.palm_left_bytes          = None
                                st.session_state.palm_left_confirmed      = False
                                st.session_state.palm_left_hand_confirmed = False
                                st.session_state.palm_left_needs_reupload = True
                                st.session_state.palm_reading_result      = None
                                st.session_state.palm_prep                = None
                        except Exception as e:
                            st.error(f"Could not update palm state: {e}")
                        st.rerun()
            elif not st.session_state.palm_left_confirmed:
                with st.container():
                    st.markdown("**Review left palm description**")
                    st.markdown(st.session_state.palm_left_str)
                _lky, _lkn = st.columns(2)
                with _lky:
                    if st.button("Looks right — use this description", key="left_desc_confirm"):
                        st.session_state.palm_left_confirmed = True
                        st.rerun()
                with _lkn:
                    if st.button("Discard — re-upload", key="left_desc_discard"):
                        st.session_state.palm_left_str            = None
                        st.session_state.palm_left_hash           = None
                        st.session_state.palm_left_status         = None
                        st.session_state.palm_left_bytes          = None
                        st.session_state.palm_left_confirmed      = False
                        st.session_state.palm_left_hand_confirmed = False
                        st.session_state.palm_left_needs_reupload = False
                        st.session_state.palm_left_regen_warning  = None
                        st.session_state["_palm_left_image_name"] = None
                        st.session_state.palm_reading_result      = None
                        st.session_state.palm_prep                = None
                        st.rerun()
            else:
                st.caption("✓ Description confirmed")
                with st.container():
                    st.markdown("**Left palm description**")
                    st.markdown(st.session_state.palm_left_str)
        elif st.session_state.palm_left_needs_reupload and uploaded_left is not None:
            st.warning(
                "This image doesn't belong in the Left hand slot — please remove it "
                "(✕ above) and upload it using the Right hand uploader instead."
            )

        # ── Right palm ────────────────────────────────────────────────────────────
        uploaded_right = st.file_uploader(
            "Right hand (current trajectory)", type=["jpg", "jpeg", "png"], key="palm_right_uploader",
        )
        if uploaded_right is not None:
            if st.session_state["_palm_right_image_name"] != uploaded_right.name:
                _rb = uploaded_right.read()
                _rh = hashlib.md5(_rb).hexdigest()
                st.session_state.palm_right_needs_reupload = False
                st.session_state.palm_right_regen_warning  = None
                with st.spinner("Validating right palm…"):
                    _vr = validate_palm_image(_rb, "right")
                if _vr["hard_reject"]:
                    st.error(_vr["reject_message"])
                    st.session_state.palm_right_str      = None
                    st.session_state.palm_right_hash     = None
                    st.session_state.palm_right_status   = None
                    st.session_state.palm_right_bytes    = None
                    st.session_state.palm_reading_result = None
                    st.session_state.palm_prep           = None
                elif st.session_state.palm_left_hash == _rh:
                    st.error("Same image uploaded for both hands — please upload each hand separately")
                    st.session_state.palm_right_str      = None
                    st.session_state.palm_right_hash     = None
                    st.session_state.palm_right_status   = None
                    st.session_state.palm_right_bytes    = None
                    st.session_state.palm_reading_result = None
                    st.session_state.palm_prep           = None
                else:
                    if _vr["warn"]:
                        st.warning(_vr["warn_message"])
                    st.session_state.palm_right_hash           = _rh
                    st.session_state.palm_right_status         = _vr
                    st.session_state.palm_right_bytes          = _rb
                    st.session_state.palm_right_hand_confirmed = False
                    try:
                        with st.spinner("Reading palm…"):
                            _desc = describe_palm_image(_rb, "right")
                        st.session_state.palm_right_str            = _desc
                        st.session_state["_palm_right_image_name"] = uploaded_right.name
                        st.session_state.palm_right_confirmed      = False
                        st.success("Right palm described — review below")
                    except RuntimeError as e:
                        st.error(f"Could not read palm image: {e}")
                        st.session_state.palm_right_str      = None
                        st.session_state.palm_reading_result = None
                        st.session_state.palm_prep           = None
        elif st.session_state.palm_right_hash is not None or st.session_state.palm_right_needs_reupload:
            st.session_state.palm_right_str            = None
            st.session_state.palm_right_hash           = None
            st.session_state.palm_right_status         = None
            st.session_state.palm_right_bytes          = None
            st.session_state.palm_right_confirmed      = False
            st.session_state.palm_right_hand_confirmed = False
            st.session_state.palm_right_needs_reupload = False
            st.session_state.palm_right_regen_warning  = None
            st.session_state["_palm_right_image_name"] = None
            st.session_state.palm_reading_result       = None
            st.session_state.palm_prep                 = None

        # ── Right palm: preview, tips, hand confirmation ────────────────────────────
        if uploaded_right is not None and st.session_state.palm_right_bytes is not None:
            st.image(st.session_state.palm_right_bytes, caption="Right palm", width=150)
            for _tip in (st.session_state.palm_right_status or {}).get("geometry_tips", []):
                st.caption(_tip)
            if st.session_state.palm_right_regen_warning:
                st.warning(st.session_state.palm_right_regen_warning)
            if not st.session_state.palm_right_hand_confirmed:
                st.write("Is this your **Right** hand?")
                _rcy, _rcn = st.columns(2)
                with _rcy:
                    if st.button("Yes", key="right_hand_yes"):
                        st.session_state.palm_right_hand_confirmed = True
                        st.rerun()
                with _rcn:
                    if st.button("No (swap)", key="right_hand_no"):
                        try:
                            if st.session_state.palm_left_hash is not None:
                                (st.session_state.palm_left_str, st.session_state.palm_right_str) = \
                                    (st.session_state.palm_right_str, st.session_state.palm_left_str)
                                (st.session_state.palm_left_hash, st.session_state.palm_right_hash) = \
                                    (st.session_state.palm_right_hash, st.session_state.palm_left_hash)
                                (st.session_state.palm_left_status, st.session_state.palm_right_status) = \
                                    (st.session_state.palm_right_status, st.session_state.palm_left_status)
                                (st.session_state.palm_left_bytes, st.session_state.palm_right_bytes) = \
                                    (st.session_state.palm_right_bytes, st.session_state.palm_left_bytes)
                                (st.session_state.palm_left_confirmed, st.session_state.palm_right_confirmed) = \
                                    (st.session_state.palm_right_confirmed, st.session_state.palm_left_confirmed)
                                st.session_state.palm_left_hand_confirmed  = True
                                st.session_state.palm_right_hand_confirmed = True

                                # Regenerate descriptions so hand-framing matches each
                                # slot's new (post-swap) image. On failure, the swapped
                                # string above stays as a fallback — it describes these
                                # bytes already, just with the original hand's framing.
                                with st.spinner("Updating palm readings…"):
                                    try:
                                        st.session_state.palm_left_str = describe_palm_image(
                                            st.session_state.palm_left_bytes, "left"
                                        )
                                        st.session_state.palm_left_regen_warning = None
                                        st.session_state.palm_left_confirmed     = False
                                        st.session_state.palm_reading_result     = None
                                        st.session_state.palm_prep               = None
                                    except RuntimeError:
                                        st.session_state.palm_left_regen_warning = (
                                            "Could not regenerate the left palm reading after "
                                            "swapping — it may reference the wrong hand. "
                                            "Consider re-uploading this image."
                                        )
                                        st.session_state.palm_reading_result = None
                                        st.session_state.palm_prep           = None
                                    try:
                                        st.session_state.palm_right_str = describe_palm_image(
                                            st.session_state.palm_right_bytes, "right"
                                        )
                                        st.session_state.palm_right_regen_warning = None
                                        st.session_state.palm_right_confirmed     = False
                                        st.session_state.palm_reading_result      = None
                                        st.session_state.palm_prep                = None
                                    except RuntimeError:
                                        st.session_state.palm_right_regen_warning = (
                                            "Could not regenerate the right palm reading after "
                                            "swapping — it may reference the wrong hand. "
                                            "Consider re-uploading this image."
                                        )
                                        st.session_state.palm_reading_result = None
                                        st.session_state.palm_prep           = None
                            else:
                                st.session_state.palm_right_str            = None
                                st.session_state.palm_right_hash           = None
                                st.session_state.palm_right_status         = None
                                st.session_state.palm_right_bytes          = None
                                st.session_state.palm_right_confirmed      = False
                                st.session_state.palm_right_hand_confirmed = False
                                st.session_state.palm_right_needs_reupload = True
                                st.session_state.palm_reading_result       = None
                                st.session_state.palm_prep                 = None
                        except Exception as e:
                            st.error(f"Could not update palm state: {e}")
                        st.rerun()
            elif not st.session_state.palm_right_confirmed:
                with st.container():
                    st.markdown("**Review right palm description**")
                    st.markdown(st.session_state.palm_right_str)
                _rky, _rkn = st.columns(2)
                with _rky:
                    if st.button("Looks right — use this description", key="right_desc_confirm"):
                        st.session_state.palm_right_confirmed = True
                        st.rerun()
                with _rkn:
                    if st.button("Discard — re-upload", key="right_desc_discard"):
                        st.session_state.palm_right_str            = None
                        st.session_state.palm_right_hash           = None
                        st.session_state.palm_right_status         = None
                        st.session_state.palm_right_bytes          = None
                        st.session_state.palm_right_confirmed      = False
                        st.session_state.palm_right_hand_confirmed = False
                        st.session_state.palm_right_needs_reupload = False
                        st.session_state.palm_right_regen_warning  = None
                        st.session_state["_palm_right_image_name"] = None
                        st.session_state.palm_reading_result       = None
                        st.session_state.palm_prep                 = None
                        st.rerun()
            else:
                st.caption("✓ Description confirmed")
                with st.container():
                    st.markdown("**Right palm description**")
                    st.markdown(st.session_state.palm_right_str)
        elif st.session_state.palm_right_needs_reupload and uploaded_right is not None:
            st.warning(
                "This image doesn't belong in the Right hand slot — please remove it "
                "(✕ above) and upload it using the Left hand uploader instead."
            )

    # ── Spouse AstroSage PDF ──────────────────────────────────────────────────
    uploaded_spouse_pdf = st.file_uploader(
        "Spouse AstroSage PDF (optional)", type=["pdf"], key="spouse_pdf_uploader",
    )
    if uploaded_spouse_pdf is not None:
        if st.session_state["_spouse_pdf_name"] != uploaded_spouse_pdf.name:
            with st.spinner("Parsing spouse AstroSage PDF…"):
                _spouse_parse_result = parse_astrosage_pdf(uploaded_spouse_pdf.read())
            if _spouse_parse_result:
                st.session_state.spouse_pdf_context = _spouse_parse_result
                st.session_state["_spouse_pdf_name"] = uploaded_spouse_pdf.name
                st.success("Spouse AstroSage data loaded.")
            else:
                st.session_state.spouse_pdf_context = None
                st.warning("Could not extract sections — check this is an AstroSage PDF.")
    elif st.session_state["_spouse_pdf_name"] is not None:
        st.session_state.spouse_pdf_context = None
        st.session_state["_spouse_pdf_name"] = None

    if _PALM_ENABLED:
        # ── Hand detail photo ─────────────────────────────────────────────────────
        uploaded_hand_detail = st.file_uploader(
            "Hand detail photo (optional — for detailed palm analysis)",
            type=["jpg", "jpeg", "png"], key="hand_detail_uploader",
        )
        if uploaded_hand_detail is not None:
            if st.session_state["_hand_detail_image_name"] != uploaded_hand_detail.name:
                _hdb = uploaded_hand_detail.read()
                _hdh = hashlib.md5(_hdb).hexdigest()
                try:
                    with st.spinner("Analysing hand detail…"):
                        import io as _io
                        _hd_img = Image.open(_io.BytesIO(_hdb))
                        _hd_desc = describe_hand_detail_image(_hd_img)
                    st.session_state.hand_detail_str       = _hd_desc
                    st.session_state.hand_detail_hash      = _hdh
                    st.session_state.hand_detail_bytes     = _hdb
                    st.session_state.hand_detail_confirmed = False
                    st.session_state["_hand_detail_image_name"] = uploaded_hand_detail.name
                    st.session_state.palm_reading_result   = None
                    st.session_state.palm_prep             = None
                    st.success("Hand detail analysed — review below")
                except ValueError as e:
                    st.error(f"Could not analyse hand detail image: {e}")
                    st.session_state.hand_detail_str       = None
                    st.session_state.hand_detail_hash      = None
                    st.session_state.hand_detail_bytes     = None
                    st.session_state.hand_detail_confirmed = False
                    st.session_state.palm_reading_result   = None
                    st.session_state.palm_prep             = None
        elif st.session_state["_hand_detail_image_name"] is not None:
            st.session_state.hand_detail_str       = None
            st.session_state.hand_detail_hash      = None
            st.session_state.hand_detail_bytes     = None
            st.session_state.hand_detail_confirmed = False
            st.session_state["_hand_detail_image_name"] = None
            st.session_state.palm_reading_result   = None
            st.session_state.palm_prep             = None

        # ── Hand detail: review, confirm/discard (mirrors palm checkpoint) ────────
        if uploaded_hand_detail is not None and st.session_state.hand_detail_bytes is not None:
            st.image(st.session_state.hand_detail_bytes, caption="Hand detail", width=150)
            if not st.session_state.hand_detail_confirmed:
                with st.container():
                    st.markdown("**Review hand detail description**")
                    st.markdown(st.session_state.hand_detail_str)
                _hdky, _hdkn = st.columns(2)
                with _hdky:
                    if st.button("Looks right — use this description", key="hand_detail_confirm"):
                        st.session_state.hand_detail_confirmed = True
                        st.rerun()
                with _hdkn:
                    if st.button("Discard — re-upload", key="hand_detail_discard"):
                        st.session_state.hand_detail_str       = None
                        st.session_state.hand_detail_hash      = None
                        st.session_state.hand_detail_bytes     = None
                        st.session_state.hand_detail_confirmed = False
                        st.session_state["_hand_detail_image_name"] = None
                        st.session_state.palm_reading_result   = None
                        st.session_state.palm_prep             = None
                        st.rerun()
            else:
                st.caption("✓ Description confirmed")
                with st.container():
                    st.markdown("**Hand detail description**")
                    st.markdown(st.session_state.hand_detail_str)

        # ── Palm reading generation (Session 65 T4 upload-triggered artifact) ─────
        # Upload-triggered, never question-routed (CLAUDE.md "T4 architecture"
        # lock) — only confirmed vision-derived descriptions are ever passed
        # through (palm_left, palm_right, hand_detail alike, CLAUDE.md "Palm
        # human checkpoint" lock); an unconfirmed description is withheld even
        # if it exists.
        st.radio(
            "Which hand do you use for most everyday tasks?",
            options=["Left hand", "Right hand"],
            key="palm_dominant_side",
        )
        _dominant_is_left = st.session_state.palm_dominant_side == "Left hand"

        _confirmed_left = (
            st.session_state.palm_left_str if st.session_state.palm_left_confirmed else None
        )
        _confirmed_right = (
            st.session_state.palm_right_str if st.session_state.palm_right_confirmed else None
        )
        _confirmed_hand_detail = (
            st.session_state.hand_detail_str if st.session_state.hand_detail_confirmed else None
        )
        _dominant_str, _nondominant_str = (
            (_confirmed_left, _confirmed_right) if _dominant_is_left
            else (_confirmed_right, _confirmed_left)
        )

        if _dominant_str:
            # LEAF A -- dominant hand confirmed (regardless of non-dominant):
            # auto-eligible, non-dominant hand is dropped (passed as None).
            if st.button("Generate Palm Reading", key="generate_palm_reading_btn"):
                st.session_state.palm_nondominant_only = False
                _gen_left, _gen_right = (
                    (_dominant_str, None) if _dominant_is_left else (None, _dominant_str)
                )
                if _DOGFOOD_CAPTURE:
                    # S70 P6b: DOGFOOD path stops at Stage 1 only -- no
                    # voicing call yet. The blocking claims-inventory
                    # checkpoint (main area, below) gates the Stage-2
                    # complete_palm_reading() call behind an explicit human
                    # ack, same AI-reviewing-AI discipline as the CLAUDE.md
                    # "Palm human checkpoint" lock. A new click here while a
                    # checkpoint is already pending simply replaces palm_prep.
                    try:
                        with st.spinner("Extracting claims (Stage 1)…"):
                            st.session_state.palm_prep = prepare_palm_reading(
                                palm_left=_gen_left,
                                palm_right=_gen_right,
                                hand_detail=_confirmed_hand_detail,
                            )
                        st.session_state.palm_reading_result = None
                        st.rerun()
                    except (ValueError, RuntimeError) as e:
                        st.error(str(e))
                else:
                    # END-USER path: unchanged -- synchronous one-shot call,
                    # no checkpoint.
                    try:
                        with st.spinner("Generating your palm reading…"):
                            st.session_state.palm_reading_result = generate_palm_reading(
                                palm_left=_gen_left,
                                palm_right=_gen_right,
                                hand_detail=_confirmed_hand_detail,
                            )
                    except (ValueError, RuntimeError) as e:
                        st.error(str(e))
        elif _nondominant_str:
            # LEAF B -- only the non-dominant hand is confirmed: does NOT
            # auto-run, requires an explicit opt-in click.
            st.info(
                "You've confirmed only your non-dominant hand. Upload your "
                "dominant hand above for the full reading, or continue with "
                "this hand only — it reflects innate potential, not your "
                "current life trajectory."
            )
            if st.button("Continue with non-dominant hand only", key="generate_palm_reading_nondominant_btn"):
                st.session_state.palm_nondominant_only = True
                _gen_left, _gen_right = (
                    (None, _nondominant_str) if _dominant_is_left else (_nondominant_str, None)
                )
                if _DOGFOOD_CAPTURE:
                    try:
                        with st.spinner("Extracting claims (Stage 1)…"):
                            st.session_state.palm_prep = prepare_palm_reading(
                                palm_left=_gen_left,
                                palm_right=_gen_right,
                                hand_detail=_confirmed_hand_detail,
                            )
                        st.session_state.palm_reading_result = None
                        st.rerun()
                    except (ValueError, RuntimeError) as e:
                        st.error(str(e))
                else:
                    try:
                        with st.spinner("Generating your palm reading…"):
                            st.session_state.palm_reading_result = generate_palm_reading(
                                palm_left=_gen_left,
                                palm_right=_gen_right,
                                hand_detail=_confirmed_hand_detail,
                            )
                    except (ValueError, RuntimeError) as e:
                        st.error(str(e))
        # LEAF C -- neither hand confirmed: unchanged, no generate button.

if st.session_state.get("pdf_context"):
    _astrosage_sections = _split_astrosage_sections(st.session_state.pdf_context)
    with st.expander("Your AstroSage Report"):
        for _section_name, _section_content in _astrosage_sections:
            if _section_name in _WITHHELD_SECTIONS:
                continue
            st.subheader(_section_name)
            st.text(_section_content)

if _PALM_ENABLED:
    # S70 P6b: DOGFOOD-path blocking checkpoint -- only ever populated on the
    # _DOGFOOD_CAPTURE-on path (see the button block above), so this panel
    # never shows on the END-USER path. ACK-ONLY: claims render read-only,
    # no edit widgets of any kind. Gated on palm_reading_result being None so
    # the panel disappears the instant Ack (or a fresh Generate click, or any
    # of the confirmed-input clear sites above) resolves it.
    if st.session_state.palm_prep is not None and st.session_state.palm_reading_result is None:
        _prep = st.session_state.palm_prep
        st.subheader("Review extracted claims (Stage 1)")
        st.caption(
            "Every claim extracted from your confirmed hand descriptions, "
            "including any excluded from voicing. Nothing here is editable — "
            "ack to proceed to voicing, or decline to discard these claims."
        )
        if _prep.claims:
            for _claim in _prep.claims:
                _excl = (
                    f"excluded ({_claim.exclusion_reason})"
                    if _claim.excluded_from_voice
                    else "included"
                )
                st.caption(
                    f"{_claim.claim_id} | {_claim.feature} | {_citation_column(_claim)} | "
                    f"{_claim.valence} | {_excl}"
                )
        else:
            st.caption("No claims extracted.")
        _stage1_retry_features = _prep.diagnostics.get("stage1_retry_features", ())
        _stage1_failed_features = _prep.diagnostics.get("stage1_failed_features", ())
        st.caption(
            f"stage1_retry_features: "
            f"{', '.join(_stage1_retry_features) if _stage1_retry_features else 'NONE'}"
        )
        st.caption(
            f"stage1_failed_features: "
            f"{', '.join(_stage1_failed_features) if _stage1_failed_features else 'NONE'}"
        )

        _ack_col, _decline_col = st.columns(2)
        with _ack_col:
            if st.button("Ack — proceed to voicing", key="checkpoint_ack_btn"):
                try:
                    with st.spinner("Voicing your palm reading (Stage 2)…"):
                        st.session_state.palm_reading_result = complete_palm_reading(_prep)
                    st.session_state.palm_prep = None
                    if _DOGFOOD_CAPTURE:
                        # Fail-soft, same pattern as the END-USER path's
                        # capture call: a capture error must never block or
                        # alter generation/display.
                        _ack_confirmed_left = (
                            st.session_state.palm_left_str if st.session_state.palm_left_confirmed else None
                        )
                        _ack_confirmed_right = (
                            st.session_state.palm_right_str if st.session_state.palm_right_confirmed else None
                        )
                        _ack_confirmed_hand_detail = (
                            st.session_state.hand_detail_str if st.session_state.hand_detail_confirmed else None
                        )
                        try:
                            _capture_dogfood_run(
                                _ack_confirmed_left,
                                _ack_confirmed_right,
                                _ack_confirmed_hand_detail,
                                st.session_state.palm_reading_result,
                            )
                            st.caption("captured to dogfood log")
                        except Exception:
                            logger.warning("app.py: dogfood capture failed", exc_info=True)
                    st.rerun()
                except RuntimeError as e:
                    st.error(str(e))
                    # palm_prep is retained on failure -- user may retry ack
                    # or decline.
        with _decline_col:
            if st.button("Decline — discard claims", key="checkpoint_decline_btn"):
                if _DOGFOOD_CAPTURE:
                    try:
                        _capture_checkpoint_declined(_prep)
                    except Exception:
                        logger.warning("app.py: checkpoint-declined capture failed", exc_info=True)
                st.session_state.palm_prep = None
                st.rerun()

    if st.session_state.palm_reading_result is not None:
        _reading = st.session_state.palm_reading_result
        if not _reading.validation.passed:
            st.error(
                "Palm reading failed validation and cannot be shown: "
                + "; ".join(_reading.validation.failures)
            )
        else:
            if st.session_state.get("palm_nondominant_only"):
                st.warning(
                    "Reading based on your non-dominant hand only — this shows "
                    "inherited nature and potential, not current trajectory. "
                    "Upload your dominant hand for a full reading."
                )
            st.markdown(_reading.reading_text)
            with st.expander("Classical sources"):
                for _src in _reading.sources:
                    st.caption(_format_source_line(_src))
                    # S119 Step 5: a rule-sourced citation shows the
                    # verbatim span it rests on -- Cheiro (1911), public
                    # domain, DISPLAY ONLY. It is never fed back into any
                    # LLM prompt (the sources list is built after Stage 2
                    # has already run and is not passed to any generator).
                    _quote = _src.get("source_quote")
                    if _quote:
                        st.caption(f"> {_quote}")
            # S70 P6b: non-blocking, display-only, never gates the reading --
            # the full Stage-1 inventory (incl. excluded_from_voice claims),
            # collapsed by default.
            with st.expander("Claims inventory"):
                if _reading.claims:
                    for _claim in _reading.claims:
                        _excl = (
                            f"excluded ({_claim.exclusion_reason})"
                            if _claim.excluded_from_voice
                            else "included"
                        )
                        st.caption(
                            f"{_claim.claim_id} | {_claim.feature} | {_citation_column(_claim)} | "
                            f"{_claim.valence} | {_excl}"
                        )
                else:
                    st.caption("No claims extracted.")

if not st.session_state.chart_ready:
    st.info("Enter your birth details in the sidebar to begin.")

# Render conversation history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Chat input — disabled until chart is ready
prompt = st.chat_input(
    "Enter your birth details in the sidebar first" if not st.session_state.chart_ready else "Ask about your birth chart…",
    disabled=not st.session_state.chart_ready,
)

if prompt:
    if not st.session_state.chart_ready:
        st.warning("Please calculate your birth chart in the sidebar first.")
    else:
        with st.chat_message("user"):
            st.markdown(prompt)

        # Deterministic calc-engine pipeline ONLY (CLAUDE.md "V1 scope" lock):
        # answer_question() routes -> builds a DomainChartProfile -> formats
        # a DomainAnswer (REFUSAL included); render_answer() turns that into
        # display text. No partner chart wiring in V1 -- marriage questions
        # will REFUSAL via has_partner_data, same as any other domain's
        # REFUSAL (rendered like any other answer, not specially handled).
        # Both user+assistant messages are appended together, only after a
        # full success, so a failure anywhere in this chain leaves
        # st.session_state.messages completely unchanged (no partial turn).
        try:
            with st.spinner("Consulting the stars…"):
                domain_answer = answer_question(prompt, st.session_state.chart)
                answer_text = render_answer(domain_answer)

            st.session_state.messages.append({"role": "user", "content": prompt})

            with st.chat_message("assistant"):
                st.markdown(answer_text)

            st.session_state.messages.append({"role": "assistant", "content": answer_text})

            # Persist session to disk; non-fatal on failure
            try:
                st.session_state.session_mgr.save()
            except RuntimeError:
                st.warning("Session could not be saved. Chat history may not persist.")

        except Exception as e:
            st.error(f"{type(e).__name__}: {e}")
