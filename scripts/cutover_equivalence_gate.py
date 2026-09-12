"""
scripts/cutover_equivalence_gate.py

MEASUREMENT HARNESS ONLY -- no production file is imported for mutation, no
source commit follows this run, no binding is created. Report goes to
diagnostics/latest_run.md (overwrite).

Pre-cutover EQUIVALENCE GATE for S104 Step 5 (the atomic rule migration +
old-field retirement, not yet authored). Proves -- or disproves -- that the
NEW path (CONTACTS parse -> contact_mapper.map_contact -> targets) can
reproduce the OLD path (typed-RELATIONSHIP parse -> targets) for the 3
rules the cutover would migrate: H_028, L_026, FT_016.

The standing rule-diff fixture used in Steps 1-4's verifications (['H_002',
'H_004']) does NOT exercise any of these 3 rules -- this gate builds fresh,
explicit synthetic observation fixtures that actually fire each one via the
OLD path first (fixture correctness is itself checked before anything else
is compared), then builds the CONTACTS-equivalent raw text for the NEW path
and assembles a `targets` dict from it using the SAME logic a future
Step 5b producer would need (written here, in the gate, as a proof -- nOT
committed anywhere as production code).
"""

from __future__ import annotations

import base64
import sys
import time
import traceback
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT))

from agent.interpretive.observation_extractor import (  # noqa: E402
    extract_relations, _RELATION_CARDINALITY,
)
from agent.interpretive.contact_mapper import map_contact  # noqa: E402
from agent.interpretive.palm_rules_table import load_rule_set, match  # noqa: E402
from agent.palm_processor import describe_palm_image  # noqa: E402
from openai import OpenAI  # noqa: E402

REPORT_PATH = _REPO_ROOT / "diagnostics" / "latest_run.md"

IMAGE_PATH = _REPO_ROOT / "data" / "test_images" / "palm_left_test.jpg"
HAND = "left"
N = 3

_RULES = load_rule_set()
_TARGET_RULE_IDS = {"H_028", "L_026", "FT_016"}


# ─── NEW-path assembly: contacts -> contact_mapper -> targets ────────────
# This is a PREVIEW of what Step 5b's producer-side wiring would need to
# do -- written here to prove it's possible/correct, NOT wired into
# production anywhere. Mirrors _store_relationship's own cardinality
# handling (set for multi, scalar for single) via the SAME registry-
# derived _RELATION_CARDINALITY dict, so this assembly can't silently
# diverge from the OLD path's own accumulation rule.
def assemble_targets_from_contacts(contacts: dict) -> tuple[dict, list[dict]]:
    """Returns (targets, quarantined) -- quarantined is every contact whose
    map_contact() call returned token=None, with its reason, for reporting.

    KNOWN, DELIBERATE GAP (not a bug in this assembly, a property of the
    CONTACTS schema itself): unlike RELATIONSHIP's optional "at <mount>"
    clause, the CONTACTS field (Step 2) has NO location/mount field at all
    -- only <target>/<verb>/<position>/<clarity>. <position> is a
    different axis (WHERE ALONG THIS LINE) from RELATIONSHIP's location
    (WHICH MOUNT the crossing happens at). This assembly therefore can
    NEVER populate a `{token}__location` entry -- there is no data to put
    there. Any rule whose antecedent carries a `location` (FT_016) is
    consequently unreachable via this NEW path as currently specified.
    This is reported as a finding, not silently patched around."""
    targets: dict[str, dict[str, object]] = {}
    quarantined: list[dict] = []
    for feature, items in contacts.items():
        for item in items:
            mapped = map_contact(item)
            if mapped["token"] is None:
                quarantined.append({"feature": feature, **mapped})
                continue
            token = mapped["token"]
            target = mapped["target"]
            bucket = targets.setdefault(feature, {})
            if _RELATION_CARDINALITY.get(token) == "multi":
                bucket.setdefault(token, set()).add(target)
            else:
                if token in bucket and bucket[token] != target:
                    continue  # first-seen wins, mirrors _store_relationship
                bucket[token] = target
    return targets, quarantined


def _jsonify_targets(targets: dict) -> dict:
    """Sets aren't directly comparable for a stable report string -- sort
    them into lists for display/equality-checking purposes only."""
    out = {}
    for feature, attrs in targets.items():
        out[feature] = {}
        for attr, val in attrs.items():
            if isinstance(val, set):
                out[feature][attr] = sorted(val)
            elif isinstance(val, dict):
                out[feature][attr] = dict(val)
            else:
                out[feature][attr] = val
    return out


def _targets_equal(a: dict, b: dict) -> bool:
    return _jsonify_targets(a) == _jsonify_targets(b)


def _fired_ids(targets: dict) -> list[str]:
    fired = match({}, {}, _RULES, targets=targets)
    return sorted(r.rule_id for r in fired)


# ─── 3 synthetic fixtures, OLD raw text + NEW (CONTACTS-equivalent) raw text ──
FIXTURES = {
    "FIX_H028": {
        "rule_id": "H_028",
        "old_raw": (
            "HEAD LINE: deep\n"
            "  RELATIONSHIP: joins_at_origin Line of Life\n"
        ),
        "new_raw": (
            "HEAD LINE: deep\n"
            "  CONTACTS: Line of Life | joins | at start | clear\n"
        ),
    },
    "FIX_L026": {
        "rule_id": "L_026",
        "old_raw": (
            "HEAD LINE: deep\n"
            "  RELATIONSHIP: joins_at_origin Line of Heart\n"
            "  RELATIONSHIP: joins_at_origin Line of Life\n"
            "HEART LINE: deep\n"
            "  RELATIONSHIP: joins_at_origin Line of Life\n"
        ),
        "new_raw": (
            "HEAD LINE: deep\n"
            "  CONTACTS: Line of Heart | joins | at start | clear\n"
            "  CONTACTS: Line of Life | joins | at start | clear\n"
            "HEART LINE: deep\n"
            "  CONTACTS: Line of Life | joins | at start | clear\n"
        ),
    },
    "FIX_FT016": {
        "rule_id": "FT_016",
        "old_raw": (
            "FATE LINE: deep\n"
            "  RELATIONSHIP: meets Line of Heart at Mount of Jupiter\n"
        ),
        "new_raw": (
            "FATE LINE: deep\n"
            "  CONTACTS: Line of Heart | merges | mid-course | clear\n"
        ),
    },
}


def _call_vision(system_prompt: str, image_bytes: bytes, mime: str, *, run_idx: int) -> str | None:
    client = OpenAI()
    b64 = base64.b64encode(image_bytes).decode("utf-8")
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": [
                    {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}},
                ]},
            ],
            max_tokens=600,
            temperature=0.0,
        )
        return response.choices[0].message.content
    except Exception as exc:  # noqa: BLE001 -- one failed run must not abort the gate
        print(f"  [ERROR] run={run_idx}: {exc}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        return None


def main() -> None:
    t0 = time.time()
    lines_out: list[str] = []
    lines_out.append("# Cutover Equivalence Gate -- S104 Step 5a (pre-cutover, no binding)\n")
    lines_out.append(f"**Date:** {time.strftime('%Y-%m-%d %H:%M:%S')}  ")
    lines_out.append(
        "**Scope:** measurement harness only. No production file modified. No "
        "commit follows this run. NO binding is created -- `assemble_targets_"
        "from_contacts()` is a PREVIEW of what Step 5b would need to write, "
        "defined here in the gate script only.\n"
    )

    # ── per-fixture equivalence ─────────────────────────────────────
    lines_out.append("## Per-fixture equivalence\n")
    fixture_results = {}
    for name, spec in FIXTURES.items():
        rule_id = spec["rule_id"]
        old_parsed = extract_relations(spec["old_raw"])
        old_targets = old_parsed["targets"]
        old_fired = _fired_ids(old_targets)
        old_fixture_valid = rule_id in old_fired

        new_parsed = extract_relations(spec["new_raw"])
        new_targets, quarantined = assemble_targets_from_contacts(new_parsed["contacts"])
        new_fired = _fired_ids(new_targets)

        targets_match = _targets_equal(old_targets, new_targets)
        fired_match = old_fired == new_fired
        new_fixture_fires = rule_id in new_fired

        status = "PASS" if (old_fixture_valid and targets_match and fired_match and new_fixture_fires) else "FAIL"

        fixture_results[name] = {
            "rule_id": rule_id,
            "old_targets": _jsonify_targets(old_targets),
            "new_targets": _jsonify_targets(new_targets),
            "old_fired": old_fired,
            "new_fired": new_fired,
            "old_fixture_valid": old_fixture_valid,
            "targets_match": targets_match,
            "fired_match": fired_match,
            "new_fixture_fires": new_fixture_fires,
            "quarantined": quarantined,
            "status": status,
        }

        lines_out.append(f"### {name} (targets rule: `{rule_id}`)\n")
        lines_out.append(f"- Fixture validity (OLD path fires `{rule_id}`): **{old_fixture_valid}**")
        lines_out.append(f"- OLD targets: `{fixture_results[name]['old_targets']}`")
        lines_out.append(f"- NEW targets: `{fixture_results[name]['new_targets']}`")
        lines_out.append(f"- Targets-structure parity: **{targets_match}**")
        lines_out.append(f"- OLD fired-ids: `{old_fired}`")
        lines_out.append(f"- NEW fired-ids: `{new_fired}`")
        lines_out.append(f"- Fired-set parity: **{fired_match}**")
        lines_out.append(f"- NEW path fires `{rule_id}`: **{new_fixture_fires}**")
        if quarantined:
            lines_out.append(f"- Quarantined on NEW path: {quarantined}")
        lines_out.append(f"\n**{name} STATUS: {status}**\n")

    # ── live arm ─────────────────────────────────────────────────────
    lines_out.append("## Live arm (palm_left_test, N=3)\n")
    if not IMAGE_PATH.is_file():
        raise FileNotFoundError(f"cutover_equivalence_gate: missing image -> {IMAGE_PATH}")
    image_bytes = IMAGE_PATH.read_bytes()
    mime = "image/png" if image_bytes[:8].startswith(b"\x89PNG") else "image/jpeg"
    prompt = None
    import agent.palm_processor as pp
    prompt = pp._build_description_system_prompt(HAND)

    old_h028_hits = 0
    new_h028_hits = 0
    all_verb_mappings: list[dict] = []
    per_run_rows = []

    for run_idx in range(N):
        raw = _call_vision(prompt, image_bytes, mime, run_idx=run_idx)
        if raw is None:
            per_run_rows.append({"run": run_idx, "error": True})
            continue
        parsed = extract_relations(raw)
        old_targets_run = parsed["targets"]
        old_fired_run = _fired_ids(old_targets_run)
        old_hit = "H_028" in old_fired_run
        old_h028_hits += int(old_hit)

        new_targets_run, quarantined_run = assemble_targets_from_contacts(parsed["contacts"])
        new_fired_run = _fired_ids(new_targets_run)
        new_hit = "H_028" in new_fired_run
        new_h028_hits += int(new_hit)

        for feature, items in parsed["contacts"].items():
            for item in items:
                mapped = map_contact(item)
                all_verb_mappings.append({"run": run_idx, "feature": feature, **mapped})

        per_run_rows.append({
            "run": run_idx, "error": False,
            "old_hit": old_hit, "new_hit": new_hit,
            "old_targets": _jsonify_targets(old_targets_run),
            "new_targets": _jsonify_targets(new_targets_run),
            "quarantined": quarantined_run,
        })
        print(f"  run {run_idx + 1}/{N} -> OK (old H_028={old_hit}, new H_028={new_hit})")

    lines_out.append("| Run | OLD path H_028 fires? | NEW path H_028 fires? |")
    lines_out.append("|---|---|---|")
    for row in per_run_rows:
        if row.get("error"):
            lines_out.append(f"| {row['run']} | ERROR | ERROR |")
        else:
            lines_out.append(f"| {row['run']} | {row['old_hit']} | {row['new_hit']} |")

    valid_runs = [r for r in per_run_rows if not r.get("error")]
    lines_out.append(f"\n**OLD path H_028 rate:** {old_h028_hits}/{len(valid_runs)}")
    lines_out.append(f"**NEW path H_028 rate:** {new_h028_hits}/{len(valid_runs)}")
    rate_ok = new_h028_hits >= old_h028_hits

    # mapper coverage on live verbs
    lines_out.append("\n## Mapper coverage on live verbs\n")
    lines_out.append("| Run | Feature | Target | Raw verb | Position | Mapped token | Confidence | Reason |")
    lines_out.append("|---|---|---|---|---|---|---|---|")
    quarantine_hits = []
    for m in all_verb_mappings:
        lines_out.append(
            f"| {m['run']} | {m['feature']} | {m['target']} | {m['raw_verb']!r} | "
            f"{m['position']!r} | {m['token']} | {m['confidence']} | {m['reason']} |"
        )
        if m["token"] is None:
            quarantine_hits.append(m)
    if not all_verb_mappings:
        lines_out.append("| (no contacts captured live) | | | | | | | |")

    lines_out.append(f"\n**Quarantined live verbs:** {len(quarantine_hits)}")
    for q in quarantine_hits:
        lines_out.append(f"  - run {q['run']} {q['feature']} -> target={q['target']!r} verb={q['raw_verb']!r}: {q['reason']}")

    # ── GATE VERDICT ─────────────────────────────────────────────────
    lines_out.append("\n## GATE VERDICT\n")
    all_fixtures_pass = all(r["status"] == "PASS" for r in fixture_results.values())
    zero_unexpected_quarantine = len(quarantine_hits) == 0

    gate_pass = all_fixtures_pass and rate_ok and zero_unexpected_quarantine

    lines_out.append(f"- All 3 fixtures parity-match: **{all_fixtures_pass}**")
    for name, r in fixture_results.items():
        lines_out.append(f"    - {name} ({r['rule_id']}): {r['status']}")
    lines_out.append(f"- Live H_028 NEW rate >= OLD rate: **{rate_ok}** ({new_h028_hits}/{len(valid_runs)} vs {old_h028_hits}/{len(valid_runs)})")
    lines_out.append(f"- Zero unexpected quarantine on live verbs: **{zero_unexpected_quarantine}** ({len(quarantine_hits)} quarantined)")

    lines_out.append(f"\n**GATE: {'PASS' if gate_pass else 'FAIL'}**\n")

    if not gate_pass:
        blocking = []
        for name, r in fixture_results.items():
            if r["status"] == "FAIL":
                if not r["old_fixture_valid"]:
                    blocking.append(f"{name}: fixture itself never fired {r['rule_id']} on the OLD path -- fixture is wrong, not the pipeline.")
                elif not r["targets_match"] or not r["fired_match"] or not r["new_fixture_fires"]:
                    blocking.append(
                        f"{name} ({r['rule_id']}): NEW path does not reproduce OLD path. "
                        + (
                            "Root cause: the CONTACTS schema (Step 2) has NO location/mount "
                            "field -- only <target>/<verb>/<position>/<clarity> -- so "
                            "`{token}__location` can never be populated on the NEW path. "
                            f"{r['rule_id']}'s antecedent requires a `location` "
                            "match, making it structurally unreachable via CONTACTS as "
                            "currently specified, independent of mapper correctness."
                            if name == "FIX_FT016" else
                            f"targets_match={r['targets_match']}, fired_match={r['fired_match']}, "
                            f"new_fires={r['new_fixture_fires']}."
                        )
                    )
        if not rate_ok:
            blocking.append(f"Live H_028 rate regressed on the NEW path ({new_h028_hits}/{len(valid_runs)} vs OLD {old_h028_hits}/{len(valid_runs)}).")
        if not zero_unexpected_quarantine:
            blocking.append(f"{len(quarantine_hits)} live verb(s) quarantined unexpectedly -- see Mapper coverage table.")

        lines_out.append("**Single blocking gap (most severe):**\n")
        # FT_016's location gap, if present, is the architectural one -- surface it first.
        ft016_gap = next((b for b in blocking if b.startswith("FIX_FT016")), None)
        lines_out.append(f"  {ft016_gap or blocking[0]}")
        if len(blocking) > 1:
            lines_out.append("\n  (other blocking items also present, listed above per-fixture/per-check)")

    lines_out.append("\n**Is the cutover (Step 5b) safe to author?**\n")
    if gate_pass:
        lines_out.append("  **YES** -- all equivalence checks passed.")
    else:
        lines_out.append(
            "  **NO.** " + (
                "FT_016 specifically cannot migrate as currently specified: the CONTACTS "
                "field has no location/mount channel, and FT_016's antecedent requires one "
                "(`meets Line of Heart at Mount of Jupiter`). H_028 and L_026 have no "
                "location requirement and may clear independently -- see their own "
                "per-fixture PASS/FAIL above; do not treat this as a blanket rejection of "
                "the whole migration, only of the location-dependent rule(s), unless a "
                "per-fixture FAIL above says otherwise."
                if any(name == "FIX_FT016" and r["status"] == "FAIL" for name, r in fixture_results.items())
                else "See the blocking gap above."
            )
        )

    report_text = "\n".join(lines_out) + "\n"
    REPORT_PATH.write_text(report_text, encoding="utf-8")

    elapsed = time.time() - t0
    print(f"\nDone in {elapsed:.1f}s. Report written to: {REPORT_PATH}")


if __name__ == "__main__":
    main()
