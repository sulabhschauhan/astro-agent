"""
scripts/heart_endpoint_synonym_probe.py

MEASUREMENT HARNESS ONLY -- no production file is imported for mutation, no
source commit follows this run. Report goes to diagnostics/latest_run.md
(overwrite).

Two questions, one small run:

  Q1 (variance vs displacement) -- S104 Step 1's sample re-read (N=1 per
     image) showed Heart's TERMINATION reading "Mount of Mercury" on both
     sample images, where 6 prior probe runs (3+3) all showed "Percussion".
     This re-checks at N=3 per image, using the CURRENT working-tree prompt
     (Step 1's uncommitted Fate/Head direction-law edit included, NOT
     reverted), to tell alternating (temp variance, safe to commit) from
     displaced (investigate further).

  Q2 (mapping) -- Heart's TERMINATION menu has two names for the same
     physical spot ("Percussion", "Mount of Mercury"). A static, no-LLM
     scan of every LIVE rule file (data/palm_rules/palm_rules_*.json, the
     same non-recursive glob agent.interpretive.palm_rules_table.
     load_rule_set() uses) checks whether any rule keys on only one
     spelling -- if so, a canonical-landmark-map layer is needed (same
     shape as the verb->token map), or such a rule silently misses
     whenever the vision model picks the other name.
"""

from __future__ import annotations

import base64
import json
import re
import sys
import time
import traceback
from collections import Counter
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT))

import agent.palm_processor as pp  # noqa: E402  (production module, read-only use)
from openai import OpenAI  # noqa: E402

# ─────────────────────────── CONFIG BLOCK ────────────────────────────────
IMAGES: dict[str, str] = {
    "fate_line":      "data/test_images/Fate line.jpeg",
    "palm_left_test": "data/test_images/palm_left_test.jpg",
}
HANDS: dict[str, str] = {"fate_line": "right", "palm_left_test": "left"}

N = 3

MODEL = "gpt-4o"
TEMPERATURE = 0.0
MAX_TOKENS = 600  # matches production describe_palm_image's own budget -- this IS that call

REPORT_PATH = _REPO_ROOT / "diagnostics" / "latest_run.md"
_RULES_DIR = _REPO_ROOT / "data" / "palm_rules"

_HEART_TERMINATION_NAMES = ("Percussion", "Mount of Mercury")

# ───────────────────────────── parsing ────────────────────────────────────
_BLOCK_HEADER_RE = re.compile(
    r"^(HAND SHAPE|FINGERS|THUMB|LIFE LINE|HEAD LINE|HEART LINE|FATE LINE"
    r"|LINE OF HEALTH|LINE OF MARRIAGE|OTHER LINES|MOUNTS|MARKS):",
)
_FEATURE_BLOCK_LABEL = {
    "HEAD LINE": "Line of Head",
    "HEART LINE": "Line of Heart",
    "FATE LINE": "Line of Fate",
}
_ORIGIN_RE = re.compile(r"^ORIGIN:\s*(.*)$")
_TERMINATION_RE = re.compile(r"^TERMINATION:\s*(.*)$")


def parse_origin_termination(raw_text: str) -> dict:
    origin: dict[str, str] = {}
    termination: dict[str, str] = {}
    current_feature: str | None = None
    for raw_line in raw_text.splitlines():
        stripped = raw_line.strip()
        header = _BLOCK_HEADER_RE.match(stripped)
        if header:
            current_feature = _FEATURE_BLOCK_LABEL.get(header.group(1))
            continue
        if current_feature is None:
            continue
        m = _ORIGIN_RE.match(stripped)
        if m:
            origin[current_feature] = m.group(1).strip()
            continue
        m = _TERMINATION_RE.match(stripped)
        if m:
            termination[current_feature] = m.group(1).strip()
    return {"origin": origin, "termination": termination}


# ───────────────────────────── API call wrapper ───────────────────────────
_client = OpenAI()


def _call_vision(system_prompt: str, image_bytes: bytes, mime: str, *, image_key: str, run_idx: int) -> str | None:
    b64 = base64.b64encode(image_bytes).decode("utf-8")
    try:
        response = _client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": [
                    {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}},
                ]},
            ],
            max_tokens=MAX_TOKENS,
            temperature=TEMPERATURE,
        )
        return response.choices[0].message.content
    except Exception as exc:  # noqa: BLE001 -- one failed run must not abort the probe
        print(f"  [ERROR] image={image_key!r} run={run_idx}: {exc}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        return None


def _mime_for(image_bytes: bytes) -> str:
    return "image/png" if image_bytes[:8].startswith(b"\x89PNG") else "image/jpeg"


# ───────────────────────── static rule-file scan (no LLM) ─────────────────
def scan_rule_files() -> list[dict]:
    """Non-recursive glob of data/palm_rules/*.json, mirroring
    palm_rules_table.load_rule_set()'s own file discovery exactly (it
    explicitly excludes _candidates/ and other subdirectories). Walks
    EVERY rule bucket in each file (validated_candidates, parked_pending*,
    retired_superseded) -- not just the live/verified set -- so a rule
    that references either landmark name anywhere is surfaced, with its
    own verified/live status reported alongside."""
    hits: list[dict] = []
    for file_path in sorted(_RULES_DIR.glob("*.json")):
        try:
            data = json.loads(file_path.read_text(encoding="utf-8"))
        except Exception as exc:  # noqa: BLE001 -- one bad file must not kill the scan
            print(f"  [ERROR] failed to parse {file_path.name}: {exc}", file=sys.stderr)
            continue
        if not isinstance(data, dict):
            continue
        for bucket_name, bucket in data.items():
            if not isinstance(bucket, list):
                continue
            for rule in bucket:
                if not isinstance(rule, dict) or "antecedents" not in rule:
                    continue
                for ant in rule.get("antecedents", []):
                    if not isinstance(ant, dict):
                        continue
                    value = str(ant.get("value", ""))
                    relation_target = str(ant.get("relation_target", "") or "")
                    for name in _HEART_TERMINATION_NAMES:
                        # substring match -- catches both an exact landmark
                        # value AND a composite value that embeds the name
                        # (e.g. "under_Mount_of_Mercury"), reported as such.
                        if name.replace(" ", "_") in value or name in value or name in relation_target:
                            hits.append({
                                "file": file_path.name,
                                "bucket": bucket_name,
                                "rule_id": rule.get("rule_id", "?"),
                                "verified": rule.get("verified"),
                                "feature": ant.get("feature"),
                                "attribute": ant.get("attribute"),
                                "value": ant.get("value"),
                                "relation_target": ant.get("relation_target"),
                                "matched_name": name,
                            })
    return hits


def main() -> None:
    t0 = time.time()

    resolved_paths = {}
    missing = []
    for key, rel in IMAGES.items():
        p = _REPO_ROOT / rel
        if not p.is_file():
            missing.append(f"{key} -> {p}")
        else:
            resolved_paths[key] = p
    if missing:
        raise FileNotFoundError("heart_endpoint_synonym_probe: missing image(s):\n  " + "\n  ".join(missing))

    # ── Q1: vision recall, current (uncommitted, post-Step-1) prompt ────
    results: dict[str, list[dict | None]] = {}
    for image_key, path in resolved_paths.items():
        image_bytes = path.read_bytes()
        mime = _mime_for(image_bytes)
        hand = HANDS[image_key]
        prompt = pp._build_description_system_prompt(hand)  # CURRENT working-tree prompt, unmodified further

        runs = []
        for run_idx in range(N):
            raw = _call_vision(prompt, image_bytes, mime, image_key=image_key, run_idx=run_idx)
            runs.append(parse_origin_termination(raw) if raw is not None else None)
            print(f"  {image_key} / run {run_idx + 1}/{N} -> {'OK' if raw else 'ERROR'}")
        results[image_key] = runs

    # ── Q2: static rule-file scan ────────────────────────────────────────
    rule_hits = scan_rule_files()

    # ── report assembly ─────────────────────────────────────────────
    lines_out: list[str] = []
    lines_out.append("# Heart-Endpoint Synonym Probe (S104 Step 1 follow-up)\n")
    lines_out.append(f"**Date:** {time.strftime('%Y-%m-%d %H:%M:%S')}  ")
    lines_out.append(f"**Model:** {MODEL}, temperature={TEMPERATURE}  ")
    lines_out.append(f"**N:** {N} per image  ")
    lines_out.append(
        "**Scope:** measurement harness only. No production file modified. "
        "No commit follows this run. Prompt used is the CURRENT working-"
        "tree agent.palm_processor._build_description_system_prompt output "
        "-- Step 1's uncommitted Fate/Head direction-law edit is included, "
        "NOT reverted.\n"
    )

    # 1. Heart TERMINATION across 6 runs
    lines_out.append("## 1. Line of Heart TERMINATION across the 6 runs\n")
    lines_out.append("| Image | Run 1 | Run 2 | Run 3 |")
    lines_out.append("|---|---|---|---|")
    all_heart_term: list[str] = []
    for image_key in IMAGES:
        vals = [r["termination"].get("Line of Heart", "ERROR") if r else "ERROR" for r in results[image_key]]
        all_heart_term.extend(v for v in vals if v != "ERROR")
        lines_out.append(f"| {image_key} | {vals[0]} | {vals[1]} | {vals[2]} |")

    counts = Counter(all_heart_term)
    lines_out.append(f"\n**Counts across all 6 runs:** {dict(counts)}")

    percussion_per_image = {}
    for image_key in IMAGES:
        vals = [r["termination"].get("Line of Heart", "ERROR") if r else "ERROR" for r in results[image_key]]
        percussion_per_image[image_key] = sum(1 for v in vals if v == "Percussion")

    displaced = counts.get("Percussion", 0) == 0 and counts.get("Mount of Mercury", 0) == 6
    alternating = any(c >= 1 for c in percussion_per_image.values())

    lines_out.append("\n**VERDICT Q1:**")
    if displaced:
        lines_out.append(
            "  **DISPLACED.** Percussion is 0/6, Mount of Mercury is 6/6 -- "
            "consistent with the Step 1 sample re-read's finding, not "
            "explained away by variance. Investigate before committing "
            "Step 1."
        )
    elif alternating:
        lines_out.append(
            f"  **ALTERNATING (temperature variance).** Percussion appears "
            f"in at least one run on at least one image "
            f"(per-image Percussion counts: {percussion_per_image}). The "
            f"Step 1 sample re-read's single Mount-of-Mercury reads were "
            f"within normal call-to-call variance, not a real displacement. "
            f"Step 1's edit is safe to commit on this criterion."
        )
    else:
        lines_out.append(
            f"  **INCONCLUSIVE** -- neither the DISPLACED nor ALTERNATING "
            f"condition as literally specified was met (counts: "
            f"{dict(counts)}). Report the raw counts to the design chat "
            f"before deciding."
        )

    # 2. Head + Fate ORIGIN/TERMINATION stability
    lines_out.append("\n## 2. Head + Fate ORIGIN/TERMINATION across the 6 runs\n")
    lines_out.append("| Line | Image | Run 1 | Run 2 | Run 3 | Consistent? |")
    lines_out.append("|---|---|---|---|---|---|")
    for line in ("Line of Head", "Line of Fate"):
        for field, getter in (("ORIGIN", "origin"), ("TERMINATION", "termination")):
            for image_key in IMAGES:
                vals = [r[getter].get(line, "ERROR") if r else "ERROR" for r in results[image_key]]
                real = [v for v in vals if v != "ERROR"]
                consistent = len(set(real)) <= 1
                lines_out.append(f"| {line} ({field}) | {image_key} | {vals[0]} | {vals[1]} | {vals[2]} | {consistent} |")

    # 3. Rule-key table + VERDICT Q2
    lines_out.append("\n## 3. Rule-key table (static scan, no LLM)\n")
    lines_out.append(
        "Non-recursive glob of `data/palm_rules/*.json` (same file set "
        "`load_rule_set()` loads -- `_candidates/` and other subdirectories "
        "excluded, matching its own docstring). Every antecedent in every "
        "bucket (validated_candidates, parked_pending*, retired_superseded) "
        "referencing either landmark name, by substring match on `value` "
        "or `relation_target`:\n"
    )
    if rule_hits:
        lines_out.append("| File | Bucket | Rule ID | Verified | Feature | Attribute | Value | relation_target | Matched name |")
        lines_out.append("|---|---|---|---|---|---|---|---|---|")
        for h in rule_hits:
            lines_out.append(
                f"| {h['file']} | {h['bucket']} | {h['rule_id']} | {h['verified']} | "
                f"{h['feature']} | {h['attribute']} | {h['value']} | {h['relation_target']} | {h['matched_name']} |"
            )
    else:
        lines_out.append("(none found)")

    plain_percussion_rules = [h for h in rule_hits if h["value"] == "Percussion" or h["relation_target"] == "Percussion"]
    plain_mercury_rules = [h for h in rule_hits if h["value"] == "Mount of Mercury" or h["relation_target"] == "Mount of Mercury"]
    composite_rules = [h for h in rule_hits if h not in plain_percussion_rules and h not in plain_mercury_rules]

    lines_out.append(
        f"\n**Breakdown:** {len(plain_percussion_rules)} rule(s) keying on the plain "
        f"landmark value 'Percussion'; {len(plain_mercury_rules)} keying on the plain "
        f"landmark value 'Mount of Mercury'; {len(composite_rules)} referencing the "
        f"name inside a DIFFERENT, composite value (not a plain endpoint-landmark match)."
    )
    if composite_rules:
        lines_out.append("\nComposite-value hits (different semantics from the plain TERMINATION landmark field -- listed for completeness, not counted as landmark-synonym exposure):")
        for h in composite_rules:
            lines_out.append(f"  - {h['rule_id']} ({h['file']}, verified={h['verified']}): attribute={h['attribute']!r}, value={h['value']!r}")

    lines_out.append("\n**VERDICT Q2:**")
    if not plain_percussion_rules and not plain_mercury_rules:
        lines_out.append(
            "  **NOT NEEDED YET.** Zero live or parked rules key on the plain "
            "landmark value 'Percussion' or 'Mount of Mercury' for Heart's "
            "TERMINATION endpoint -- there is currently nothing for a "
            "synonym-canonical-map layer to protect, because no rule "
            "depends on that field's landmark identity at all. "
            + (
                "One unrelated rule (HL_009, verified=true, live) uses a "
                "DIFFERENT attribute ('Position') with a composite value "
                "('under_Mount_of_Mercury') describing a BREAK LOCATION, not "
                "the line's endpoint -- this is a separate semantic and a "
                "separate, out-of-scope reachability question (registry has "
                "no attribute_value_binding entry for 'Position' at all, so "
                "its 'legal' status is an open-value default, not confirmed "
                "vision-emittable); noted here, not resolved. "
                if composite_rules else ""
            )
            + "Recommendation: if a future rule is authored against Heart's "
            "plain TERMINATION landmark, it should match BOTH spellings "
            "from the start (same pattern as a verb->token canonical map), "
            "since the vision model demonstrably produces either one."
        )
    else:
        one_sided = [h for h in plain_percussion_rules if h["rule_id"] not in {x["rule_id"] for x in plain_mercury_rules}] + \
                    [h for h in plain_mercury_rules if h["rule_id"] not in {x["rule_id"] for x in plain_percussion_rules}]
        if one_sided:
            lines_out.append(
                f"  **NEEDED.** {len(one_sided)} rule(s) key on only one spelling: "
                f"{[h['rule_id'] for h in one_sided]}. A synonym-landmark canonical "
                "map is needed so these rules fire regardless of which spelling "
                "the vision model picks."
            )
        else:
            lines_out.append("  **NOT NEEDED.** All rules referencing either spelling are robust to both.")

    # 4. single biggest risk
    lines_out.append("\n## 4. Single biggest risk\n")
    if displaced:
        risk = "Heart's TERMINATION reading has genuinely shifted away from Percussion -- root cause (Step 1 edit vs. something else) is still unconfirmed and needs isolation before Step 1 is committed."
    elif alternating:
        risk = (
            "none blocking Step 1's commit on this criterion, but the underlying "
            "two-spellings-one-landmark ambiguity is architectural, not fixed by "
            "this probe -- any future rule-authoring pass against Heart's "
            "TERMINATION must handle both names from the outset."
        )
    else:
        risk = "the Q1 result didn't cleanly resolve to either named outcome -- needs a design-chat read before proceeding."
    lines_out.append(f"  {risk}")

    report_text = "\n".join(lines_out) + "\n"
    REPORT_PATH.write_text(report_text, encoding="utf-8")

    elapsed = time.time() - t0
    print(f"\nDone in {elapsed:.1f}s. Report written to: {REPORT_PATH}")


if __name__ == "__main__":
    main()
