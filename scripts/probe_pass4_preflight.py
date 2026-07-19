"""
scripts/probe_pass4_preflight.py

Pre-flight smoke probe for Ring 3 pass 4 (S68 close-out state). THROWAWAY
script, NOT a scoring pass -- Ring 3 pass 4 itself still requires fresh
uploads through the real Streamlit app with live human checkpoints
(CLAUDE.md "T4 golden semantics" / "Palm human checkpoint" locks); this
script exists only to catch a wiring/pipeline defect in the S68 F-C/F-A/
F-B landed work (chunk-anchor tagging, Ring 1 V-1/V-2 anchor validators,
supported-feature coverage check, two-tier absence classification)
BEFORE spending a fresh-upload pass-4 run on it.

Ported from scripts/probe_pass3_preflight.py (S67 close-out, `2da2819`)
-- same fixtures, same Run-C shape, same capturing-client mechanism.
Updates for the S68 pipeline:
  1. `_run_ring1_checks` is now an 8-validator sequence (V-1
     `_check_tag_completeness` + V-2 `_check_anchor_legality` appended,
     A1/S68 F-C) and takes a `valid_chunk_ids` argument the pass-3
     script never had to pass -- this script now computes the same
     union-of-gated-chunk-ids `generate_palm_reading()` computes
     internally, via the same private helpers, for its own first-draft
     best-effort recomputation.
  2. `_VALIDATOR_PREFIXES` gained the 2 new validator names.
  3. Reports `result.reading_text_tagged` (the A1 raw tagged draft) as
     its own section, not just the stripped `result.reading_text`.
  4. Reports `result.validation.warnings` (F-A coverage warnings) in
     the final Ring 1 result section, and best-effort recomputes
     `_check_feature_coverage` for the first draft (mirrors the
     existing first-draft Ring 1 failures best-effort recomputation --
     same caveat: not literally the same object generate_palm_reading()
     computed internally, reported as a diagnostic, not asserted).

Uses the data/test_images/ fixtures -- sanctioned for mechanical probes
only (per the instructing prompt), never a substitute for Ring 3's
fresh-upload requirement. This script also bypasses the palm
human-checkpoint UI gate (S65/S66 F1 lock) by construction (it is
headless) -- the vision descriptions below are captured and reported
verbatim but are NOT human-confirmed; that gate still applies to any
real user-facing flow and is unaffected by this probe.

Runs the Run-C shape (hardest case, per Ring 3 pass-2/pass-3 precedent):
both palm images + hand_detail, live OpenAI vision + generation.

Does NOT touch agent/interpretive/palm_reading.py or any other
production module -- imports its private helpers read-only for
introspection, same as the pass-3 script.

If any product-code bug surfaces, this script stops and reports it --
it does not attempt a fix (out of scope for a pre-flight probe).
"""

from __future__ import annotations

import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PIL import Image

from agent.interpretive import palm_reading
from agent.palm_processor import describe_hand_detail_image, describe_palm_image

_REPORT_PATH = Path(__file__).resolve().parent.parent / "diagnostics" / "latest_run.md"

_FIXTURE_DIR = Path(__file__).resolve().parent.parent / "data" / "test_images"
_LEFT_PATH = _FIXTURE_DIR / "palm_left_test.jpg"
_RIGHT_PATH = _FIXTURE_DIR / "palm_right_test.jpg"
_HAND_DETAIL_PATH = _FIXTURE_DIR / "Back Hand.jpeg"

# S68: 8 validator names/prefixes (was 6 in the pass-3 script) -- V-1/V-2
# appended, same order _run_ring1_checks itself runs them in.
_VALIDATOR_PREFIXES: tuple[tuple[str, str], ...] = (
    ("jargon_blacklist", "jargon_blacklist:"),
    ("self_help_blacklist", "self_help_blacklist:"),
    ("unsupported_dates", "unsupported_dates:"),
    ("length_guard", "length_guard:"),
    ("banned_feature_mention", "unsupported feature mentioned:"),
    ("exemplar_echo", "exemplar_echo:"),
    ("anchor_completeness", "anchor_completeness:"),
    ("anchor_legality", "anchor_legality:"),
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
# ─── returned text, in order -- the only way to see the FIRST draft ────
# ─── when generate_palm_reading()'s retry fires (it only returns the ───
# ─── FINAL draft in PalmReadingResult).                                ─

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


def main() -> None:
    lines: list[str] = []
    lines.append("# Pre-flight smoke probe for Ring 3 pass 4 (S68 close-out state)")
    lines.append("")
    lines.append(
        "**THROWAWAY SCRIPT. NOT A SCORING PASS.** Ring 3 pass 4 itself "
        "still requires fresh uploads through the real app with live "
        "human checkpoints (CLAUDE.md T4 golden semantics / Palm human "
        "checkpoint locks). This probe uses `data/test_images/` "
        "fixtures (sanctioned for mechanical probes only) to catch a "
        "pipeline defect in the S68 F-C/F-A/F-B landed work before "
        "spending a fresh-upload pass-4 run on it. Vision descriptions "
        "below are captured verbatim but are NOT human-confirmed -- "
        "this headless script bypasses the S65/S66 F1 checkpoint UI by "
        "construction; that gate is unaffected and still applies to any "
        "real user-facing flow."
    )
    lines.append("")
    lines.append(
        "Run shape: Run-C (hardest case) -- both palm images + "
        "hand_detail, live OpenAI vision + generation."
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
            # S68 F-C: same union-of-gated-chunk-ids computation
            # generate_palm_reading() does internally for V-2 anchor
            # legality -- needed here for this probe's own first-draft
            # best-effort Ring 1 recomputation below.
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
        lines.append(f"- **valid_chunk_ids** (V-2 union, count={len(valid_chunk_ids)}): {sorted(valid_chunk_ids)}")
        lines.append("")

        lines.append("## Python decline block")
        lines.append("")
        if decline_block:
            lines.append(f"Appended for: {list(unsupported_features)}")
            lines.append("")
            lines.append("```")
            lines.append(decline_block)
            lines.append("```")
        else:
            lines.append("Not appended (unsupported_features is empty).")
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
        lines.append(f"{len(draft_texts)} chat.completions.create() call(s) captured (hard cap 2).")
        lines.append("")

        # First-draft diagnostic (only meaningful if a retry fired).
        # Best-effort: uses THIS probe's own locally-computed
        # unsupported_features/context_corpus/valid_chunk_ids (from the
        # retrieval/gate section above), which should match
        # generate_palm_reading()'s internal computation deterministically
        # (same input descriptions) but is not literally the same object
        # -- reported as a diagnostic, not asserted.
        context_corpus = (
            " ".join(part for part in (palm_left, palm_right, hand_detail) if part)
            + " "
            + " ".join(c["text"] for chunks in gated_results.values() for c in chunks)
        )

        lines.append("## retry_used + first-draft Ring 1 failures / coverage misses")
        lines.append("")
        lines.append(f"`retry_used`: **{result.retry_used}**")
        lines.append("")
        if result.retry_used and len(draft_texts) >= 1:
            first_draft_failures = tuple(
                palm_reading._run_ring1_checks(
                    draft_texts[0], context_corpus, unsupported_features, valid_chunk_ids
                )
            )
            first_draft_coverage_misses = tuple(
                palm_reading._check_feature_coverage(
                    draft_texts[0], gated_results, supported_features
                )
            )
            lines.append(
                "First-draft Ring 1 failures (best-effort recomputation "
                "against this probe's own locally-computed "
                "unsupported_features/context_corpus/valid_chunk_ids -- "
                "see caveat above; this is what triggered the retry, "
                "combined with any coverage miss below):"
            )
            lines.append("")
            lines += _fmt_validator_breakdown(first_draft_failures)
            lines.append("")
            lines.append(
                f"First-draft coverage misses (F-A, best-effort recomputation): "
                f"{list(first_draft_coverage_misses) if first_draft_coverage_misses else 'none'}"
            )
        else:
            lines.append("N/A -- first draft passed Ring 1 cleanly with no coverage miss, no retry fired.")
        lines.append("")

        lines.append("## Final Ring 1 result (authoritative, from PalmReadingResult.validation)")
        lines.append("")
        lines.append(f"`passed`: **{result.validation.passed}**")
        lines.append("")
        lines += _fmt_validator_breakdown(result.validation.failures)
        lines.append("")
        lines.append(
            f"**F-A coverage warnings** (`validation.warnings`, fail-open, "
            f"never blocks display, per the S68 close-out lock a "
            f"warning-bearing run cannot score P4 clean): "
            f"{list(result.validation.warnings) if result.validation.warnings else 'none'}"
        )
        lines.append("")

        lines.append("## reading_text (verbatim, final -- includes decline block + disclaimer, tags STRIPPED)")
        lines.append("")
        lines.append("```")
        lines.append(result.reading_text)
        lines.append("```")
        lines.append("")

        # S68 F-C A1: the raw tagged draft -- every sentence's trailing
        # [OBS]/[chunk_id] anchor tag(s) intact. This is what pass 4's
        # claim ledger builds from (self-declared anchors), NOT a
        # reconstruction probe -- confirming this field is populated and
        # tag-bearing is exactly what this probe update exists to check.
        lines.append("## reading_text_tagged (verbatim, A1 raw tagged draft -- anchors intact)")
        lines.append("")
        lines.append("```")
        lines.append(result.reading_text_tagged)
        lines.append("```")
        lines.append("")

        lines.append("## sources (from PalmReadingResult, post-gate)")
        lines.append("")
        for s in result.sources:
            lines.append(f"- {s['book']}, p.{s['page']} (score: {s['score']}) -- feature: {s['feature']}")
        lines.append("")

        # ── Deterministic sanity asserts (fail loudly) ────────────────
        lines.append("## Sanity asserts")
        lines.append("")

        assert_failures: list[str] = []

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

        if not result.validation.passed:
            assert_failures.append(
                "ASSERT FAILED: Ring 1 passed=True on the final draft -- got "
                f"False. Failures: {list(result.validation.failures)}. The "
                "S66 F2c retry is a HARD CAP of 2 calls, no further retries "
                "-- a failing final draft is a real, reportable defect."
            )
        else:
            lines.append("- [x] Ring 1 `passed=True` on the final draft")

        echo_hits = palm_reading._check_exemplar_echo(result.reading_text)
        if echo_hits:
            assert_failures.append(
                f"ASSERT FAILED: no 6-gram exemplar echo in reading_text -- "
                f"got: {echo_hits}"
            )
        else:
            lines.append("- [x] No 6-gram exemplar echo in `reading_text`")

        # S68 NEW: reading_text_tagged must be non-empty and must contain
        # at least one recognized anchor tag -- the tagging CONTRACT
        # itself must be exercised, not just present-but-blank (mirrors
        # _check_tag_completeness's own "anchor contract not exercised"
        # primary guard, checked here independently as a probe-level
        # sanity, not a re-test of that validator).
        if not result.reading_text_tagged or not result.reading_text_tagged.strip():
            assert_failures.append(
                "ASSERT FAILED: reading_text_tagged is empty/whitespace-only "
                "-- the A1 tagging contract was not exercised."
            )
        elif not palm_reading.CHUNK_ANCHOR_TAG_PATTERN.search(result.reading_text_tagged):
            assert_failures.append(
                "ASSERT FAILED: reading_text_tagged contains no recognized "
                "[OBS]/[chunk_id] anchor tag at all."
            )
        else:
            lines.append("- [x] `reading_text_tagged` is populated and contains a recognized anchor tag")

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
            "All 4 sanity asserts PASSED. This is a wiring smoke check "
            "only -- it says nothing about interpretive quality/citation "
            "accuracy (that is Ring 3 pass 4's job, on fresh uploads, "
            "human-scored). No product code was touched or fixed by this "
            "script."
        )

        _REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")
        print(f"Report written to {_REPORT_PATH}")
        print(
            f"retry_used={result.retry_used} passed={result.validation.passed} "
            f"warnings={list(result.validation.warnings)} "
            f"supported={len(result.supported_features)} "
            f"unsupported={len(result.unsupported_features)}"
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
