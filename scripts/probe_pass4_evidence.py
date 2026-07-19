"""
scripts/probe_pass4_evidence.py

Ring 3 pass 4 evidence-assembly probe (S68 close-out state, fresh live
dogfood uploads 2026-07-19). Read-only, reconstructs nothing that
matters for the CLAIM LEDGER itself -- per the instructing design, the
ledger is built from SELF-DECLARED anchors in the captured
`reading_text_tagged` field directly (parsed here, not re-derived).
Reconstruction (same pattern as scripts/probe_pass3_chunks.py) is used
ONLY for two things the F5 capture does not otherwise expose:
  1. `ValidationReport.warnings` (F-A coverage) -- `frontend/app.py`'s
     `_capture_dogfood_run()` never writes a "warnings:" line (verified
     by reading the function source, not assumed -- see
     diagnostics/latest_run.md's earlier report this session). Needs
     gated_results + supported_features, which are reconstructed here
     from the captured confirmed descriptions via the same production
     private helpers pass-3's chunk probe used.
  2. Verbatim chunk TEXT for any cited chunk_id the claim ledger needs
     to spot-check faithfulness against (chunk_id/page/score alone,
     already in the "### sources" capture, isn't the doctrine text
     itself).

MEASURE-FIRST GATE (same discipline as probe_pass3_chunks.py): before
trusting ANY reconstructed data, this script asserts its own
reconstructed supported_features/unsupported_features EXACTLY match
each run's captured "### feature_support" section. A mismatch aborts
loudly -- reconstructed evidence is not used if the reconstruction
itself cannot be proven faithful to what generate_palm_reading()
computed live.

Targets the 3 real, human-confirmed, freshly-uploaded RUN blocks from
2026-07-19 (Run A baseline 10:40:50, Run B identical-input regenerate
10:42:48, Run C +HAND_DETAIL 10:43:39) -- NOT the 2 bonus failed-draft
RUN blocks from the same session (10:36:21, 10:37:24 for Run A's first
2 attempts, 10:41:49 for Run B's first attempt), which are separately
useful evidence (real self_help_blacklist fail-closed firings) but have
no displayed reading_text to build a claim ledger from.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agent.interpretive import palm_reading

_LOG_PATH = Path(__file__).resolve().parent.parent / "diagnostics" / "dogfood_capture.md"
_REPORT_PATH = Path(__file__).resolve().parent.parent / "diagnostics" / "ring3_evidence_S68_pass4.md"

_TARGET_RUNS: tuple[tuple[str, str], ...] = (
    ("Run A (baseline)", "2026-07-19T10:40:50.482046"),
    ("Run B (identical-input regenerate)", "2026-07-19T10:42:48.947566"),
    ("Run C (+HAND_DETAIL)", "2026-07-19T10:43:39.978164"),
)


class _AbortProbe(Exception):
    pass


def _extract_run_block(full_text: str, timestamp: str) -> str:
    marker = f"## RUN {timestamp}"
    start = full_text.find(marker)
    if start == -1:
        raise _AbortProbe(f"RUN block not found for timestamp {timestamp!r}")
    next_marker = full_text.find("\n## RUN ", start + 1)
    return full_text[start:next_marker] if next_marker != -1 else full_text[start:]


def _extract_section(block: str, header: str, next_headers: tuple[str, ...]) -> str:
    start = block.find(header)
    if start == -1:
        return ""
    start += len(header)
    end = len(block)
    for nh in next_headers:
        idx = block.find(nh, start)
        if idx != -1:
            end = min(end, idx)
    return block[start:end].strip("\n")


def _parse_confirmed_descriptions(block: str) -> tuple[str | None, str | None, str | None]:
    desc_section = _extract_section(
        block, "### Confirmed descriptions\n", ("\n### reading_text",)
    )
    left = right = hand_detail = None
    if "#### LEFT" in desc_section:
        left = _extract_section(desc_section, "#### LEFT\n", ("#### RIGHT", "#### HAND_DETAIL"))
    if "#### RIGHT" in desc_section:
        right = _extract_section(desc_section, "#### RIGHT\n", ("#### HAND_DETAIL",))
    if "#### HAND_DETAIL" in desc_section:
        hand_detail = desc_section[desc_section.find("#### HAND_DETAIL\n") + len("#### HAND_DETAIL\n"):].strip("\n")
    return left, right, hand_detail


def _parse_tagged_text(block: str) -> str:
    return _extract_section(block, "### READING (TAGGED)\n", ("\n### sources",))


def _parse_feature_support(block: str) -> tuple[tuple[str, ...], tuple[str, ...]]:
    section = _extract_section(block, "### feature_support\n", ("\n### ring1_validation",))
    supported_line = next(l for l in section.splitlines() if l.startswith("supported_features:"))
    unsupported_line = next(l for l in section.splitlines() if l.startswith("unsupported_features:"))
    supported = eval(supported_line.split(":", 1)[1].strip())
    unsupported = eval(unsupported_line.split(":", 1)[1].strip())
    return supported, unsupported


# ─── Claim ledger: positional split of reading_text_tagged on ─────────
# ─── CHUNK_ANCHOR_TAG_PATTERN matches -- SELF-DECLARED anchors only, ───
# ─── no reconstruction involved in this function.                    ───

def _build_claim_ledger(tagged_text: str) -> list[tuple[str, list[str]]]:
    """Returns [(clause_text, [tag_tokens]), ...] in document order.
    A "clause" here is the text between the end of one tag and the end
    of the next (i.e. one sentence + its own trailing tag(s), stripped
    of the tag markup itself) -- same segmentation V-1's own positional
    logic relies on, applied here for reporting, not re-validation."""
    ledger: list[tuple[str, list[str]]] = []
    pos = 0
    tags_buffer: list[str] = []
    clause_start = 0
    for m in palm_reading.CHUNK_ANCHOR_TAG_PATTERN.finditer(tagged_text):
        token = m.group(0)[1:-1]
        # Adjacent tags (e.g. "[OBS][cheiro..._c1]" or two chunk ids back
        # to back) belong to the SAME clause -- only flush the clause
        # once we hit a tag that is NOT immediately adjacent to the
        # previous one.
        if tags_buffer and m.start() != pos:
            clause_text = tagged_text[clause_start:pos].strip()
            if clause_text:
                ledger.append((clause_text, tags_buffer))
            tags_buffer = []
            clause_start = pos
        tags_buffer.append(token)
        pos = m.end()
    if tags_buffer:
        clause_text = tagged_text[clause_start:pos]
        # strip trailing tag markup from the clause text itself
        clause_text = palm_reading.CHUNK_ANCHOR_TAG_PATTERN.sub("", clause_text).strip()
        ledger.append((clause_text, tags_buffer))
    return ledger


def main() -> None:
    if not _LOG_PATH.exists():
        raise _AbortProbe(f"dogfood log not found: {_LOG_PATH}")
    full_text = _LOG_PATH.read_text(encoding="utf-8")

    report_lines: list[str] = []
    report_lines.append("# Ring 3 pass 4 evidence -- claim ledger + coverage reconstruction")
    report_lines.append("")
    report_lines.append(
        "Source: `diagnostics/dogfood_capture.md`, 3 fresh live 2026-07-19 "
        "RUN blocks (real photo uploads, human-confirmed descriptions). "
        "Claim ledger below is built from SELF-DECLARED anchors in each "
        "run's captured `reading_text_tagged` -- direct positional parse, "
        "NOT a reconstruction. Coverage warnings and per-chunk verbatim "
        "text ARE reconstructed (gated_results/supported_features are not "
        "otherwise captured), gated behind a measure-first reconstruction-"
        "fidelity assert per run (see each run's own gate line below)."
    )
    report_lines.append("")

    for run_label, timestamp in _TARGET_RUNS:
        report_lines.append(f"## {run_label} -- `{timestamp}`")
        report_lines.append("")

        block = _extract_run_block(full_text, timestamp)
        left, right, hand_detail = _parse_confirmed_descriptions(block)
        tagged_text = _parse_tagged_text(block)
        captured_supported, captured_unsupported = _parse_feature_support(block)

        # ── Reconstruction (gated_results/supported/unsupported) ────
        left_fields = palm_reading._parse_fields(left) if left else {}
        right_fields = palm_reading._parse_fields(right) if right else {}
        hd_fields = palm_reading._parse_bullet_fields(hand_detail) if hand_detail else {}
        texts_by_feature = palm_reading._gather_feature_texts(left_fields, right_fields, hd_fields)
        per_feature_results, failed_features = palm_reading._retrieve_per_feature(
            left_fields, right_fields, hd_fields
        )
        gated_results, recon_supported, recon_unsupported = palm_reading._apply_support_gate(
            per_feature_results, texts_by_feature
        )

        # ── MEASURE-FIRST GATE ───────────────────────────────────────
        if recon_supported != captured_supported or recon_unsupported != captured_unsupported:
            report_lines.append(
                "**RECONSTRUCTION FIDELITY GATE FAILED** -- reconstructed "
                f"supported_features={recon_supported!r} / "
                f"unsupported_features={recon_unsupported!r} does NOT match "
                f"the captured feature_support "
                f"supported_features={captured_supported!r} / "
                f"unsupported_features={captured_unsupported!r}. "
                "Coverage warnings and chunk-text lookups below are "
                "UNTRUSTED for this run -- ChromaDB embedding retrieval is "
                "not guaranteed byte-stable across separate calls, and this "
                "run's reconstruction diverged. Reporting the divergence, "
                "not silently using unverified data."
            )
            report_lines.append("")
            recon_reliable = False
        else:
            report_lines.append(
                f"Reconstruction fidelity gate PASSED -- reconstructed "
                f"supported_features/unsupported_features exactly match "
                f"the capture. Coverage warnings and chunk-text lookups "
                f"below are trustworthy for this run."
            )
            report_lines.append("")
            recon_reliable = True

        if recon_reliable:
            coverage_warnings = palm_reading._check_feature_coverage(
                tagged_text, gated_results, recon_supported
            )
            valid_chunk_ids = frozenset(
                c["chunk_id"] for chunks in gated_results.values() for c in chunks
            )
            report_lines.append(
                f"**F-A coverage warnings (reconstructed)**: "
                f"{coverage_warnings if coverage_warnings else 'none'}"
            )
            report_lines.append(
                f"**valid_chunk_ids count (V-2 union, reconstructed)**: {len(valid_chunk_ids)}"
            )
            report_lines.append("")

            # F-B live-data check: is markings/other features genuinely
            # absent per BOTH hands' MARKS text, and if so, why did it
            # still land in supported_features?
            marks_texts = texts_by_feature.get("markings/other features", [])
            report_lines.append("**F-B absence-classification check on this run's MARKS texts**:")
            for t in marks_texts:
                is_abs = palm_reading._is_absence(t, "markings/other features")
                report_lines.append(f"- `_is_absence(feature='markings/other features')` = **{is_abs}** for: {t!r}")
            report_lines.append("")

        # ── Claim ledger (self-declared, no reconstruction) ─────────
        ledger = _build_claim_ledger(tagged_text)
        report_lines.append(f"### Claim ledger ({len(ledger)} tagged clauses, self-declared anchors)")
        report_lines.append("")
        report_lines.append("| # | Clause | Anchor(s) |")
        report_lines.append("|---|---|---|")
        chunk_id_lookup: dict[str, dict] = {
            c["chunk_id"]: c for chunks in gated_results.values() for c in chunks
        } if recon_reliable else {}
        for i, (clause, tags) in enumerate(ledger, start=1):
            anchor_display = ", ".join(tags)
            clause_display = clause.replace("|", "\\|").replace("\n", " ")
            report_lines.append(f"| {i} | {clause_display} | {anchor_display} |")
        report_lines.append("")

        if recon_reliable:
            report_lines.append("### Verbatim chunk text for every cited chunk_id (not [OBS])")
            report_lines.append("")
            cited_ids = sorted({
                tag for _, tags in ledger for tag in tags if tag != "OBS"
            })
            for cid in cited_ids:
                c = chunk_id_lookup.get(cid)
                if c is None:
                    report_lines.append(f"- `{cid}`: **NOT FOUND in reconstructed gated_results** (would be an anchor-legality concern, but this run's `ring1_failures` reported none -- reconstruction may differ from the live retrieval slightly; flagged, not asserted).")
                else:
                    report_lines.append(f"- `{cid}` (p.{c['page_ref']}, score {c['score']}, feature={next(f for f, chunks in gated_results.items() if c in chunks)}):")
                    report_lines.append(f"  > {c['text']}")
            report_lines.append("")

        report_lines.append("---")
        report_lines.append("")

    _REPORT_PATH.write_text("\n".join(report_lines), encoding="utf-8")
    print(f"Report written to {_REPORT_PATH}")


if __name__ == "__main__":
    try:
        main()
    except _AbortProbe as exc:
        print(f"ABORT: {exc}")
        sys.exit(1)
