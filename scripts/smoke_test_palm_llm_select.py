"""LLM-select smoke test for the prose-rule architecture (VERIFICATION
ARCHITECTURE — fidelity-not-truth, see data/palm_rules/README.md).

Builds a 7-rule in-file prose corpus (verbatim source_quote spans pulled
from data/palm_rules/palm_rules_head_heart_v1.json, asserted as substrings
at load time), gives it plus a hand-state to gpt-4o (temp=0), and runs a
WHOLE-SENTENCE evaluation: no condition decomposition, no per-condition
checklist, no rewriting the rule -- the model reads each rule's full
verbatim sentence and decides whether it genuinely applies to the hand,
explicitly instructed to read the whole sentence (including qualifying
phrases like "even from the finger itself") before deciding, to
evaluate every rule rather than stopping early, to merge every fired
rule's reading into one combined interpretation, and to judge each rule
ONLY against features explicitly present in the hand-state, never
inventing or asserting an unstated feature. Prompt and rule corpus are
UNCHANGED from the prior (Jupiter_touching_life) run.

Two hand-state CASES are run this time, both 5x. Prior runs (see
diagnostics/latest_run.md history) found that giving the LLM the
whole-sentence H_027/H_002 pair unfiltered produces a STABLE failure:
H_027 (Jupiter-origin, compound) fires every time regardless of whether
Jupiter is actually present, and H_002 (plain touching-life) never fires
-- unfixed by removing decomposition or by adding an explicit
anti-fabrication instruction. This run adds a DETERMINISTIC CODE GATE in
front of the LLM step: a small hard-prerequisite map, checked in pure
Python against the hand-state, drops H_027 from the candidate list
handed to the model whenever head.origin doesn't contain "Jupiter", and
drops H_002 whenever head.origin isn't exactly "touching_life". Every
other rule (H_026, HL_001, HL_002, H_005, HL_019) has no prerequisite and
always passes through untouched. The LLM step itself (system prompt,
whole-sentence reading, anti-fabrication instruction) is UNCHANGED --
this test is asking whether removing the ambiguous rule from the
candidate pool entirely, rather than trusting the model to reason its
way out of the trap, fixes the failure structurally.
  CASE A: head.origin='Jupiter_touching_life' -- gate drops H_002 (its
    prerequisite fails), H_027 passes gate. Expected: H_027 fires,
    H_002 (unreachable) does not.
  CASE B: head.origin='touching_life' -- gate drops H_027 (its
    prerequisite fails, so it is NEVER SHOWN to the model), H_002
    passes gate. Expected: H_027 does not fire (structurally
    impossible now), H_002 fires.
Case B's combined_reading can still legitimately mention "Jupiter" via
the heart line (heart.origin is unchanged, finger_of_Jupiter, and HL_002
has no prerequisite so it still reaches the model) -- the jupiter_absent
check for Case B is scoped to HEAD-tagged fired quotes and head-tagged
sentences in combined_reading only, not bare "Jupiter" presence overall
(same scoping principle as the prior run's head_jupiter_claim check).
Bare "Jupiter" presence is still reported loudly per run for visibility.

No production code or rules files are touched. Report-only: writes
diagnostics/latest_run.md (truncate, per CLAUDE.md Diagnostics convention).
"""
import json
import re
from pathlib import Path

from openai import OpenAI

_REPO_ROOT = Path(__file__).resolve().parent.parent
_RULES_PATH = _REPO_ROOT / "data" / "palm_rules" / "palm_rules_head_heart_v1.json"
_REPORT_PATH = _REPO_ROOT / "diagnostics" / "latest_run.md"

_MODEL = "gpt-4o"
_TEMPERATURE = 0
_N_RUNS = 5

# rule_id -> involves tags (per-task spec)
_RULE_IDS = {
    "H_002": ["head"],    # gated in Case B (plain touching_life), gated out in Case A
    "H_026": ["head"],
    "H_027": ["head"],    # gated in Case A (Jupiter present), gated out in Case B
    "HL_001": ["heart"],  # no prerequisite; trap -- "center of Jupiter" origin, not satisfied
    "HL_002": ["heart"],  # no prerequisite
    "H_005": ["head"],    # no prerequisite; neutral non-match: short, hand-state is long
    "HL_019": ["heart"],  # no prerequisite; neutral non-match: color, not observed
}

_HAND_STATES = {
    "A": {
        "head": {"origin": "Jupiter_touching_life", "length": "long", "direction": "sloping_gentle"},
        "heart": {"origin": "finger_of_Jupiter"},
        "gap": "moderate",
    },
    "B": {
        "head": {"origin": "touching_life", "length": "long", "direction": "sloping_gentle"},
        "heart": {"origin": "finger_of_Jupiter"},
        "gap": "moderate",
    },
}

# Deterministic hard-prerequisite gate, checked in pure Python against
# head.origin BEFORE the candidate list is handed to the LLM. Only the
# two rules under test get a prerequisite -- the rest of the corpus is
# intentionally left unauthored/ungated per the task scope (do not author
# prerequisites for H_026/HL_001/HL_002/H_005/HL_019 here).
_HARD_PREREQUISITES = {
    "H_027": lambda origin: "Jupiter" in origin,       # requires head.origin includes 'Jupiter'
    "H_002": lambda origin: origin == "touching_life",  # requires plain touching_life, NOT Jupiter
}

_CASE_EXPECTED_GATED_OUT = {
    "A": {"H_002"},  # Jupiter_touching_life fails H_002's exact-match prerequisite
    "B": {"H_027"},  # touching_life fails H_027's Jupiter-substring prerequisite
}


def _apply_gate(corpus: list[dict], hand_state: dict) -> tuple[list[dict], list[str]]:
    """Pure-Python pre-filter: drops any rule whose prerequisite (keyed by
    rule id, checked against head.origin) is not satisfied by this
    hand-state. Rules with no prerequisite always pass through. Returns
    (filtered_corpus, gated_out_ids) -- gated_out_ids is logged, not just
    silently dropped."""
    origin = hand_state["head"]["origin"]
    filtered = []
    gated_out = []
    for rule in corpus:
        check = _HARD_PREREQUISITES.get(rule["id"])
        if check is None or check(origin):
            filtered.append(rule)
        else:
            gated_out.append(rule["id"])
    return filtered, gated_out


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


def load_rule_corpus() -> list[dict]:
    """Loads the 7 target rules from the head/heart rules file and builds
    the in-file prose corpus. Asserts each pulled text is a verbatim
    substring of that rule's own stored source_quote -- fails loud
    (AssertionError) if the rules file has drifted since this script's
    ids/pages were chosen."""
    with open(_RULES_PATH, encoding="utf-8") as f:
        data = json.load(f)

    by_id = {}
    for section in ("validated_candidates", "parked_pending_relation_target", "retired_superseded"):
        for rule in data.get(section, []):
            by_id[rule["rule_id"]] = rule

    corpus = []
    for rule_id, involves in _RULE_IDS.items():
        if rule_id not in by_id:
            raise AssertionError(f"{rule_id}: not found in {_RULES_PATH.name}")
        rule = by_id[rule_id]
        source_quote = rule["source_quote"]
        text = source_quote  # verbatim, full stored quote
        assert text in source_quote, f"{rule_id}: text is not a substring of its own source_quote"
        corpus.append({
            "id": rule_id,
            "involves": involves,
            "text": text,
            "page": rule["source_page"],
        })
    return corpus


def _build_user_prompt(corpus: list[dict], hand_state: dict) -> str:
    rules_block = json.dumps(corpus, indent=2, ensure_ascii=False)
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
    response = client.chat.completions.create(
        model=_MODEL,
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=_TEMPERATURE,
        response_format={"type": "json_object"},
    )
    return response.choices[0].message.content


def _head_jupiter_claim_present(combined_reading: str) -> bool:
    """True if any sentence mentions BOTH 'head' and 'jupiter' -- a
    head-line Jupiter-origin claim invented in prose despite H_027 never
    being a candidate rule in Case B (it was gated out before the LLM
    call, so the model has no legitimate rule text to draw this from).
    Case B's heart line legitimately involves Jupiter (finger_of_Jupiter
    is unchanged, HL_002 has no prerequisite and always reaches the
    model), so bare presence of the word 'Jupiter' is expected and not
    itself a fabrication."""
    sentences = re.split(r"(?<=[.!?])\s+", combined_reading)
    for sentence in sentences:
        lowered = sentence.lower()
        if "jupiter" in lowered and "head" in lowered:
            return True
    return False


def _head_tagged_quote_has_jupiter(fired: list, corpus_by_id: dict[str, dict]) -> bool:
    """True if a fired quote belonging to a head-tagged rule contains
    'jupiter'. With H_027 gated out of the candidate pool in Case B, no
    head-tagged rule the model could legitimately cite mentions Jupiter
    -- so this can only fire on a hallucinated id/quote, not a genuine
    citation."""
    for item in fired:
        if not isinstance(item, dict):
            continue
        rule = corpus_by_id.get(item.get("id"))
        if rule is None:
            continue
        quote = item.get("quote") or ""
        if "head" in rule.get("involves", []) and "jupiter" in quote.lower():
            return True
    return False


def _check_run(parsed: dict, corpus_by_id: dict[str, dict], case: str, gated_out: list[str]) -> dict:
    """Deterministic per-run checks, case-aware. corpus_by_id here is the
    FILTERED (post-gate) corpus -- only rules the model actually saw --
    so a fired id/quote referencing a gated-out rule fails quotes_ok
    rather than being silently validated against text never shown to
    the model. Never raises -- a malformed shape shows up as a failed
    check, not a crash."""
    fired = parsed.get("fired", [])
    if not isinstance(fired, list):
        fired = []
    combined_reading = parsed.get("combined_reading", "")
    if not isinstance(combined_reading, str):
        combined_reading = ""
    unmatched = parsed.get("unmatched_features", [])
    if not isinstance(unmatched, list):
        unmatched = []

    fired_ids = {
        item.get("id") for item in fired
        if isinstance(item, dict) and item.get("id") is not None
    }

    gate_correct = set(gated_out) == _CASE_EXPECTED_GATED_OUT[case]

    if case == "A":
        case_ok = "H_027" in fired_ids and "H_002" not in fired_ids
    else:
        case_ok = "H_027" not in fired_ids and "H_002" in fired_ids

    quotes_ok = True
    for item in fired:
        if not isinstance(item, dict):
            quotes_ok = False
            continue
        rid = item.get("id")
        quote = item.get("quote")
        rule = corpus_by_id.get(rid)
        if rule is None or not isinstance(quote, str) or quote == "" or quote not in rule["text"]:
            quotes_ok = False

    reading_lower = combined_reading.lower()
    jupiter_literal_present = "jupiter" in reading_lower or any(
        isinstance(item, dict) and "jupiter" in (item.get("quote") or "").lower()
        for item in fired
    )

    result = {
        "gate_correct": gate_correct,
        "gated_out": sorted(gated_out),
        "case_ok": case_ok,
        "quotes_ok": quotes_ok,
        "jupiter_literal_present": jupiter_literal_present,
        "fired_ids": sorted(fired_ids),
        "unmatched_features": unmatched,
        "combined_reading": combined_reading,
    }

    if case == "B":
        head_jupiter_claim = _head_jupiter_claim_present(combined_reading)
        head_quote_jupiter = _head_tagged_quote_has_jupiter(fired, corpus_by_id)
        result["jupiter_absent"] = not head_jupiter_claim and not head_quote_jupiter
        result["head_jupiter_claim"] = head_jupiter_claim

    return result


def _format_case_section(
    case: str, hand_state: dict, gated_out: list[str],
    candidate_ids: list[str], run_results: list[dict],
) -> list[str]:
    lines = []
    lines.append(f"## Case {case}\n")
    lines.append("```json")
    lines.append(json.dumps(hand_state, indent=2))
    lines.append("```\n")
    lines.append(
        f"**Gate result:** dropped {gated_out if gated_out else '(none)'}; "
        f"candidate rules handed to the LLM: {candidate_ids}\n"
    )

    lines.append(f"### Case {case} per-run results\n")
    if case == "B":
        lines.append("| run | gate_correct | case_ok | quotes_ok | jupiter_absent | fired_ids |")
        lines.append("|---|---|---|---|---|---|")
        check_keys = ("gate_correct", "case_ok", "quotes_ok", "jupiter_absent")
    else:
        lines.append("| run | gate_correct | case_ok | quotes_ok | fired_ids |")
        lines.append("|---|---|---|---|---|")
        check_keys = ("gate_correct", "case_ok", "quotes_ok")
    clean_count = 0
    for i, r in enumerate(run_results, start=1):
        if r.get("error"):
            lines.append(f"| {i} | " + " | ".join(["ERROR"] * len(check_keys)) + f" | {r['error']} |")
            continue
        all_clean = all(r[k] for k in check_keys)
        if all_clean:
            clean_count += 1
        fired_ids = ",".join(r["fired_ids"]) if r["fired_ids"] else "-"
        cells = " | ".join(str(r[k]) for k in check_keys)
        lines.append(f"| {i} | {cells} | {fired_ids} |")
    lines.append("")
    lines.append(
        f"**Case {case} stability: {clean_count}/{_N_RUNS} runs fully clean "
        f"on all {len(check_keys)} checks.**\n"
    )

    if case == "B":
        lines.append("### Case B Jupiter flag (loud)\n")
        lines.append(
            "'jupiter_literal_present' is EXPECTED true (heart.origin is still "
            "finger_of_Jupiter, so HL_002 legitimately mentions Jupiter, and "
            "H_027 was gated out so it never reaches the model at all). "
            "'jupiter_absent' (graded above) is scoped to HEAD-tagged content "
            "only: no fired quote from a head-tagged rule contains 'jupiter', "
            "and no sentence in combined_reading ties 'head' and 'jupiter' "
            "together. Since H_027 is not even a candidate this run, any "
            "head-Jupiter claim here would be a pure hallucination, not a "
            "misapplied-but-real citation.\n"
        )
        lines.append("| run | jupiter_literal_present | head_jupiter_claim (FABRICATION) |")
        lines.append("|---|---|---|")
        any_head_jupiter_claim = False
        for i, r in enumerate(run_results, start=1):
            if r.get("error"):
                lines.append(f"| {i} | ERROR | ERROR |")
                continue
            if r["head_jupiter_claim"]:
                any_head_jupiter_claim = True
            lines.append(f"| {i} | {r['jupiter_literal_present']} | {r['head_jupiter_claim']} |")
        lines.append("")
        if any_head_jupiter_claim:
            lines.append("**⚠ FLAG: at least one Case B run asserted a head-line Jupiter-origin claim.**\n")
        else:
            lines.append("No Case B run asserted a head-line Jupiter-origin claim.\n")

    lines.append(f"### Case {case} raw per-run detail\n")
    for i, r in enumerate(run_results, start=1):
        lines.append(f"#### Run {i}")
        if r.get("error"):
            lines.append(f"- ERROR: {r['error']}")
        else:
            lines.append(f"- fired_ids: {r['fired_ids']}")
            lines.append(f"- unmatched_features: {r['unmatched_features']}")
            lines.append(f"- combined_reading: {r['combined_reading']!r}")
        lines.append("")

    return lines


def _format_report(
    corpus: list[dict], gates_by_case: dict[str, tuple[list[dict], list[str]]],
    results_by_case: dict[str, list[dict]],
) -> str:
    lines = []
    lines.append("# Latest Run: palm LLM-select smoke test — deterministic gate, Case A vs Case B\n")
    lines.append(f"Model: {_MODEL}, temperature={_TEMPERATURE}, runs per case={_N_RUNS}\n")
    lines.append("## Full rule corpus (pre-gate)\n")
    lines.append("| id | involves | page |")
    lines.append("|---|---|---|")
    for rule in corpus:
        lines.append(f"| {rule['id']} | {','.join(rule['involves'])} | {rule['page']} |")
    lines.append("")
    lines.append("## Hard-prerequisite gate (in-file, H_027/H_002 only)\n")
    lines.append("- H_027 requires head.origin includes 'Jupiter'")
    lines.append("- H_002 requires head.origin == 'touching_life'")
    lines.append("- All other rules have no prerequisite and always pass through.\n")

    for case in ("A", "B"):
        filtered_corpus, gated_out = gates_by_case[case]
        candidate_ids = [r["id"] for r in filtered_corpus]
        lines.extend(_format_case_section(
            case, _HAND_STATES[case], gated_out, candidate_ids, results_by_case[case],
        ))

    return "\n".join(lines)


def main() -> None:
    corpus = load_rule_corpus()

    client = OpenAI()
    gates_by_case: dict[str, tuple[list[dict], list[str]]] = {}
    results_by_case: dict[str, list[dict]] = {}
    for case in ("A", "B"):
        hand_state = _HAND_STATES[case]
        filtered_corpus, gated_out = _apply_gate(corpus, hand_state)
        gates_by_case[case] = (filtered_corpus, gated_out)
        filtered_corpus_by_id = {rule["id"]: rule for rule in filtered_corpus}
        print(f"case {case}: gated out {gated_out}, candidates {[r['id'] for r in filtered_corpus]}")

        user_prompt = _build_user_prompt(filtered_corpus, hand_state)
        run_results = []
        for i in range(1, _N_RUNS + 1):
            try:
                raw = _call_llm(client, user_prompt)
                parsed = json.loads(raw)
                result = _check_run(parsed, filtered_corpus_by_id, case, gated_out)
            except Exception as exc:  # noqa: BLE001 -- record and continue, per task spec
                result = {"error": f"{type(exc).__name__}: {exc}"}
            run_results.append(result)
            print(f"case {case} run {i}: {result}")
        results_by_case[case] = run_results

    report = _format_report(corpus, gates_by_case, results_by_case)
    _REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(_REPORT_PATH, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"\nWrote report to {_REPORT_PATH}")


if __name__ == "__main__":
    main()
