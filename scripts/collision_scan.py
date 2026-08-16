"""Deterministic collision scan for the prose-rule architecture
(VERIFICATION ARCHITECTURE -- fidelity-not-truth, see
data/palm_rules/README.md). NO LLM calls -- pure Python over the
structured rule data.

Finds rule PAIRS shaped like the H_027/H_002 fabrication proven in
scripts/smoke_test_palm_llm_select.py: two rules that (a) share an
antecedent at the same value (so an LLM reading either one in isolation
could think it applies to the same hand), and (b) differ on a HARD
discriminator antecedent (Starting_Point / Position / Presence) that one
rule requires and the other does not. These are exactly the pairs where
a whole-sentence LLM selector was observed to fire the richer/more
elaborate rule and silently ignore the missing discriminator.

NORMALIZATION NOTE (why a naive (attribute, value) match is not enough):
inspecting the corpus directly shows H_027 and H_002 do NOT share a
literal (attribute, value) pair -- H_002 stores its life-line origin as
Starting_Point='rising_from_Line_of_Life', while H_027 stores the SAME
physical fact (the head line touching the line of life) as
Proximity='touching' with relation_target='Line of Life'. Two different
attribute vocabularies for one fact -- the exact three-vocabularies-drift
mistake class data/_meta/learnings_for_astrology_rules.md exists to
catch. _origin_target() bridges ONLY this specific, source-verified
split (Starting_Point='rising_from_X' <-> Proximity='touching' with
relation_target=X) into a canonical ('<feature>', 'ORIGIN_AT', X) token.
It does NOT invent any broader equivalence -- e.g. HL_001's
'rising_from_Mount_of_Jupiter' and HL_002's
'rising_from_Finger_of_Jupiter' stay distinct tokens (different values in
the corpus's own vocabulary), so that pair is correctly NOT flagged here
even though a human might read them as related.

Hard-discriminator detection stays literal per the task's own definition
(Starting_Point / Position / Presence only) -- no normalization applied
there, since the discriminator IS the value/relation_target difference
itself.

Read-only: only validated_candidates in
data/palm_rules/palm_rules_head_heart_v1.json is read. No rules or
production files are touched. Report-only: writes
diagnostics/latest_run.md (truncate, per CLAUDE.md Diagnostics
convention).
"""
import json
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
_RULES_PATH = _REPO_ROOT / "data" / "palm_rules" / "palm_rules_head_heart_v1.json"
_REPORT_PATH = _REPO_ROOT / "diagnostics" / "latest_run.md"

# Per task spec: only these three attributes count as "hard discriminators".
_HARD_DISCRIMINATOR_ATTRIBUTES = ("Starting_Point", "Position", "Presence")


def load_validated_rules() -> list[dict]:
    """Reads validated_candidates only -- read-only, no other section of
    the rules file is consulted or modified."""
    try:
        with open(_RULES_PATH, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        raise AssertionError(f"could not load {_RULES_PATH}: {exc}") from exc

    rules = data.get("validated_candidates")
    if not isinstance(rules, list) or not rules:
        raise AssertionError(f"{_RULES_PATH.name}: validated_candidates missing or empty")
    return rules


def _origin_target(antecedent: dict) -> str | None:
    """Normalizes an origin/touching-type antecedent to a canonical
    target name; returns None for antecedents that aren't one. See the
    module docstring's NORMALIZATION NOTE for exactly what this does and
    does not bridge."""
    attribute = antecedent.get("attribute")
    value = antecedent.get("value")
    relation_target = antecedent.get("relation_target")

    if attribute == "Starting_Point":
        if isinstance(value, str) and value.startswith("rising_from_"):
            return value[len("rising_from_"):].replace("_", " ")
        if value == "between_Jupiter_and_Saturn":
            return "between Jupiter and Saturn"
        if value is None and relation_target:
            return relation_target
        return None

    if attribute == "Proximity" and value == "touching" and relation_target:
        return relation_target

    return None


def _shared_tokens(rule: dict) -> set[tuple]:
    """Tokens for the 'shares an antecedent at the same value' half of
    the collision test: one literal (feature, attribute, value) token per
    antecedent with a concrete value, plus a normalized
    (feature, 'ORIGIN_AT', target) token for origin/touching antecedents."""
    tokens = set()
    for a in rule.get("antecedents", []):
        feature = a.get("feature")
        attribute = a.get("attribute")
        value = a.get("value")
        if value is not None:
            tokens.add((feature, attribute, value))
        target = _origin_target(a)
        if target is not None:
            tokens.add((feature, "ORIGIN_AT", target))
    return tokens


def _discriminator_tokens(rule: dict) -> set[tuple]:
    """Tokens for the 'differ on a hard discriminator' half of the
    collision test -- Starting_Point / Position / Presence antecedents
    only, literal (no normalization: the difference IS the signal)."""
    tokens = set()
    for a in rule.get("antecedents", []):
        attribute = a.get("attribute")
        if attribute not in _HARD_DISCRIMINATOR_ATTRIBUTES:
            continue
        value = a.get("value")
        relation_target = a.get("relation_target")
        token_value = value if value is not None else f"->{relation_target}"
        tokens.add((attribute, token_value))
    return tokens


def _humanize_token(token: tuple) -> str:
    if len(token) == 3:
        feature, attribute, value = token
        if attribute == "ORIGIN_AT":
            return f"{feature} touches/originates at {value}"
        return f"{feature}.{attribute}={value}"
    attribute, value = token
    return f"{attribute}={value}"


def find_collisions(rules: list[dict]) -> list[dict]:
    """Pairwise scan (all pairs, not restricted to matching topic_group --
    the task explicitly asks for cross head/heart pairs too). A pair is
    flagged iff its shared-token sets intersect AND its discriminator-token
    sets differ (symmetric difference non-empty)."""
    shared = {r["rule_id"]: _shared_tokens(r) for r in rules}
    discrim = {r["rule_id"]: _discriminator_tokens(r) for r in rules}
    topic = {r["rule_id"]: r.get("topic_group") for r in rules}

    collisions = []
    for i in range(len(rules)):
        for j in range(i + 1, len(rules)):
            rid_a, rid_b = rules[i]["rule_id"], rules[j]["rule_id"]

            shared_hit = shared[rid_a] & shared[rid_b]
            if not shared_hit:
                continue

            discrim_diff = discrim[rid_a] ^ discrim[rid_b]
            if not discrim_diff:
                continue

            gloss_shared = "; ".join(sorted(_humanize_token(t) for t in shared_hit))
            gloss_discrim = "; ".join(sorted(_humanize_token(t) for t in discrim_diff))
            collisions.append({
                "rule_a": rid_a,
                "rule_b": rid_b,
                "topic_a": topic[rid_a],
                "topic_b": topic[rid_b],
                "shared": sorted(_humanize_token(t) for t in shared_hit),
                "discriminator": sorted(_humanize_token(t) for t in discrim_diff),
                "gloss": (
                    f"{rid_a} and {rid_b} both key on [{gloss_shared}], "
                    f"but differ on [{gloss_discrim}] -- an LLM given both "
                    f"could fire the wrong one for a hand missing the "
                    f"discriminator."
                ),
            })
    return collisions


def build_report(rules: list[dict], collisions: list[dict]) -> str:
    lines = []
    lines.append("# Latest Run: collision_scan -- LLM-selector confusion candidates\n")
    lines.append(f"Rules scanned (validated_candidates): {len(rules)}")
    lines.append(f"Collision pairs found: {len(collisions)}\n")

    distinct = set()
    for c in collisions:
        distinct.add(c["rule_a"])
        distinct.add(c["rule_b"])
    lines.append(f"Distinct rules involved in >=1 collision (candidates for a hard-prerequisite tag): {len(distinct)}")
    lines.append(f"Rule ids: {sorted(distinct)}\n")

    lines.append("## Method\n")
    lines.append(
        "- Shared token: literal (feature, attribute, value) per antecedent, "
        "PLUS a normalized (feature, ORIGIN_AT, target) token bridging "
        "Starting_Point='rising_from_X' and Proximity='touching' with "
        "relation_target=X (the exact H_027/H_002 vocabulary split -- see "
        "module docstring). No other equivalences are invented.\n"
    )
    lines.append(
        "- Hard discriminator: literal (attribute, value_or_target) for "
        "Starting_Point / Position / Presence antecedents only (per task "
        "spec), no normalization.\n"
    )
    lines.append(
        "- Flagged iff shared-token sets intersect AND discriminator-token "
        "sets differ (symmetric difference non-empty). All pairs across the "
        "full corpus are scanned, not just within-topic_group.\n"
    )

    lines.append("## Collision pairs\n")
    lines.append("| rule_a | rule_b | shared | discriminator | gloss |")
    lines.append("|---|---|---|---|---|")
    for c in sorted(collisions, key=lambda c: (c["rule_a"], c["rule_b"])):
        shared_str = "; ".join(c["shared"])
        disc_str = "; ".join(c["discriminator"])
        lines.append(f"| {c['rule_a']} | {c['rule_b']} | {shared_str} | {disc_str} | {c['gloss']} |")
    lines.append("")

    return "\n".join(lines)


def main() -> None:
    try:
        rules = load_validated_rules()
        collisions = find_collisions(rules)
        report = build_report(rules, collisions)
    except Exception as exc:  # noqa: BLE001 -- fail loud into the report, never silent
        report = (
            "# Latest Run: collision_scan -- FAILED\n\n"
            f"{type(exc).__name__}: {exc}\n"
        )
        _REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(_REPORT_PATH, "w", encoding="utf-8") as f:
            f.write(report)
        raise

    _REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(_REPORT_PATH, "w", encoding="utf-8") as f:
        f.write(report)

    distinct = {rid for c in collisions for rid in (c["rule_a"], c["rule_b"])}
    print(f"Scanned {len(rules)} rules, found {len(collisions)} collision pairs "
          f"across {len(distinct)} distinct rules.")
    print(f"Wrote report to {_REPORT_PATH}")


if __name__ == "__main__":
    main()
