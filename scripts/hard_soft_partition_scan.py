"""Hard/soft antecedent partition scan + hard-side generality proof of the
production matcher (VERIFICATION ARCHITECTURE -- fidelity-not-truth, see
data/palm_rules/README.md).

Two questions, one pass, ZERO LLM calls and zero network:

  (1) PARTITION -- for the S95 architecture sharpen ("FULLY-HARD rules fire
      from the gate; only soft-containing rules reach the LLM", CLAUDE.md
      Locked Decision #23), every antecedent in every validated_candidate
      must be classifiable as HARD (a landmark/topology/computed fact with a
      single structurally-correct answer) or SOFT (a quality/texture read
      that is genuinely reader-dependent). The classification is defined
      ONCE, below, as an attribute-CLASS map plus two structural overrides
      -- it is never a per-rule label, so it cannot be tuned rule-by-rule to
      make a target come out right.

  (2) HARD-SIDE PROOF -- the S95 close-out demonstrated that
      palm_rules_table.match() reproduces the hand-written H_010a/H_010b
      lambda gate. That was ONE rule. This scan runs the same demonstration
      across the WHOLE corpus: for every rule carrying at least one hard
      antecedent, build a synthetic hand-state in the rules' own vocabulary,
      assert match() FIRES the rule, then delete exactly one HARD fact and
      assert match() no longer fires (fail-closed). A rule that fires when
      it shouldn't, or fails to fire when it should, is a generalization
      risk and is FLAGGED, never smoothed over.

The engine is IMPORTED, never reimplemented -- match() and _antecedent_fires
are used exactly as production uses them, so a pass here is a statement
about production behaviour, not about a copy of it.

AMBIGUOUS is a first-class outcome, not a failure: attributes whose class
genuinely depends on a human ruling (Position height-vs-location, Branching
count-vs-target, hand Type, Quadrangle Breadth, Presence 'faded', and
anything not named in either list) are reported as AMBIGUOUS with a reason
and a ruling question. They are NOT forced into a bucket to make the
percentages look clean.

SCOPE NOTE -- the S95 quarantine set (H_013, H_024, H_023, H_018, H_019,
H_020, HL_002, HL_015; SESSION_LOG.md S95 QUARANTINE line) is processed like
every other rule and tagged in its own column, never silently skipped: a
quarantined rule's antecedents still tell us what the partition has to
handle once it is re-modelled.

Report-only: writes diagnostics/latest_run.md (truncate, per CLAUDE.md
Diagnostics convention). Touches no other file, makes no commit.
"""
from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

_RULES_PATH = _REPO_ROOT / "data" / "palm_rules" / "palm_rules_head_heart_v1.json"
_REPORT_PATH = _REPO_ROOT / "diagnostics" / "latest_run.md"

try:
    from agent.interpretive.palm_rules_table import PalmRule, load_rules, match, resolve_priority
except ImportError as exc:  # pragma: no cover -- environment problem, not data
    raise RuntimeError(
        "hard_soft_partition_scan: could not import agent.interpretive.palm_rules_table "
        f"-- this scan proves the PRODUCTION engine's behaviour and refuses to "
        f"reimplement match(): {exc}"
    ) from exc


# ---------------------------------------------------------------------------
# THE PARTITION -- defined once, applied uniformly to every antecedent
# ---------------------------------------------------------------------------

# HARD by attribute: a landmark / topology fact. One structurally-correct
# answer exists; two competent readers looking at the same hand agree.
_HARD_ATTRS = frozenset({
    "Starting_Point",   # which landmark the line rises from
    "Ending_Point",     # which landmark it ends on (no current rule uses it)
    "Presence",         # does the feature exist at all
    "Proximity",        # spatial relation to a named landmark
})

# SOFT by attribute: a quality / texture judgment. Reader-dependent by nature
# -- this is exactly what the whole-sentence LLM step exists to read.
_SOFT_ATTRS = frozenset({
    "Depth",            # NON-comparative only; the comparative override wins first
    "Width",
    "Color",
    "Continuity",       # chained / broken / forked / islanded / barred / clear
    "Direction",
    "Slope",
    "Slope_Magnitude",
    "Curve",
    "Clarity",
})

# AMBIGUOUS by attribute -- each needs a human ruling before it can be routed.
# The value carried by each key is the ruling QUESTION, reproduced verbatim in
# the report's flag list so the reader is never asked to guess what is being
# asked of them.
_AMBIGUOUS_ATTRS = {
    "Position": (
        "Position is VALUE-SPLIT: 'high'/'low' is a height judgment relative to "
        "the palm (reader-dependent, reads SOFT), while 'under_Mount_of_X' / "
        "'terminating_on_X' / 'running_through_X' names a landmark (reads HARD). "
        "RULING NEEDED: split the attribute, or route the whole attribute one way?"
    ),
    "Branching": (
        "Branching is SHAPE-SPLIT: with relation_target set it is a directed "
        "landmark fact (HARD, and the structural override already routes it "
        "there); as a bare count value ('single'/'double'/'branched') it is a "
        "quality read. RULING NEEDED: is a branch COUNT hard (countable) or soft "
        "(reader-dependent)?"
    ),
    "Type": (
        "Hand Type (square / spatulate / philosophic) is a whole-hand shape "
        "classification -- neither a landmark nor a line-quality read, and the "
        "attribute is a known S95 ontology gap (H_018/019/020 quarantine). "
        "RULING NEEDED: hard taxonomy or soft judgment?"
    ),
    "Breadth": (
        "Quadrangle Breadth ('narrow') is a SPACING measurement between two "
        "lines -- arguably computable from their positions (HARD) or a "
        "gestalt read (SOFT). RULING NEEDED."
    ),
    "Length": (
        "Length ('short'/'long'/'extending_across_entire_palm') is named in "
        "NEITHER list in the partition spec. Extent is measurable in principle "
        "but is described in relative prose terms. RULING NEEDED."
    ),
}

# Value-level ambiguity carve-outs, applied only for the attribute they name.
_AMBIGUOUS_VALUES = {
    ("Presence", "faded"): (
        "Presence is HARD as existence, but the value 'faded' is a VISIBILITY "
        "GRADE, not a yes/no -- it smuggles a quality judgment into a hard "
        "attribute. RULING NEEDED."
    ),
}

# Position values whose SHAPE is landmark-naming rather than height-judging.
# Used only to describe the split in the note column -- it never overrides the
# AMBIGUOUS verdict, because forcing the split is precisely what this scan is
# forbidden to do.
_POSITION_LANDMARK_PREFIXES = ("under_", "terminating_on_", "running_through_")

HARD, SOFT, AMBIGUOUS = "hard", "soft", "ambiguous"

# S95 quarantine set (SESSION_LOG.md S95 QUARANTINE) -- tagged, never skipped.
_QUARANTINED = frozenset({"H_013", "H_024", "H_023", "H_018", "H_019", "H_020", "HL_002", "HL_015"})

# Synthetic ordinal used ONLY to satisfy comparative antecedents in the proof
# hand-states. Not a doctrine claim about depth -- just two distinguishable
# magnitudes plus a tie value, so '>' / '<' / '=' can each be satisfied.
_MAG_HIGH, _MAG_TIE, _MAG_LOW = 2, 1, 0


def classify_antecedent(ant) -> tuple[str, str]:
    """Returns (class, note). Structural overrides are checked FIRST and in a
    fixed order, so no attribute-level opinion can override the two facts that
    make an antecedent structurally hard."""
    # Override 1: a directed antecedent names a landmark -- hard regardless of
    # which attribute carries it.
    if ant.relation_target is not None:
        return HARD, f"structural: relation_target={ant.relation_target!r} names a landmark"
    # Override 2: a comparative is COMPUTED from magnitudes by the engine --
    # the 'stronger' interpreted term S95 forbids the LLM from inferring.
    if ant.condition_type == "comparative":
        return HARD, (
            f"structural: comparative {ant.feature} {ant.attribute} "
            f"{ant.comparator} {ant.comparator_feature} -- code-computed"
        )

    key = (ant.attribute, ant.value)
    if key in _AMBIGUOUS_VALUES:
        return AMBIGUOUS, _AMBIGUOUS_VALUES[key]

    if ant.attribute in _AMBIGUOUS_ATTRS:
        note = _AMBIGUOUS_ATTRS[ant.attribute]
        if ant.attribute == "Position" and isinstance(ant.value, str):
            shape = (
                "landmark-shaped value"
                if ant.value.startswith(_POSITION_LANDMARK_PREFIXES)
                else "height-shaped value"
            )
            note = f"[{shape}] {note}"
        return AMBIGUOUS, note

    if ant.attribute in _HARD_ATTRS:
        return HARD, f"attribute-class: {ant.attribute} is a landmark/topology fact"
    if ant.attribute in _SOFT_ATTRS:
        return SOFT, f"attribute-class: {ant.attribute} is a quality/texture read"

    return AMBIGUOUS, (
        f"attribute {ant.attribute!r} appears in NEITHER the hard nor the soft "
        "list -- unclassified by the partition spec. RULING NEEDED."
    )


def bucket_rule(classes: list[str]) -> str:
    """CONTAINS-AMBIGUOUS takes precedence: a rule with any unruled antecedent
    cannot be honestly called fully-hard or fully-soft."""
    if not classes:
        return "NO-ANTECEDENTS"
    if AMBIGUOUS in classes:
        return "CONTAINS-AMBIGUOUS"
    if all(c == HARD for c in classes):
        return "FULLY-HARD"
    if all(c == SOFT for c in classes):
        return "FULLY-SOFT"
    return "MIXED"


# ---------------------------------------------------------------------------
# Synthetic hand-state construction (rules' own vocabulary)
# ---------------------------------------------------------------------------

class UntestableRule(Exception):
    """A synthetic hand-state cannot be honestly built for this rule."""


def _fact_keys(ant) -> list[tuple[str, str, str]]:
    """The (bucket, feature, attribute) slots this antecedent needs filled.
    Used both to build the hand-state and to delete exactly one fact for the
    fail-closed step."""
    if ant.condition_type == "comparative":
        return [
            ("magnitudes", ant.feature, ant.attribute),
            ("magnitudes", ant.comparator_feature, ant.attribute),
        ]
    keys = []
    if ant.value is not None:
        keys.append(("observation", ant.feature, ant.attribute))
    if ant.relation_target is not None:
        keys.append(("targets", ant.feature, ant.attribute))
    return keys


def build_hand_state(rule: PalmRule) -> tuple[dict, dict, dict]:
    """Builds (observation, magnitudes, targets) satisfying EVERY antecedent of
    `rule`. Raises UntestableRule when the antecedent shape cannot be honestly
    satisfied -- never returns a state that only looks satisfying."""
    observation: dict[str, dict[str, str]] = defaultdict(dict)
    magnitudes: dict[str, dict[str, object]] = defaultdict(dict)
    targets: dict[str, dict[str, str]] = defaultdict(dict)

    for ant in rule.antecedents:
        if ant.condition_type == "comparative":
            if ant.comparator_feature is None:
                raise UntestableRule(
                    f"comparative antecedent on {ant.feature}.{ant.attribute} has no "
                    "comparator_feature -- no second magnitude to compare against"
                )
            if ant.comparator == ">":
                a_val, b_val = _MAG_HIGH, _MAG_LOW
            elif ant.comparator == "<":
                a_val, b_val = _MAG_LOW, _MAG_HIGH
            elif ant.comparator == "=":
                a_val, b_val = _MAG_TIE, _MAG_TIE
            else:
                raise UntestableRule(
                    f"comparative antecedent carries comparator {ant.comparator!r}, which "
                    "_antecedent_fires does not implement (only > < =) -- it can never fire"
                )
            magnitudes[ant.feature][ant.attribute] = a_val
            magnitudes[ant.comparator_feature][ant.attribute] = b_val
            continue

        if ant.value is None and ant.relation_target is None:
            raise UntestableRule(
                f"degenerate antecedent {ant.feature}.{ant.attribute}: value AND "
                "relation_target are both null -- _antecedent_fires returns False "
                "unconditionally, so no hand-state can fire this rule"
            )
        if ant.value is not None:
            observation[ant.feature][ant.attribute] = ant.value
        if ant.relation_target is not None:
            targets[ant.feature][ant.attribute] = ant.relation_target

    return dict(observation), dict(magnitudes), dict(targets)


def _delete_fact(state: tuple[dict, dict, dict], bucket: str, feature: str, attribute: str) -> tuple[dict, dict, dict]:
    """Returns a deep-ish copy of the state with one fact removed."""
    observation, magnitudes, targets = state
    copies = {
        "observation": {f: dict(v) for f, v in observation.items()},
        "magnitudes": {f: dict(v) for f, v in magnitudes.items()},
        "targets": {f: dict(v) for f, v in targets.items()},
    }
    copies[bucket].get(feature, {}).pop(attribute, None)
    return copies["observation"], copies["magnitudes"], copies["targets"]


def prove_rule(rule: PalmRule, classes: list[str], all_rules) -> dict:
    """The hard-side proof for one rule. Returns a result row; never raises for
    a rule-level problem -- an unbuildable state is reported as UNTESTABLE with
    its reason, never as a pass."""
    row = {
        "rule_id": rule.rule_id,
        "fires": None,
        "fails_closed": None,
        "verdict": None,
        "scope": None,
        "removed": None,
        "co_fired": [],
        "reason": "",
    }

    if rule.verified is not True:
        row["verdict"] = "UNTESTABLE"
        row["reason"] = "rule.verified is not True -- match() skips it by design (fail-closed)"
        return row

    hard_idx = [i for i, c in enumerate(classes) if c == HARD]
    if not hard_idx:
        row["verdict"] = "N/A"
        row["reason"] = "no hard antecedent -- outside the hard-side proof's scope"
        return row

    try:
        state = build_hand_state(rule)
    except UntestableRule as exc:
        row["verdict"] = "UNTESTABLE"
        row["reason"] = str(exc)
        return row

    row["scope"] = "hard-only" if all(c == HARD for c in classes) else "all-antecedents"

    # Baseline: the full synthetic state must fire the rule.
    try:
        fired = {r.rule_id for r in match(state[0], state[1], all_rules, state[2])}
    except Exception as exc:  # noqa: BLE001 -- engine failure must surface, not pass
        row["verdict"] = "UNTESTABLE"
        row["reason"] = f"match() raised on the baseline state: {type(exc).__name__}: {exc}"
        return row
    row["fires"] = rule.rule_id in fired
    # CO-FIRE: match() is run over the WHOLE corpus, so a synthetic state built
    # for one rule can also satisfy others. That is not automatically a defect
    # (a genuinely more-general rule SHOULD co-fire, and resolve_priority()
    # exists to arbitrate) -- but it is the collision surface the S94 scan
    # flagged, so it is measured and reported rather than left invisible.
    row["co_fired"] = sorted(fired - {rule.rule_id})

    # Fail-closed: delete exactly ONE hard fact and re-run.
    target_ant = rule.antecedents[hard_idx[0]]
    keys = _fact_keys(target_ant)
    if not keys:
        row["verdict"] = "UNTESTABLE"
        row["reason"] = f"hard antecedent {target_ant.attribute} occupies no hand-state slot to delete"
        return row

    # Guard: if another antecedent of this SAME rule writes the same slot, the
    # deletion is not isolating anything -- say so rather than claim a pass.
    bucket, feature, attribute = keys[0]
    others = [
        k for i, a in enumerate(rule.antecedents) if i != hard_idx[0]
        for k in _fact_keys(a)
    ]
    if (bucket, feature, attribute) in others:
        row["verdict"] = "UNTESTABLE"
        row["reason"] = (
            f"the hard fact {feature}.{attribute} ({bucket}) is also written by another "
            "antecedent of the same rule -- deleting it does not isolate one hard fact"
        )
        return row

    row["removed"] = f"{bucket}:{feature}.{attribute}"
    reduced = _delete_fact(state, bucket, feature, attribute)
    try:
        fired_after = {r.rule_id for r in match(reduced[0], reduced[1], all_rules, reduced[2])}
    except Exception as exc:  # noqa: BLE001
        row["verdict"] = "UNTESTABLE"
        row["reason"] = f"match() raised on the reduced state: {type(exc).__name__}: {exc}"
        return row
    row["fails_closed"] = rule.rule_id not in fired_after

    row["verdict"] = "PASS" if (row["fires"] and row["fails_closed"]) else "FAIL"
    if row["verdict"] == "FAIL":
        if not row["fires"]:
            row["reason"] = "did NOT fire on a state satisfying all its antecedents"
        else:
            row["reason"] = "still fired after a required hard fact was removed (NOT fail-closed)"
    return row


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

def _esc(text) -> str:
    return str(text).replace("|", "/").replace("\n", " ")


def _ant_label(ant) -> str:
    bits = f"{ant.feature}.{ant.attribute}"
    if ant.condition_type == "comparative":
        return f"{bits} {ant.comparator} {ant.comparator_feature} (comparative)"
    if ant.relation_target is not None:
        val = "*" if ant.value is None else ant.value
        return f"{bits}={val} -> {ant.relation_target}"
    return f"{bits}={ant.value}"


def build_report(rules, per_rule) -> str:
    total = len(rules)
    lines: list[str] = []
    lines.append("# Latest Run: hard/soft antecedent partition scan + hard-side proof of match()\n")
    lines.append(
        "Report-only. No LLM call, no network, no source edit, nothing committed. "
        "The engine is IMPORTED from `agent/interpretive/palm_rules_table.py` "
        "(`match()` / `_antecedent_fires`) and used exactly as production uses it — "
        "not reimplemented — so every PASS below is a statement about production "
        "behaviour.\n"
    )
    lines.append(f"Corpus: `{_RULES_PATH.relative_to(_REPO_ROOT).as_posix()}`, "
                 f"`validated_candidates` — **{total} rules**, "
                 f"{sum(len(r.antecedents) for r in rules)} antecedents.\n")

    # --- the partition, stated once -------------------------------------
    lines.append("## 1. The partition (defined once, applied uniformly)\n")
    lines.append("Structural overrides, checked first in this order:\n")
    lines.append("1. `relation_target` is set → **HARD** (names a landmark).")
    lines.append("2. `condition_type == \"comparative\"` → **HARD** (code-computed from "
                 "`magnitudes`; the 'stronger' interpreted term S95 forbids the LLM to infer).\n")
    lines.append(f"- **HARD attributes:** {', '.join(sorted(_HARD_ATTRS))}")
    lines.append(f"- **SOFT attributes:** {', '.join(sorted(_SOFT_ATTRS))}")
    lines.append(f"- **AMBIGUOUS attributes (ruling needed):** {', '.join(sorted(_AMBIGUOUS_ATTRS))}"
                 f"; plus the value-level carve-out {sorted(_AMBIGUOUS_VALUES)}")
    lines.append("- Anything in neither list → **AMBIGUOUS**, never defaulted.\n")
    lines.append("No per-rule labels exist anywhere in this scan: the class of an antecedent "
                 "is a function of `(attribute, value, relation_target, condition_type)` only.\n")

    # --- bucket counts ---------------------------------------------------
    counts = Counter(r["bucket"] for r in per_rule)
    lines.append("## 2. Bucket counts\n")
    lines.append("| bucket | rules | % of corpus |")
    lines.append("|---|---|---|")
    for bucket in ("FULLY-HARD", "FULLY-SOFT", "MIXED", "CONTAINS-AMBIGUOUS", "NO-ANTECEDENTS"):
        n = counts.get(bucket, 0)
        if n or bucket != "NO-ANTECEDENTS":
            lines.append(f"| {bucket} | {n} | {100.0 * n / total:.1f}% |")
    lines.append("")
    cls_counts = Counter(c for r in per_rule for c in r["classes"])
    tot_ants = sum(cls_counts.values())
    lines.append(f"Antecedent-level: **{cls_counts.get(HARD,0)} hard** "
                 f"({100.0*cls_counts.get(HARD,0)/tot_ants:.1f}%), "
                 f"**{cls_counts.get(SOFT,0)} soft** "
                 f"({100.0*cls_counts.get(SOFT,0)/tot_ants:.1f}%), "
                 f"**{cls_counts.get(AMBIGUOUS,0)} ambiguous** "
                 f"({100.0*cls_counts.get(AMBIGUOUS,0)/tot_ants:.1f}%) "
                 f"of {tot_ants}.\n")

    # --- per-antecedent table -------------------------------------------
    lines.append("## 3. Per-antecedent classification (all rules, quarantine tagged)\n")
    lines.append("| rule | S95 quarantine | antecedent | class | note |")
    lines.append("|---|---|---|---|---|")
    for row in per_rule:
        rule = row["rule"]
        q = "**QUARANTINED**" if rule.rule_id in _QUARANTINED else ""
        if not rule.antecedents:
            lines.append(f"| {rule.rule_id} | {q} | *(none)* | — | rule has no antecedents |")
        for ant, cls, note in zip(rule.antecedents, row["classes"], row["notes"]):
            lines.append(f"| {rule.rule_id} | {q} | `{_esc(_ant_label(ant))}` | **{cls}** | {_esc(note)} |")
    lines.append("")

    # --- hard-side proof --------------------------------------------------
    proofs = [r for r in per_rule if r["proof"]["verdict"] not in (None, "N/A")]
    lines.append("## 4. HARD-SIDE PROOF via the real `match()`\n")
    lines.append(
        "For each rule with ≥1 hard antecedent: build a synthetic hand-state in the "
        "rules' own vocabulary, assert `match()` fires the rule, then delete exactly "
        "ONE hard fact and assert it no longer fires.\n"
    )
    lines.append(
        "**Scope column, stated honestly:** `hard-only` means the rule is FULLY-HARD, so "
        "the state satisfies nothing but hard facts — the literal test asked for. "
        "`all-antecedents` means the rule also carries soft/ambiguous antecedents; since "
        "`match()` is AND-over-all-antecedents, a hard-only state could never produce a "
        "baseline fire, so the soft antecedents are satisfied too. The **deletion is "
        "always of a HARD fact**, so the fail-closed half of the test is unaffected.\n"
    )
    lines.append("| rule | quarantine | scope | fires-when-satisfied | fails-closed-when-removed | removed fact | co-fired | verdict |")
    lines.append("|---|---|---|---|---|---|---|---|")
    for row in per_rule:
        p = row["proof"]
        if p["verdict"] in (None, "N/A"):
            continue
        q = "Q" if row["rule"].rule_id in _QUARANTINED else ""
        verdict = f"**{p['verdict']}**" if p["verdict"] != "PASS" else "PASS"
        co = ", ".join(p["co_fired"]) if p["co_fired"] else "—"
        lines.append(
            f"| {p['rule_id']} | {q} | {p['scope'] or '—'} | {p['fires']} | "
            f"{p['fails_closed']} | `{_esc(p['removed'] or '—')}` | {co} | {verdict} |"
        )
    lines.append("")
    pv = Counter(p["proof"]["verdict"] for p in per_rule)
    lines.append(
        f"**Proof totals: {pv.get('PASS',0)} PASS / {pv.get('FAIL',0)} FAIL / "
        f"{pv.get('UNTESTABLE',0)} UNTESTABLE**, out of {len(proofs)} rules carrying "
        f"≥1 hard antecedent ({pv.get('N/A',0)} rules have no hard antecedent and are "
        "outside this test's scope).\n"
    )

    # --- flags ------------------------------------------------------------
    co_rows = [r for r in per_rule if r["proof"].get("co_fired")]
    lines.append("### 4a. Co-fire measurement (test-strength caveat)\n")
    lines.append(
        "The baseline half of the proof is weak by construction: the hand-state is built "
        "FROM the rule's own antecedents, so a fire is close to tautological. The two "
        "halves that carry real information are (i) the fail-closed deletion and (ii) "
        "this co-fire count — `match()` runs over the whole corpus, so a state built for "
        "one rule may satisfy others. Co-firing is not automatically a defect "
        "(`resolve_priority()` exists to arbitrate, and a more-general rule SHOULD "
        "co-fire), but it is the collision surface the S94 scan flagged, so it is "
        "measured here rather than left invisible.\n"
    )
    if co_rows:
        lines.append(f"**{len(co_rows)} of {len(proofs)} proof states co-fired at least one other rule.** "
                     "Each co-fire is run through the production `resolve_priority()` to show "
                     "whether the existing arbitration actually cleans it up:\n")
        lines.append("| state built for | also fired | after `resolve_priority()` | arbitrated? |")
        lines.append("|---|---|---|---|")
        by_id = {r.rule_id: r for r in rules}
        unarbitrated: list[tuple[str, str, str]] = []
        for r in co_rows:
            rid = r["proof"]["rule_id"]
            co = r["proof"]["co_fired"]
            try:
                survivors, _ = resolve_priority([by_id[rid]] + [by_id[c] for c in co])
                surviving_ids = [s.rule_id for s in survivors]
            except Exception as exc:  # noqa: BLE001
                lines.append(f"| {rid} | {', '.join(co)} | resolve_priority raised: "
                             f"{type(exc).__name__}: {exc} | **UNKNOWN** |")
                continue
            leftover = [c for c in co if c in surviving_ids]
            ok = "yes — suppressed" if not leftover else "**NO**"
            for c in leftover:
                unarbitrated.append((rid, c, by_id[c].topic_group))
            lines.append(f"| {rid} | {', '.join(co)} | {', '.join(surviving_ids)} | {ok} |")
        lines.append("")
        if unarbitrated:
            lines.append("**UNARBITRATED CO-FIRE — the one real finding in this section.** "
                         "`resolve_priority()` only suppresses an antecedent-subset rule "
                         "*within the same `topic_group`*, so these survive together:\n")
            for rid, other, group in unarbitrated:
                lines.append(
                    f"- `{rid}` (group `{by_id[rid].topic_group}`) co-fires `{other}` "
                    f"(group `{group}`) and **neither is suppressed** — the antecedent sets "
                    "are in a strict subset relation, but the cross-group exemption means "
                    "both claims reach the reader."
                )
            lines.append("")
    else:
        lines.append("**No proof state fired any rule other than its own target** — across all "
                     f"{len(proofs)} states, `match()` selected exactly one rule each time.\n")

    lines.append("## 5. FLAG — every AMBIGUOUS antecedent (human ruling needed)\n")
    amb = [
        (row["rule"].rule_id, _ant_label(ant), note)
        for row in per_rule
        for ant, cls, note in zip(row["rule"].antecedents, row["classes"], row["notes"])
        if cls == AMBIGUOUS
    ]
    if amb:
        by_attr = defaultdict(list)
        for rid, label, note in amb:
            by_attr[label.split(".")[1].split("=")[0].split(" ")[0]].append((rid, label, note))
        lines.append(f"{len(amb)} ambiguous antecedents across "
                     f"{len({r for r, _, _ in amb})} rules, grouped by attribute:\n")
        for attr in sorted(by_attr):
            rows = by_attr[attr]
            lines.append(f"### {attr} — {len(rows)} antecedent(s)\n")
            lines.append(f"> {_esc(rows[0][2])}\n")
            lines.append("| rule | antecedent |")
            lines.append("|---|---|")
            for rid, label, _ in rows:
                lines.append(f"| {rid} | `{_esc(label)}` |")
            lines.append("")
    else:
        lines.append("(none)\n")

    lines.append("## 6. FLAG — rules where `match()` did NOT behave as expected\n")
    bad = [r for r in per_rule if r["proof"]["verdict"] in ("FAIL", "UNTESTABLE")]
    if bad:
        lines.append("| rule | verdict | reason |")
        lines.append("|---|---|---|")
        for r in bad:
            p = r["proof"]
            lines.append(f"| {p['rule_id']} | **{p['verdict']}** | {_esc(p['reason'])} |")
        lines.append("")
        lines.append("These are the real generalization risks — a rule that cannot be fired "
                     "by any synthetic hand-state cannot be fired by a real one either.\n")
    else:
        lines.append("(none — every rule with a hard antecedent fired when satisfied and "
                     "failed closed when a hard fact was removed)\n")

    lines.append("## 7. S95 quarantine set\n")
    lines.append("| rule | bucket | proof verdict |")
    lines.append("|---|---|---|")
    for row in per_rule:
        if row["rule"].rule_id in _QUARANTINED:
            lines.append(f"| {row['rule'].rule_id} | {row['bucket']} | {row['proof']['verdict']} |")
    missing = sorted(_QUARANTINED - {r["rule"].rule_id for r in per_rule})
    lines.append("")
    if missing:
        lines.append(f"**NOTE:** {missing} named in the quarantine set are NOT present in "
                     "`validated_candidates` (retired, parked, or renamed) — reported, not skipped.\n")
    return "\n".join(lines)


def main() -> None:
    try:
        rules = load_rules(_RULES_PATH)
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(
            f"hard_soft_partition_scan: could not load rules from {_RULES_PATH}: "
            f"{type(exc).__name__}: {exc}"
        ) from exc

    per_rule = []
    for rule in rules:
        classes, notes = [], []
        for ant in rule.antecedents:
            cls, note = classify_antecedent(ant)
            classes.append(cls)
            notes.append(note)
        per_rule.append({
            "rule": rule,
            "classes": classes,
            "notes": notes,
            "bucket": bucket_rule(classes),
            "proof": prove_rule(rule, classes, rules),
        })

    for row in per_rule:
        p = row["proof"]
        print(f"{row['rule'].rule_id:8} {row['bucket']:20} proof={p['verdict']}")

    report = build_report(rules, per_rule)
    try:
        _REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
        _REPORT_PATH.write_text(report, encoding="utf-8")
    except OSError as exc:
        raise OSError(f"could not write report to {_REPORT_PATH}: {exc}") from exc
    print(f"\nWrote report to {_REPORT_PATH}")


if __name__ == "__main__":
    main()
