"""
scripts/probe_pass5_preflight.py

Pre-flight smoke probe for Ring 3 pass 5, ported from scripts/probe_pass4_
preflight.py (S68 close-out state) to the S69 F-H two-stage pipeline
(extract_claims Stage 1 + voice_claims Stage 2). THROWAWAY script, NOT a
scoring pass -- Ring 3 pass 5 itself still requires fresh uploads through
the real Streamlit app with live human checkpoints (CLAUDE.md T4 golden
semantics / Palm human checkpoint locks, extended by S70 P6b's own
claims-ack checkpoint). This script exists only to catch a wiring defect
in the landed two-stage pipeline BEFORE spending a fresh-upload pass-5 run
on it.

pass4's probe predates F-H and exercised RETIRED code paths (_run_ring1_
checks, _check_feature_coverage, CHUNK_ANCHOR_TAG_PATTERN) that
generate_palm_reading() no longer calls -- this is a genuine re-port, not
a copy-edit, with the following differences:
  1. Retrieval/gate introspection (fixture self-gate, vision descriptions,
     _parse_fields/_parse_bullet_fields/_gather_feature_texts/_retrieve_
     per_feature/_apply_support_gate, per-feature retrieval map, support
     gate verdicts, valid_chunk_ids) is UNCHANGED -- retrieval and the
     support gate predate and are untouched by F-H.
  2. The old "first-draft Ring 1 failures / coverage misses" section is
     DROPPED, not replaced -- it existed only to recompute the retired
     single-call `_run_ring1_checks`/`_check_feature_coverage` against a
     capturing client's first draft. The two-stage pipeline's own retries
     are OWNED internally by claim_extraction.extract_claims (per-feature,
     up to 2 calls each) and claim_voicing.voice_claims (whole-reading, up
     to 2 calls) -- PalmReadingResult.stage1_retry_features/stage2_retry_
     used already surface whether either fired, with no need for this
     probe to guess at internal call boundaries from a flat capturing-
     client call list.
  3. `_VALIDATOR_PREFIXES` drops the retired anchor_completeness/anchor_
     legality rows and gains three Stage-2 validator prefixes
     (tag_legality, claim_coverage, doctrine_guard) -- PalmReadingResult.
     validation.failures is now voice_result.validation_failures (V-3/V-4/
     V-5) merged with the 6 surviving display checks (unchanged names).
  4. The old assert 4 (CHUNK_ANCHOR_TAG_PATTERN presence in reading_text_
     tagged) is REPLACED by a [C<n>]-tag presence check against the NEW
     `{[C<n>], [OBS], [FLOW]}` vocabulary (claim_voicing's own tags, not
     CHUNK_ANCHOR_TAG_PATTERN's `[OBS]`/`[<book>_p<n>_c<n>]` vocabulary).
  5. Two NEW asserts (5/6) close-inventory-check the claims mechanism
     itself: every non-excluded claim's chunk_id must belong to this
     probe's own recomputed gated chunk-id union (5), and every [C<n>]
     tag actually cited in reading_text_tagged must resolve to a member
     of the non-excluded claim_id set (6) -- both read-only, black-box
     checks from OUTSIDE claim_extraction.py/claim_voicing.py, not a
     re-test of their own internal E-1/V-3/V-4 validators.
  6. Stage1/Stage2 retry fields are reported verbatim (data, not
     asserted) -- a single run is not rate evidence, per the S68 Run-B
     evidence-file precedent (a single observation doesn't establish a
     rate; report it, don't assert a threshold against it).
  7. Report path is diagnostics/pass5_preflight_S70.md, a dedicated file
     for this probe -- NOT diagnostics/latest_run.md (CLAUDE.md Working
     Style #10's routing convention is for TASK reports; this is a
     standalone probe artifact, same convention pass4's own probe used
     before it, and pass3's before that).

Uses the data/test_images/ fixtures -- sanctioned for mechanical probes
only (per the instructing prompt), never a substitute for Ring 3's
fresh-upload requirement. This script bypasses BOTH human checkpoints by
construction (it is headless): the S65/S66 F1 palm-description confirm
gate, AND S70 P6b's new claims-ack checkpoint (this script calls
generate_palm_reading() directly, the prepare/complete two-phase seam
un-checkpointed) -- vision descriptions and the claims inventory below
are captured and reported verbatim but are NOT human-confirmed/acked;
both gates are unaffected and still apply to any real user-facing flow.

Runs the Run-C shape (hardest case, per Ring 3 pass-2/pass-3/pass-4
precedent): both palm images + hand_detail, live OpenAI vision + live
two-stage generation.

Does NOT touch agent/interpretive/palm_reading.py, claim_extraction.py,
claim_voicing.py, or any other production module -- imports private
helpers read-only for introspection, same as the pass-3/pass-4 scripts.

If any product-code bug surfaces, this script stops and reports it -- it
does not attempt a fix (out of scope for a pre-flight probe).
"""

from __future__ import annotations

import re
import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PIL import Image

from agent.interpretive import palm_reading
from agent.palm_processor import describe_hand_detail_image, describe_palm_image

_REPORT_PATH = Path(__file__).resolve().parent.parent / "diagnostics" / "pass5_preflight_S70.md"

_FIXTURE_DIR = Path(__file__).resolve().parent.parent / "data" / "test_images"
_LEFT_PATH = _FIXTURE_DIR / "palm_left_test.jpg"
_RIGHT_PATH = _FIXTURE_DIR / "palm_right_test.jpg"
_HAND_DETAIL_PATH = _FIXTURE_DIR / "Back Hand.jpeg"

# Assert 4's tag-presence regex, per the instructing prompt's literal
# spec -- deliberately a fresh, narrow pattern, not palm_reading.py's own
# module-level _STAGE2_TAG_PATTERN (which also matches [OBS]/[FLOW]);
# this probe checks specifically for the claim-citation tag kind.
_CLAIM_TAG_PATTERN = re.compile(r"\[C\d+\]")

# Two-stage pipeline: PalmReadingResult.validation.failures is voice_
# claims' own V-3/V-4/V-5 (tag_legality/claim_coverage/doctrine_guard)
# merged with palm_reading._run_display_checks' 6 surviving display
# checks (jargon/self_help/unsupported_dates/length/banned_feature_
# mention/exemplar_echo) -- V-1/V-2/anchor_completeness/anchor_legality
# are RETIRED (not called), so they are NOT in this table (see module
# docstring point 3).
_VALIDATOR_PREFIXES: tuple[tuple[str, str], ...] = (
    ("jargon_blacklist", "jargon_blacklist:"),
    ("self_help_blacklist", "self_help_blacklist:"),
    ("unsupported_dates", "unsupported_dates:"),
    ("length_guard", "length_guard:"),
    ("banned_feature_mention", "unsupported feature mentioned:"),
    ("exemplar_echo", "exemplar_echo:"),
    ("tag_legality", "tag_legality:"),
    ("claim_coverage", "claim_coverage:"),
    ("doctrine_guard", "doctrine_guard:"),
)


class _AbortProbe(Exception):
    """Raised to stop the probe with a diagnosis -- caught in main(),
    never lets a bare traceback stand in for a reported reason."""


# ─── Self-gate: fixtures must exist and be readable, no substitution ───

def _self_gate_fixtures() -> tuple[bytes, bytes, Image.Image]:
    missing = [p for p in (_LEFT_PATH, _RIGHT_PATH, _HAND_DETAIL_PATH) if not p.exists()]
    if missing:
        raise _AbortProbe(
            "SELF-GATE FAILED: missing fixture(s): "
            + ", ".join(str(p) for p in missing)
            + " -- data/test_images/ fixtures are sanctioned for this probe, "
            "but substituting other images is not. Stopping."
        )
    try:
        left_bytes = _LEFT_PATH.read_bytes()
        right_bytes = _RIGHT_PATH.read_bytes()
        hd_image = Image.open(_HAND_DETAIL_PATH)
        hd_image.load()
    except Exception as exc:
        raise _AbortProbe(
            f"SELF-GATE FAILED: fixture(s) present but unreadable: {exc}"
        ) from exc
    return left_bytes, right_bytes, hd_image


# ─── Capturing client: records every chat.completions.create() call's ──
# ─── returned text, in order -- across BOTH stages (Stage 1's per-      ─
# ─── feature calls and Stage 2's whole-reading call share the same      ─
# ─── client, per generate_palm_reading()'s own contract).               ─

class _CapturingCompletions:
    def __init__(self, real_completions, calls: list[str]):
        self._real = real_completions
        self._calls = calls

    def create(self, **kwargs):
        response = self._real.create(**kwargs)
        self._calls.append(response.choices[0].message.content)
        return response


class _CapturingChat:
    def __init__(self, real_chat, calls: list[str]):
        self.completions = _CapturingCompletions(real_chat.completions, calls)


class _CapturingClient:
    def __init__(self, real_client):
        self.calls: list[str] = []
        self.chat = _CapturingChat(real_client.chat, self.calls)


# ─── Report formatting helpers ──────────────────────────────────────────

def _fmt_retrieval_map(per_feature_results: dict[str, list[dict]]) -> list[str]:
    lines = ["| Feature | Chunks (page_ref, score, chunk_id) |", "|---|---|"]
    for feature in palm_reading._FEATURE_REGISTRY:
        chunks = per_feature_results.get(feature, [])
        if not chunks:
            lines.append(f"| {feature} | _(none -- skipped or retrieval failed)_ |")
            continue
        cell = "; ".join(
            f"(p.{c['page_ref']}, {c['score']:.4f}, {c['chunk_id']})" for c in chunks
        )
        lines.append(f"| {feature} | {cell} |")
    return lines


def _fmt_validator_breakdown(failures: tuple[str, ...]) -> list[str]:
    lines = ["| Validator | Result | Detail |", "|---|---|---|"]
    for name, prefix in _VALIDATOR_PREFIXES:
        hit = next((f for f in failures if f.startswith(prefix)), None)
        if hit:
            lines.append(f"| {name} | FAIL | {hit} |")
        else:
            lines.append(f"| {name} | pass | -- |")
    # Anything present in failures but not matched by a known prefix --
    # would indicate a validator this script's prefix table hasn't been
    # kept in sync with; surfaced rather than silently dropped.
    known = {f for name, prefix in _VALIDATOR_PREFIXES for f in failures if f.startswith(prefix)}
    unclassified = [f for f in failures if f not in known]
    for f in unclassified:
        lines.append(f"| UNCLASSIFIED | FAIL | {f} |")
    return lines


def _fmt_claims_inventory(claims: tuple) -> list[str]:
    """P6a pipe format (frontend/app.py's _capture_dogfood_run), reused
    verbatim here so this probe's claims table is diff-able against real
    dogfood_capture.md RUN blocks."""
    lines = [
        "claim_id | feature | chunk_id | valence | excluded_from_voice | "
        "exclusion_reason | condition_text | claim_text"
    ]
    if not claims:
        lines.append("claims_inventory: EMPTY")
        return lines
    for claim in claims:
        claim_text_oneline = claim.claim_text.replace("\n", " ")
        lines.append(
            f"{claim.claim_id} | {claim.feature} | {claim.chunk_id} | "
            f"{claim.valence} | {claim.excluded_from_voice} | "
            f"{claim.exclusion_reason} | {claim.condition_text} | "
            f"{claim_text_oneline}"
        )
    return lines


def main() -> None:
    lines: list[str] = []
    lines.append("# Pre-flight smoke probe for Ring 3 pass 5 (S69 F-H two-stage pipeline)")
    lines.append("")
    lines.append(
        "**THROWAWAY SCRIPT. NOT A SCORING PASS.** Ring 3 pass 5 itself "
        "still requires fresh uploads through the real app with live "
        "human checkpoints (CLAUDE.md T4 golden semantics / Palm human "
        "checkpoint locks, extended by S70 P6b's own claims-ack "
        "checkpoint). This probe uses `data/test_images/` fixtures "
        "(sanctioned for mechanical probes only) to catch a wiring "
        "defect in the landed S69 F-H two-stage pipeline before "
        "spending a fresh-upload pass-5 run on it. Vision descriptions "
        "and the claims inventory below are captured verbatim but are "
        "NOT human-confirmed/acked -- this headless script bypasses "
        "BOTH the S65/S66 F1 palm-description checkpoint UI and S70 "
        "P6b's claims-ack checkpoint by construction (it calls "
        "generate_palm_reading() directly, the prepare/complete seam "
        "un-checkpointed); both gates are unaffected and still apply to "
        "any real user-facing flow."
    )
    lines.append("")
    lines.append(
        "Run shape: Run-C (hardest case) -- both palm images + "
        "hand_detail, live OpenAI vision + live two-stage generation."
    )
    lines.append("")

    try:
        left_bytes, right_bytes, hd_image = _self_gate_fixtures()
        lines.append("## Fixtures")
        lines.append("")
        lines.append(f"- LEFT: `{_LEFT_PATH}`")
        lines.append(f"- RIGHT: `{_RIGHT_PATH}`")
        lines.append(f"- HAND_DETAIL: `{_HAND_DETAIL_PATH}`")
        lines.append("")

        # ── Vision descriptions (live) ──────────────────────────────
        try:
            palm_left = describe_palm_image(left_bytes, "left")
            palm_right = describe_palm_image(right_bytes, "right")
            hand_detail = describe_hand_detail_image(hd_image)
        except Exception as exc:
            raise _AbortProbe(
                "PRODUCT-CODE BUG SURFACED (vision description step, "
                f"palm_processor.py): {exc}\n{traceback.format_exc()}"
            ) from exc

        lines.append("## Confirmed descriptions (NOT human-confirmed -- headless probe)")
        lines.append("")
        lines.append("**LEFT** (verbatim):")
        lines.append("```")
        lines.append(palm_left)
        lines.append("```")
        lines.append("")
        lines.append("**RIGHT** (verbatim):")
        lines.append("```")
        lines.append(palm_right)
        lines.append("```")
        lines.append("")
        lines.append("**HAND_DETAIL** (verbatim):")
        lines.append("```")
        lines.append(hand_detail)
        lines.append("```")
        lines.append("")

        # ── Raw per-feature retrieval (pre-gate), via the actual ────
        # ── production private helpers, read-only introspection ─────
        # ── (UNCHANGED from pass4's probe -- retrieval/gate predate F-H) ─
        try:
            left_fields = palm_reading._parse_fields(palm_left)
            right_fields = palm_reading._parse_fields(palm_right)
            hd_fields = palm_reading._parse_bullet_fields(hand_detail)
            texts_by_feature = palm_reading._gather_feature_texts(
                left_fields, right_fields, hd_fields
            )
            per_feature_results, failed_features = palm_reading._retrieve_per_feature(
                left_fields, right_fields, hd_fields
            )
            gated_results, supported_features, unsupported_features = (
                palm_reading._apply_support_gate(per_feature_results, texts_by_feature)
            )
            decline_block = palm_reading._build_decline_block(unsupported_features)
            # Same union-of-gated-chunk-ids computation generate_palm_
            # reading() does internally (now feeding claim_extraction's
            # own per-feature E-1 legality check rather than the retired
            # V-2) -- needed here for asserts 5/6's outside-in closed-
            # inventory check below.
            valid_chunk_ids = frozenset(
                c["chunk_id"] for chunks in gated_results.values() for c in chunks
            )
        except Exception as exc:
            raise _AbortProbe(
                "PRODUCT-CODE BUG SURFACED (retrieval/gate introspection, "
                f"palm_reading.py private helpers): {exc}\n{traceback.format_exc()}"
            ) from exc

        lines.append("## Per-feature retrieval map (raw, pre-gate, all 10 registry features)")
        lines.append("")
        if failed_features:
            lines.append(f"**Retrieval FAILED for**: {', '.join(failed_features)}")
            lines.append("")
        lines += _fmt_retrieval_map(per_feature_results)
        lines.append("")

        lines.append("## Support gate verdicts")
        lines.append("")
        lines.append(f"- **supported_features** (registry order): {list(supported_features)}")
        lines.append(f"- **unsupported_features** (registry order): {list(unsupported_features)}")
        genuine_absence = [
            f for f in palm_reading._FEATURE_REGISTRY
            if f not in supported_features and f not in unsupported_features
        ]
        lines.append(
            f"- **genuine negative-absence** (in neither tuple -- nothing to "
            f"support, nothing to decline): {genuine_absence}"
        )
        lines.append(
            f"- **valid_chunk_ids** (union, count={len(valid_chunk_ids)}): "
            f"{sorted(valid_chunk_ids)}"
        )
        lines.append("")

        lines.append("## Python decline block (pre-Stage-1 estimate, from the gate alone)")
        lines.append("")
        if decline_block:
            lines.append(f"Appended for: {list(unsupported_features)}")
            lines.append("")
            lines.append("```")
            lines.append(decline_block)
            lines.append("```")
        else:
            lines.append("Not appended (unsupported_features is empty).")
        lines.append(
            "\n(Note: the FINAL decline block generate_palm_reading() builds "
            "can differ from this -- `_compute_decline_features` also folds "
            "in Stage-1 extraction failures and gate-supported-but-zero-"
            "claims features; see the final Ring 1 result section below for "
            "the authoritative reading.)"
        )
        lines.append("")

        # ── Full pipeline call (live), via capturing client ──────────
        from openai import OpenAI
        real_client = OpenAI()
        capturing_client = _CapturingClient(real_client)

        try:
            result = palm_reading.generate_palm_reading(
                palm_left, palm_right, hand_detail, client=capturing_client
            )
        except Exception as exc:
            raise _AbortProbe(
                "PRODUCT-CODE BUG SURFACED (generate_palm_reading call): "
                f"{exc}\n{traceback.format_exc()}"
            ) from exc

        draft_texts = capturing_client.calls
        lines.append("## LLM call count")
        lines.append("")
        lines.append(
            f"{len(draft_texts)} chat.completions.create() call(s) captured "
            f"total across BOTH stages (Stage 1: up to 2 calls PER attempted "
            f"feature, own F2c retry; Stage 2: up to 2 calls, own whole-"
            f"reading F2c retry -- no single global cap, unlike the old "
            f"single-call architecture's flat 2-call ceiling)."
        )
        lines.append("")

        lines.append("## Stage1/Stage2 retry fields (data, NOT asserted -- single run, no rate claim)")
        lines.append("")
        lines.append(
            f"- `stage1_retry_features`: {list(result.stage1_retry_features) if result.stage1_retry_features else 'NONE'}"
        )
        lines.append(f"- `stage2_retry_used`: {result.stage2_retry_used}")
        lines.append(f"- `retry_used` (COMPAT, true if either stage retried): {result.retry_used}")
        lines.append("")

        lines.append("## Final Ring 1 result (authoritative, from PalmReadingResult.validation)")
        lines.append("")
        lines.append(f"`passed`: **{result.validation.passed}**")
        lines.append("")
        lines += _fmt_validator_breakdown(result.validation.failures)
        lines.append("")
        lines.append(
            f"`validation.warnings` (F-A retired, superseded by Stage 2's "
            f"own V-4 claim-coverage check -- always `()` now): "
            f"{list(result.validation.warnings) if result.validation.warnings else 'none'}"
        )
        lines.append("")

        lines.append("## Full claims inventory (P6a pipe format, PalmReadingResult.claims verbatim)")
        lines.append("")
        lines += _fmt_claims_inventory(result.claims)
        lines.append("")

        lines.append("## reading_text (verbatim, final -- includes decline block + disclaimer, tags STRIPPED)")
        lines.append("")
        lines.append("```")
        lines.append(result.reading_text)
        lines.append("```")
        lines.append("")

        lines.append("## reading_text_tagged (verbatim, Stage 2 raw voiced draft -- [C<n>]/[OBS]/[FLOW] tags intact)")
        lines.append("")
        lines.append("```")
        lines.append(result.reading_text_tagged)
        lines.append("```")
        lines.append("")

        lines.append("## sources (from PalmReadingResult, per-claim-cited only)")
        lines.append("")
        for s in result.sources:
            lines.append(f"- {s['book']}, p.{s['page']} (score: {s['score']}) -- feature: {s['feature']}")
        lines.append("")

        # ── Deterministic sanity asserts (fail loudly) ────────────────
        lines.append("## Sanity asserts")
        lines.append("")

        assert_failures: list[str] = []

        # 1. >=1 supported feature.
        if len(result.supported_features) < 1:
            assert_failures.append(
                "ASSERT FAILED: at least 1 feature supported -- got 0. "
                "ALL-DECLINE is a pipeline defect (retrieval or support-gate "
                "wiring broken), not a legitimate outcome for this fixture "
                "set (both palm images observe multiple features with known "
                "Cheiro-corpus coverage, e.g. life line/head line)."
            )
        else:
            lines.append(
                f"- [x] At least 1 feature supported -- got "
                f"{len(result.supported_features)}: {list(result.supported_features)}"
            )

        # 2. validation.passed=True on the final result.
        if not result.validation.passed:
            assert_failures.append(
                "ASSERT FAILED: Ring 1 passed=True on the final draft -- got "
                f"False. Failures: {list(result.validation.failures)}. Both "
                "Stage 1 and Stage 2 already own their own hard-capped F2c "
                "retry internally -- a failing final draft is a real, "
                "reportable defect, not something this probe can retry past."
            )
        else:
            lines.append("- [x] Ring 1 `passed=True` on the final draft")

        # 3. No 6-gram exemplar echo in reading_text.
        echo_hits = palm_reading._check_exemplar_echo(result.reading_text)
        if echo_hits:
            assert_failures.append(
                f"ASSERT FAILED: no 6-gram exemplar echo in reading_text -- "
                f"got: {echo_hits}"
            )
        else:
            lines.append("- [x] No 6-gram exemplar echo in `reading_text`")

        # 4. REPLACED: reading_text_tagged non-empty AND contains >=1
        # [C<n>] tag -- the OLD CHUNK_ANCHOR_TAG_PATTERN assert (A1's
        # [OBS]/[chunk_id] vocabulary) is retired with that architecture;
        # NOT imported here.
        if not result.reading_text_tagged or not result.reading_text_tagged.strip():
            assert_failures.append(
                "ASSERT FAILED: reading_text_tagged is empty/whitespace-only "
                "-- Stage 2's own tagging contract was not exercised."
            )
        elif not _CLAIM_TAG_PATTERN.search(result.reading_text_tagged):
            assert_failures.append(
                "ASSERT FAILED: reading_text_tagged contains no [C<n>] claim-"
                "citation tag at all (regex \\[C\\d+\\])."
            )
        else:
            lines.append("- [x] `reading_text_tagged` is populated and contains >=1 `[C<n>]` tag")

        # 5. NEW: result.claims non-empty; every non-excluded claim's
        # chunk_id appears in the union of gated chunk ids (this probe's
        # own recomputed valid_chunk_ids from the production private
        # helpers above -- read-only introspection, not a re-test of
        # claim_extraction's own internal E-1 legality check, which runs
        # against ITS OWN per-feature chunk map, not this probe's union).
        if not result.claims:
            assert_failures.append(
                "ASSERT FAILED: result.claims is empty -- Stage 1 extracted "
                "nothing at all from a fixture set with known gated-chunk "
                "coverage (see per-feature retrieval map above)."
            )
        else:
            lines.append(f"- [x] `result.claims` is non-empty -- got {len(result.claims)} claim(s)")
            non_excluded = [c for c in result.claims if not c.excluded_from_voice]
            orphaned = [c for c in non_excluded if c.chunk_id not in valid_chunk_ids]
            if orphaned:
                assert_failures.append(
                    "ASSERT FAILED: non-excluded claim(s) cite a chunk_id "
                    "outside this probe's own recomputed gated chunk-id "
                    "union -- claim_id(s)/chunk_id(s): "
                    + ", ".join(f"{c.claim_id}->{c.chunk_id}" for c in orphaned)
                )
            else:
                lines.append(
                    f"- [x] Every non-excluded claim's chunk_id is a member "
                    f"of the gated chunk-id union -- checked {len(non_excluded)} "
                    f"non-excluded claim(s) against {len(valid_chunk_ids)} valid id(s)"
                )

        # 6. NEW: every claim_id cited in reading_text_tagged (a [C<n>]
        # tag) is a member of the non-excluded claim id set -- closed-
        # inventory check FROM THE OUTSIDE (black-box on reading_text_
        # tagged), independent of claim_voicing's own internal V-4 check.
        non_excluded_ids = {c.claim_id for c in result.claims if not c.excluded_from_voice}
        cited_ids = {
            m.group(0)[1:-1] for m in _CLAIM_TAG_PATTERN.finditer(result.reading_text_tagged)
        }
        uncited_orphans = cited_ids - non_excluded_ids
        if uncited_orphans:
            assert_failures.append(
                "ASSERT FAILED: reading_text_tagged cites claim_id(s) not in "
                f"the non-excluded claim id set: {sorted(uncited_orphans)}"
            )
        else:
            lines.append(
                f"- [x] Every `[C<n>]` tag cited in `reading_text_tagged` "
                f"resolves to a member of the non-excluded claim id set -- "
                f"cited {sorted(cited_ids)} against {sorted(non_excluded_ids)}"
            )

        lines.append("")

        if assert_failures:
            lines.append("## ABORT -- sanity assert(s) failed")
            lines.append("")
            for f in assert_failures:
                lines.append(f"- {f}")
            lines.append("")
            _REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")
            print(f"Report written to {_REPORT_PATH}")
            print("\n".join(assert_failures))
            sys.exit(1)

        lines.append("## Verdict")
        lines.append("")
        lines.append(
            "All 6 sanity asserts PASSED. This is a wiring smoke check "
            "only -- it says nothing about interpretive quality/citation "
            "accuracy (that is Ring 3 pass 5's job, on fresh uploads, "
            "human-scored, with both checkpoints live). No product code "
            "was touched or fixed by this script."
        )

        _REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")
        print(f"Report written to {_REPORT_PATH}")
        print(
            f"stage1_retry_features={list(result.stage1_retry_features)} "
            f"stage2_retry_used={result.stage2_retry_used} "
            f"passed={result.validation.passed} "
            f"supported={len(result.supported_features)} "
            f"unsupported={len(result.unsupported_features)} "
            f"claims={len(result.claims)}"
        )

    except _AbortProbe as exc:
        lines.append("## ABORT")
        lines.append("")
        lines.append(str(exc))
        lines.append("")
        _REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")
        print(f"Report written to {_REPORT_PATH}")
        print(str(exc))
        sys.exit(1)


if __name__ == "__main__":
    main()
