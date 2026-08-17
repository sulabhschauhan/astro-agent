"""Soft-feature eval harness v1 (VERIFICATION ARCHITECTURE -- fidelity-not-truth,
see data/palm_rules/README.md).

Scaffolding-only wiring prompt: reuses the hard-fact gate + whole-sentence
LLM-select + verbatim-quote guard already proven in
scripts/smoke_test_palm_llm_select.py (H_027/H_002 gate probe), repackaged
into one callable -- select() -- and pointed at a fresh slice of the rule
corpus: PURE-SOFT rules from data/palm_rules/palm_rules_head_heart_v1.json's
validated_candidates. "Pure-soft" here means every antecedent's attribute is
one of Continuity/Branching/Direction/Width/Depth/Color (no
Starting_Point/Position/Presence -- i.e. no origin, no location, no
presence-only token), the antecedent value is a plain literal (not a
relation_target wildcard), and its condition_type is not "comparative" --
these are the rules whose firing genuinely depends on reading a described
line quality (forked / broken / chained / doubled / bright red / ...), not
on where a landmark sits or whether a feature exists at all. Filtering the
current corpus this way yields exactly 11 rules: H_004, H_008, H_009, H_011,
H_012, H_025 (head) and HL_013, HL_014, HL_017, HL_019, HL_020 (heart).

Three synthetic hand-states are defined below with EMPTY expected_fire /
expected_not_fire (and, for hand C, expected_precedence) lists -- Sulabh
fills these in as the answer key after reviewing the printed candidate
rules. Until filled, the scorer prints "AWAITING ANSWER KEY" and scores
nothing; this run is report-only wiring, not a graded result.

  Hand A -- H_008 ("chained" head line) PRESENT. All other pure-soft
    features in the hand are deliberately neutral/non-matching, including
    one partial-match distractor (head.direction=wavy, not the "straight"
    H_004 needs) to test that a compound rule's AND-join isn't satisfied by
    a single matching antecedent.
  Hand B -- identical to A except head.continuity flips from "chained" to
    "clear" (single-field diff) -- a phantom-fire control: NOTHING in the
    pure-soft pool should fire (H_008 least of all).
  Hand C -- crowding (head line high + narrow quadrangle) with an explicit
    Depth comparison (head "deep" vs heart "shallow") to exercise the
    H_010a/H_010b precedence pair (same source sentence, mutually exclusive
    "head rules heart" vs "heart rules head" outcomes). H_010a/H_010b are
    NOT pure-soft by the attribute-allowlist above (they key on
    Position/Quadrangle-Breadth/comparative-Depth) -- they are added to hand
    C's candidate pool as a deliberate, documented exception, because the
    precedence tie-break this hand exists to test has no pure-soft
    candidate to test it with. A deterministic hard-prerequisite gate
    (reusing the smoke test's per-rule-id lambda-check pattern) resolves the
    Depth comparison in pure Python before the LLM ever sees a candidate
    list, so only the winning rule of the pair is even offered -- structural
    impossibility for the loser to fire, same design as the smoke test's
    H_027/H_002 gate.

Deliberately out of scope for this prompt: no rule file or ontology edit,
no commit. Report-only, writes diagnostics/latest_run.md (truncate, per
CLAUDE.md Diagnostics convention).
"""
import json
from pathlib import Path

from openai import OpenAI

_REPO_ROOT = Path(__file__).resolve().parent.parent
_RULES_PATH = _REPO_ROOT / "data" / "palm_rules" / "palm_rules_head_heart_v1.json"
_REPORT_PATH = _REPO_ROOT / "diagnostics" / "latest_run.md"

_MODEL = "gpt-4o"
_TEMPERATURE = 0
# Single run per hand: expected sets are empty (AWAITING ANSWER KEY), so
# there is nothing yet to measure stability against. Bump this once Sulabh
# fills the answer key and stability across repeated runs becomes a
# meaningful signal.
_N_RUNS = 1

_PURE_SOFT_ATTRS = {"Continuity", "Branching", "Direction", "Width", "Depth", "Color"}
_LINE_FEATURES = {"Line of Head", "Line of Heart"}

_PRECEDENCE_RULE_IDS = ("H_010a", "H_010b")

_DEPTH_ORDINAL = {"shallow": 0, "medium": 1, "deep": 2}


# ---------------------------------------------------------------------------
# Rule corpus: load + pure-soft filter
# ---------------------------------------------------------------------------

def _is_pure_soft(rule: dict) -> bool:
    """A rule is pure-soft iff EVERY antecedent: belongs to a line feature
    (Line of Head / Line of Heart, not Quadrangle/Hand cross-feature), keys
    on an attribute in _PURE_SOFT_ATTRS, carries a plain literal value (not
    a relation_target wildcard), and is not a comparative condition."""
    antecedents = rule.get("antecedents", [])
    if not antecedents:
        return False
    for a in antecedents:
        if a.get("feature") not in _LINE_FEATURES:
            return False
        if a.get("attribute") not in _PURE_SOFT_ATTRS:
            return False
        if a.get("value") is None:
            return False
        if a.get("relation_target"):
            return False
        if a.get("condition_type") == "comparative":
            return False
    return True


def _involves_tag(rule: dict) -> list[str]:
    tags = set()
    for a in rule.get("antecedents", []):
        feat = a.get("feature")
        if feat == "Line of Head":
            tags.add("head")
        elif feat == "Line of Heart":
            tags.add("heart")
        elif feat == "Quadrangle":
            tags.add("quadrangle")
        cf = a.get("comparator_feature")
        if cf == "Line of Head":
            tags.add("head")
        elif cf == "Line of Heart":
            tags.add("heart")
    return sorted(tags) if tags else ["unknown"]


def _to_corpus_item(rule: dict) -> dict:
    if "source_quote" not in rule or not rule["source_quote"]:
        raise AssertionError(f"{rule.get('rule_id')}: missing source_quote")
    if "source_page" not in rule:
        raise AssertionError(f"{rule.get('rule_id')}: missing source_page")
    return {
        "id": rule["rule_id"],
        "involves": _involves_tag(rule),
        "text": rule["source_quote"],
        "page": rule["source_page"],
        "claim": rule.get("claim", ""),
    }


def load_rule_pools() -> tuple[list[dict], dict[str, dict]]:
    """Loads validated_candidates, skips any rule flagged needs_remodel
    (no rule currently carries this flag -- checked defensively so a future
    hand-added flag is honored without a code change), and returns
    (pure_soft_corpus, precedence_corpus_by_id). Fails loud (AssertionError)
    if the two H_010a/H_010b precedence rules are missing -- that pair is
    load-bearing for hand C and must not silently vanish."""
    try:
        with open(_RULES_PATH, encoding="utf-8") as f:
            data = json.load(f)
    except OSError as exc:
        raise OSError(f"could not read rule file {_RULES_PATH}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"rule file {_RULES_PATH} is not valid JSON: {exc}") from exc

    candidates = data.get("validated_candidates", [])
    by_id = {r["rule_id"]: r for r in candidates}

    pure_soft = [
        _to_corpus_item(r) for r in candidates
        if not r.get("needs_remodel") and _is_pure_soft(r)
    ]
    pure_soft.sort(key=lambda r: r["id"])

    precedence_by_id = {}
    for rid in _PRECEDENCE_RULE_IDS:
        if rid not in by_id:
            raise AssertionError(f"{rid}: not found in validated_candidates (required for hand C)")
        precedence_by_id[rid] = _to_corpus_item(by_id[rid])

    return pure_soft, precedence_by_id


# ---------------------------------------------------------------------------
# Synthetic hand states (answer key columns TO BE FILLED BY SULABH)
# ---------------------------------------------------------------------------

_HAND_STATES = {
    "A": {
        "head": {"continuity": "chained", "branching": "single", "direction": "wavy", "width": "medium"},
        "heart": {"continuity": "clear", "width": "medium", "color": "normal"},
        "quadrangle": {"breadth": "normal"},
    },
    "B": {
        "head": {"continuity": "clear", "branching": "single", "direction": "wavy", "width": "medium"},
        "heart": {"continuity": "clear", "width": "medium", "color": "normal"},
        "quadrangle": {"breadth": "normal"},
    },
    "C": {
        "head": {"position": "high", "depth": "deep", "continuity": "clear", "branching": "single", "direction": "wavy", "width": "medium"},
        "heart": {"depth": "shallow", "continuity": "clear", "width": "medium", "color": "normal"},
        "quadrangle": {"breadth": "narrow"},
    },
}

_EXPECTED = {
    "A": {"expected_fire": [], "expected_not_fire": []},
    "B": {"expected_fire": [], "expected_not_fire": []},
    "C": {"expected_fire": [], "expected_not_fire": [], "expected_precedence": []},
}

# One-off probe variant, NOT part of _HAND_STATES/_EXPECTED: Hand C copied
# verbatim (identical head/heart/quadrangle block) plus exactly ONE added
# field, "stronger_line", whose value ("head") is the literal word H_010a's
# own source_quote turns on ("...if that line be the strongest"). Depth
# stays deep/shallow unchanged, so the deterministic gate resolves the same
# way as Hand C (H_010b gated out, H_010a passes) -- the only variable under
# test is whether handing the LLM an explicit lexical match for "the
# strongest" changes whether it fires H_010a, not the gate outcome.
_HAND_STATE_C2 = {
    "head": {"position": "high", "depth": "deep", "continuity": "clear", "branching": "single", "direction": "wavy", "width": "medium"},
    "heart": {"depth": "shallow", "continuity": "clear", "width": "medium", "color": "normal"},
    "quadrangle": {"breadth": "narrow"},
    "stronger_line": "head",
}


# ---------------------------------------------------------------------------
# Hard-prerequisite gate (reused pattern from smoke_test_palm_llm_select.py,
# generalized from a single origin-string check to an arbitrary
# hand_state -> bool check per rule id)
# ---------------------------------------------------------------------------

def _depth_winner(hand_state: dict) -> str | None:
    """Resolves the H_010a/H_010b precedence pair in pure Python: whichever
    of head/heart Depth is ordinally greater wins (per the shared source
    sentence -- 'the head will completely rule the heart, if that line be
    the strongest, and vice versa'). Returns None (fail-closed, both rules
    gated out) if either depth is missing or unrecognized, or on a tie."""
    head_depth = hand_state.get("head", {}).get("depth")
    heart_depth = hand_state.get("heart", {}).get("depth")
    if head_depth not in _DEPTH_ORDINAL or heart_depth not in _DEPTH_ORDINAL:
        return None
    head_v, heart_v = _DEPTH_ORDINAL[head_depth], _DEPTH_ORDINAL[heart_depth]
    if head_v > heart_v:
        return "H_010a"
    if heart_v > head_v:
        return "H_010b"
    return None


_HARD_PREREQUISITES = {
    "H_010a": lambda hand_state: _depth_winner(hand_state) == "H_010a",
    "H_010b": lambda hand_state: _depth_winner(hand_state) == "H_010b",
}


def _apply_gate(candidate_rules: list[dict], hand_state: dict) -> tuple[list[dict], list[str]]:
    """Pure-Python pre-filter: drops any rule whose prerequisite is not
    satisfied by this hand-state. Rules with no prerequisite always pass
    through. Returns (filtered_rules, gated_out_ids)."""
    filtered = []
    gated_out = []
    for rule in candidate_rules:
        check = _HARD_PREREQUISITES.get(rule["id"])
        if check is None or check(hand_state):
            filtered.append(rule)
        else:
            gated_out.append(rule["id"])
    return filtered, gated_out


# ---------------------------------------------------------------------------
# LLM select (verbatim from smoke_test_palm_llm_select.py -- no behaviour
# change per task spec)
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = (
    "You are a rule-evaluation engine for a palmistry system. You will be given "
    "an observed hand's state and, for each rule, its verbatim Cheiro text, id, "
    "page, and involves-tags. Nothing is decomposed for you.\n\n"
    "For each rule, read its full sentence and decide whether its reading "
    "genuinely applies to THIS hand. A rule applies only if the hand matches "
    "everything the sentence requires -- but read the whole sentence, including "
    "phrases like 'even from the finger itself' or 'and vice versa', before "
    "deciding. Evaluate every rule; do not stop early. Fire all that genuinely "
    "apply. Merge the fired readings into one combined interpretation. Quote "
    "each fired rule verbatim. List a feature as unmatched only if no rule "
    "truly covers it.\n\n"
    "Judge each rule ONLY against features explicitly present in the "
    "hand-state. Never introduce, infer, or assert a feature the hand-state "
    "does not contain. If a rule's applicability depends on a feature that is "
    "not stated in the hand-state, do NOT fire it and do NOT mention it. Your "
    "combined_reading may reference ONLY features present in the hand-state -- "
    "do not add origins, lengths, or qualities that were not given.\n\n"
    "Return strict JSON only, matching this shape: "
    '{"fired": [{"id": "<rule_id>", "quote": "<verbatim substring>", "page": <int>}], '
    '"combined_reading": "<string>", "unmatched_features": ["<feature>", ...]}'
)


def _build_user_prompt(corpus: list[dict], hand_state: dict) -> str:
    rules_block = json.dumps(
        [{"id": r["id"], "involves": r["involves"], "text": r["text"], "page": r["page"]} for r in corpus],
        indent=2, ensure_ascii=False,
    )
    hand_state_block = json.dumps(hand_state, indent=2, ensure_ascii=False)
    return (
        "RULES:\n" + rules_block + "\n\n"
        "OBSERVED HAND STATE:\n" + hand_state_block + "\n\n"
        "Decide which rules genuinely apply to this hand and produce the "
        "combined result."
    )


def _call_llm(client: OpenAI, user_prompt: str) -> str:
    """Single try/except boundary around one API call, per CLAUDE.md
    Working Style #6. Raises to the caller, which records and continues."""
    try:
        response = client.chat.completions.create(
            model=_MODEL,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=_TEMPERATURE,
            response_format={"type": "json_object"},
        )
    except Exception as exc:  # noqa: BLE001 -- reraise with meaningful context
        raise RuntimeError(f"OpenAI call failed: {type(exc).__name__}: {exc}") from exc
    return response.choices[0].message.content


def select(client: OpenAI, hand_state: dict, candidate_rules: list[dict]) -> dict:
    """The reused pipeline as one callable: hard-prerequisite gate -> whole-
    sentence LLM select -> verbatim-quote guard. candidate_rules is the
    UNGATED pool (this function applies the gate itself). Returns a dict
    with the gate outcome, the validated fired set (quote-guard passed),
    any quote-guard rejections, and the raw LLM shape for reporting. Never
    raises for a malformed/failed LLM call -- records under "error" and
    returns empty fired/gated results instead, so the caller's per-hand
    loop can continue to the next hand."""
    filtered_rules, gated_out = _apply_gate(candidate_rules, hand_state)
    filtered_by_id = {r["id"]: r for r in filtered_rules}

    result = {
        "gated_out": sorted(gated_out),
        "candidate_ids": [r["id"] for r in filtered_rules],
        "fired": [],
        "invalid_fired": [],
        "combined_reading": "",
        "unmatched_features": [],
        "error": None,
    }

    if not filtered_rules:
        return result

    try:
        user_prompt = _build_user_prompt(filtered_rules, hand_state)
        raw = _call_llm(client, user_prompt)
        parsed = json.loads(raw)
    except Exception as exc:  # noqa: BLE001 -- record and continue, per task spec
        result["error"] = f"{type(exc).__name__}: {exc}"
        return result

    raw_fired = parsed.get("fired", [])
    if not isinstance(raw_fired, list):
        raw_fired = []
    combined_reading = parsed.get("combined_reading", "")
    result["combined_reading"] = combined_reading if isinstance(combined_reading, str) else ""
    unmatched = parsed.get("unmatched_features", [])
    result["unmatched_features"] = unmatched if isinstance(unmatched, list) else []

    for item in raw_fired:
        if not isinstance(item, dict):
            result["invalid_fired"].append({"raw": item, "reason": "not an object"})
            continue
        rid = item.get("id")
        quote = item.get("quote")
        rule = filtered_by_id.get(rid)
        if rule is None:
            result["invalid_fired"].append({"raw": item, "reason": "id not in gated candidate pool"})
            continue
        if not isinstance(quote, str) or quote == "" or quote not in rule["text"]:
            result["invalid_fired"].append({"raw": item, "reason": "quote not a verbatim substring of source_quote"})
            continue
        result["fired"].append({"id": rid, "quote": quote, "page": item.get("page")})

    return result


# ---------------------------------------------------------------------------
# Deterministic scorer (no LLM)
# ---------------------------------------------------------------------------

def _score(fired_ids: set[str], expected_fire: list[str], expected_not_fire: list[str]) -> dict | None:
    if not expected_fire and not expected_not_fire:
        return None
    expected_fire_set = set(expected_fire)
    expected_not_fire_set = set(expected_not_fire)
    true_positive = fired_ids & expected_fire_set
    missed_fire = sorted(expected_fire_set - fired_ids)
    phantom_fire = sorted(fired_ids - expected_fire_set)
    violated_not_fire = sorted(fired_ids & expected_not_fire_set)
    precision = (len(true_positive) / len(fired_ids)) if fired_ids else None
    recall = (len(true_positive) / len(expected_fire_set)) if expected_fire_set else None
    return {
        "precision": precision,
        "recall": recall,
        "missed_fire": missed_fire,
        "phantom_fire": phantom_fire,
        "violated_not_fire": violated_not_fire,
    }


def _score_precedence(fired_ids: set[str], expected_precedence: list[str]) -> dict | None:
    if not expected_precedence:
        return None
    winner = expected_precedence[0]
    losers = expected_precedence[1:]
    precedence_ok = winner in fired_ids and all(loser not in fired_ids for loser in losers)
    return {"winner": winner, "losers": losers, "precedence_ok": precedence_ok}


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

def _format_candidate_table(candidate_rules: list[dict]) -> list[str]:
    lines = ["| id | involves | page | claim |", "|---|---|---|---|"]
    for r in candidate_rules:
        claim = r["claim"].replace("|", "/").replace("\n", " ")
        lines.append(f"| {r['id']} | {','.join(r['involves'])} | {r['page']} | {claim} |")
    return lines


def _format_hand_section(
    hand: str, hand_state: dict, candidate_rules: list[dict],
    expected: dict, run_results: list[dict],
) -> list[str]:
    lines = [f"## Hand {hand}\n", "```json", json.dumps(hand_state, indent=2), "```\n"]
    lines.append(f"### Hand {hand} candidate pure-soft rules (pre-gate, full pool)\n")
    lines.extend(_format_candidate_table(candidate_rules))
    lines.append("")

    failures = []

    for i, result in enumerate(run_results, start=1):
        lines.append(f"### Hand {hand} run {i}\n")
        if result.get("error"):
            lines.append(f"- ERROR: {result['error']}")
            failures.append(f"run {i}: LLM/parse error -- {result['error']}")
            lines.append("")
            continue
        lines.append(f"- gated_out: {result['gated_out'] if result['gated_out'] else '(none)'}")
        lines.append(f"- candidate_ids handed to LLM: {result['candidate_ids']}")
        fired_ids = sorted(item["id"] for item in result["fired"])
        lines.append(f"- fired: {fired_ids if fired_ids else '(none)'}")
        for item in result["fired"]:
            lines.append(f"  - {item['id']} (p.{item['page']}): {item['quote']!r}")
        if result["invalid_fired"]:
            lines.append(f"- **INVALID FIRED (quote-guard rejected, dropped from fired set):**")
            for bad in result["invalid_fired"]:
                lines.append(f"  - {bad['reason']}: {bad['raw']!r}")
            failures.append(f"run {i}: {len(result['invalid_fired'])} fired item(s) failed the verbatim-quote guard")
        lines.append(f"- unmatched_features: {result['unmatched_features']}")
        lines.append(f"- combined_reading: {result['combined_reading']!r}")
        lines.append("")

    lines.append(f"### Hand {hand} score\n")
    last_ok_result = next((r for r in reversed(run_results) if not r.get("error")), None)
    fired_ids = {item["id"] for item in last_ok_result["fired"]} if last_ok_result else set()

    score = _score(fired_ids, expected["expected_fire"], expected["expected_not_fire"])
    if score is None:
        lines.append("**AWAITING ANSWER KEY** -- expected_fire/expected_not_fire are both empty for this hand; nothing scored.\n")
    else:
        lines.append(f"- precision: {score['precision']}")
        lines.append(f"- recall: {score['recall']}")
        lines.append(f"- missed_fire (expected but did not fire): {score['missed_fire']}")
        lines.append(f"- phantom_fire (fired but not expected): {score['phantom_fire']}")
        lines.append(f"- violated_not_fire (explicitly expected NOT to fire, but did): {score['violated_not_fire']}")
        lines.append("")
        if score["missed_fire"]:
            failures.append(f"missed_fire: {score['missed_fire']}")
        if score["phantom_fire"]:
            failures.append(f"phantom_fire: {score['phantom_fire']}")
        if score["violated_not_fire"]:
            failures.append(f"violated_not_fire: {score['violated_not_fire']}")

    if "expected_precedence" in expected:
        prec = _score_precedence(fired_ids, expected["expected_precedence"])
        lines.append(f"### Hand {hand} precedence (H_010a vs H_010b)\n")
        if prec is None:
            lines.append("**AWAITING ANSWER KEY** -- expected_precedence is empty; nothing scored.\n")
        else:
            lines.append(f"- winner: {prec['winner']}, losers: {prec['losers']}")
            lines.append(f"- precedence_ok: {prec['precedence_ok']}\n")
            if not prec["precedence_ok"]:
                failures.append(f"precedence violated: expected winner {prec['winner']} vs losers {prec['losers']}, fired={sorted(fired_ids)}")

    lines.append(f"### Hand {hand} FAILURES\n")
    if failures:
        for f in failures:
            lines.append(f"- {f}")
    else:
        lines.append("(none)")
    lines.append("")

    return lines


def _format_report(
    pure_soft_pool: list[dict],
    hands_candidates: dict[str, list[dict]],
    results_by_hand: dict[str, list[dict]],
) -> str:
    lines = ["# Latest Run: soft-feature eval harness v1 (scaffold + wiring, report-only)\n"]
    lines.append(f"Model: {_MODEL}, temperature={_TEMPERATURE}, runs per hand={_N_RUNS}\n")
    lines.append("## Full pure-soft rule pool (validated_candidates, needs_remodel skipped)\n")
    lines.extend(_format_candidate_table(pure_soft_pool))
    lines.append("")
    lines.append(
        "Hand C additionally carries H_010a/H_010b (Position/Quadrangle-Breadth/"
        "comparative-Depth -- NOT pure-soft by the attribute allowlist) as a "
        "deliberate documented exception, needed to exercise the precedence "
        "tie-break; see module docstring.\n"
    )

    for hand in ("A", "B", "C"):
        lines.extend(_format_hand_section(
            hand, _HAND_STATES[hand], hands_candidates[hand], _EXPECTED[hand], results_by_hand[hand],
        ))

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# C2 probe report (standalone -- not the full A/B/C report; no scoring,
# per task spec, since C2 carries no expected_* answer key)
# ---------------------------------------------------------------------------

def _format_c2_report(hand_state: dict, result: dict) -> str:
    lines = [
        "# Latest Run: C2 probe -- explicit stronger_line field vs Hand C\n",
        f"Model: {_MODEL}, temperature={_TEMPERATURE}\n",
        (
            "C2 = Hand C copied verbatim, plus exactly one added field: "
            '`"stronger_line": "head"` -- a literal echo of H_010a\'s own '
            'wording ("if that line be the strongest"). Same gate, same '
            "candidate pool, same select() path as Hand C. Everything else "
            "(head/heart/quadrangle block) is byte-identical to Hand C.\n"
        ),
        "## Hand state\n",
        "```json",
        json.dumps(hand_state, indent=2),
        "```\n",
    ]

    if result.get("error"):
        lines.append(f"- ERROR: {result['error']}\n")
        lines.append("## Verdict\n")
        lines.append("H_010a fired for C2: ERROR (LLM call failed, see above) vs Hand C (no).\n")
        return "\n".join(lines)

    fired_ids = sorted(item["id"] for item in result["fired"])
    lines.append(f"- gated_out: {result['gated_out'] if result['gated_out'] else '(none)'}")
    lines.append(f"- candidate_ids handed to LLM: {result['candidate_ids']}")
    lines.append(f"- fired: {fired_ids if fired_ids else '(none)'}")
    for item in result["fired"]:
        lines.append(f"  - {item['id']} (p.{item['page']}): {item['quote']!r}")
    if result["invalid_fired"]:
        lines.append("- **INVALID FIRED (quote-guard rejected, dropped from fired set):**")
        for bad in result["invalid_fired"]:
            lines.append(f"  - {bad['reason']}: {bad['raw']!r}")
    lines.append(f"- combined_reading: {result['combined_reading']!r}\n")

    h010a_fired = "H_010a" in fired_ids
    lines.append("## Verdict\n")
    lines.append(
        f"H_010a fired for C2: {'yes' if h010a_fired else 'no'} "
        "vs Hand C (no, per the prior recorded run -- H_010a passed the "
        "gate but the LLM declined to fire it against Hand C's "
        '"depth"/"breadth" wording alone).\n'
    )
    return "\n".join(lines)


def run_c2_probe() -> None:
    """Report-only, single-hand probe. Reuses load_rule_pools() and
    select() unchanged (same gate + LLM-select + verbatim-quote guard path
    as Hand C in main()). Does not touch _HAND_STATES/_EXPECTED (A/B/C) or
    any rule/ontology file. Writes diagnostics/latest_run.md (truncate),
    containing ONLY the C2 result -- not the full A/B/C report."""
    pure_soft_pool, precedence_by_id = load_rule_pools()
    candidate_rules = pure_soft_pool + [precedence_by_id["H_010a"], precedence_by_id["H_010b"]]

    client = OpenAI()
    try:
        result = select(client, _HAND_STATE_C2, candidate_rules)
    except Exception as exc:  # noqa: BLE001 -- select() already guards its own LLM
        # call internally; this outer boundary catches anything unexpected
        # (e.g. a client construction failure) so the probe still reports
        # instead of crashing.
        result = {
            "gated_out": [], "candidate_ids": [], "fired": [], "invalid_fired": [],
            "combined_reading": "", "unmatched_features": [],
            "error": f"{type(exc).__name__}: {exc}",
        }

    fired_ids = sorted(item["id"] for item in result["fired"]) if not result.get("error") else "ERROR"
    print(f"C2 probe: fired={fired_ids} gated_out={result.get('gated_out')} error={result.get('error')}")

    report = _format_c2_report(_HAND_STATE_C2, result)
    try:
        _REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(_REPORT_PATH, "w", encoding="utf-8") as f:
            f.write(report)
    except OSError as exc:
        raise OSError(f"could not write report to {_REPORT_PATH}: {exc}") from exc
    print(f"Wrote report to {_REPORT_PATH}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    pure_soft_pool, precedence_by_id = load_rule_pools()

    hands_candidates = {
        "A": pure_soft_pool,
        "B": pure_soft_pool,
        "C": pure_soft_pool + [precedence_by_id["H_010a"], precedence_by_id["H_010b"]],
    }

    client = OpenAI()
    results_by_hand: dict[str, list[dict]] = {}
    for hand in ("A", "B", "C"):
        hand_state = _HAND_STATES[hand]
        candidate_rules = hands_candidates[hand]
        print(f"hand {hand}: {len(candidate_rules)} candidate rule(s)")
        run_results = []
        for i in range(1, _N_RUNS + 1):
            result = select(client, hand_state, candidate_rules)
            run_results.append(result)
            fired_ids = sorted(item["id"] for item in result["fired"]) if not result.get("error") else "ERROR"
            print(f"hand {hand} run {i}: fired={fired_ids} gated_out={result.get('gated_out')} error={result.get('error')}")
        results_by_hand[hand] = run_results

    report = _format_report(pure_soft_pool, hands_candidates, results_by_hand)
    try:
        _REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(_REPORT_PATH, "w", encoding="utf-8") as f:
            f.write(report)
    except OSError as exc:
        raise OSError(f"could not write report to {_REPORT_PATH}: {exc}") from exc
    print(f"\nWrote report to {_REPORT_PATH}")


if __name__ == "__main__":
    # This task's scope is the C2 probe only (see run_c2_probe's docstring).
    # main() (full A/B/C harness run) is left intact, unchanged, for future
    # use -- swap this line to call main() to reproduce the earlier report.
    run_c2_probe()
