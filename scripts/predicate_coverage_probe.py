"""SUPERSEDED S137 -- PHASE-0 SCAFFOLDING, NOT A PRODUCTION COMPONENT.

    `_HAND_TYPED` below is NOT a mapper and must never be treated as the start
    of one. There is no claim-text -> predicate lookup anywhere in this system
    and there must never be: the interpreter DECLARES each verse's condition
    itself, with the verse in front of it (see the S137 lock in CLAUDE.md).
    This table existed for ONE purpose -- to exercise the evaluators before the
    interpreter emitted anything -- and live typed output replaced it on
    2026-09-19 (`diagnostics/qa_capture/20260919T080136Z.md`, typed_coverage
    1.00).

    KEPT, NOT DELETED, deliberately: Working Style #16 requires a script whose
    numbers are cited in a decision to stay auditable, and this one's 95.7% is
    cited in SESSION_LOG S137 and in docs/ANSWER_VERIFICATION_ARCHITECTURE.md.
    Do not extend it, do not import from it, do not add rows.

PHASE 0 PROBE -- can the claims we already ship be TYPED, and does typing
them recover the insights the composer dropped?

DECISION THIS SERVES: if typed coverage >= 80% and the five wrongly-demoted
yoga claims come back SATISFIED, Phase 1 (interpreter emits `preconditions`)
is justified. Else the vocabulary is wrong and the design is re-opened.
TOKEN CEILING: none -- this makes NO model call and costs nothing to re-run.

HOW TO READ THE RESULT, AND ITS ONE HONEST LIMIT
------------------------------------------------
`_HAND_TYPED` below is the twelve claims of the live capture
`diagnostics/qa_capture/20260918T193426Z.md`, with their preconditions written
out BY HAND from each claim's own prose. In Phase 1 the INTERPRETER emits these;
here a human/agent stands in for it, so this probe measures whether the
VOCABULARY and the EVALUATORS are sufficient -- NOT whether the interpreter will
type claims correctly. That second question is Phase 1's, and it needs a live
run.

Per Working Style #5 (AI reviewing AI): this mapping has no human review yet.
Sulabh should sanity-check the twelve rows before the result is treated as
ratified. Each row carries the claim's own words so that check is quick.

Usage:  python scripts/predicate_coverage_probe.py [capture.md]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agent.astro import predicates as P  # noqa: E402

_DEFAULT_CAPTURE = (Path(__file__).resolve().parents[1]
                    / "diagnostics" / "qa_capture" / "20260918T193426Z.md")

# claim_id -> (shipped?, one-line quote, preconditions)
# "shipped" records what the LIVE composer did, so the probe can contrast.
_HAND_TYPED: dict[int, tuple[bool, str, list[dict]]] = {
    0: (True, "10th lord in the 4th -> gain through public authority",
        [{"type": "lord_in_house", "lord_of": 10, "house": 4}]),
    1: (True, "10th lord in the 4th together with the 9th lord -> fame",
        [{"type": "lord_in_house", "lord_of": 10, "house": 4},
         {"type": "lord_in_house", "lord_of": 9, "house": 4}]),
    2: (True, "10th lord strong by association with the 9th lord in the 4th",
        [{"type": "lord_in_house", "lord_of": 10, "house": 4},
         {"type": "lord_in_house", "lord_of": 9, "house": 4},
         {"type": "yoga_fired", "yoga_id": "dharma_karmadhipati"}]),
    3: (False, "ascendant lord in 5th + 5th lord in 2nd, aspecting -> Raja yoga",
        [{"type": "lord_in_house", "lord_of": 1, "house": 5},
         {"type": "lord_in_house", "lord_of": 5, "house": 2},
         {"type": "yoga_fired", "yoga_id": "kendra_trikona_1_5"}]),
    4: (False, "11th lord in the 10th from itself -> honour from rulers",
        [{"type": "lord_in_house", "lord_of": 11, "house": 10},
         {"type": "house_lord_is", "house": 11, "graha": "Venus"}]),
    5: (False, "Adhi yoga, benefics 6th/7th from the Moon -> ministerial rank",
        [{"type": "yoga_fired", "yoga_id": "adhi"}]),
    6: (False, "Vesi yoga, benefic in the 2nd from the Sun -> rise",
        [{"type": "yoga_fired", "yoga_id": "vesi"}]),
    7: (False, "Budha-Aditya, Sun and Mercury together -> authority and skill",
        [{"type": "yoga_fired", "yoga_id": "nipuna"},
         {"type": "conjunction", "grahas": ["Sun", "Mercury"]}]),
    8: (False, "benefics in angles from the ATMAKARAKA -> one becomes a king",
        # The detector's raja_sambandha_lagna keys on the AMATYAkaraka, a
        # different karaka. Honest typing: the reference frame this claim names
        # is not expressible, so it ships hedged rather than as confirmed.
        [{"type": "planet_in_house", "graha": "Jupiter", "house": 5},
         {"type": "unfittable", "note": "Atmakaraka reference frame not a fact class"}]),
    9: (False, "a planet ruling the 10th aspecting the ascendant -> Raja yoga",
        [{"type": "house_lord_is", "house": 10, "graha": "Mercury"},
         {"type": "aspects_house", "graha": "Mercury", "house": 1}]),
    10: (False, "ascendant lord in the 5th -> 1st-5th Raja yoga strength",
         [{"type": "lord_in_house", "lord_of": 1, "house": 5},
          {"type": "yoga_fired", "yoga_id": "kendra_trikona_1_5"}]),
    11: (True, "6th lord in the 6th (Harsha) -> overcoming opponents",
         [{"type": "lord_in_house", "lord_of": 6, "house": 6},
          {"type": "yoga_fired", "yoga_id": "harsha_yoga"}]),
}


def load_facts(path: Path) -> dict:
    s = path.read_text(encoding="utf-8")
    cf = s[s.index("### chart_facts"):s.index("### plan (Stage 1")]
    return json.loads(cf[cf.index("```json") + 7:cf.rindex("```")])


def main() -> int:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else _DEFAULT_CAPTURE
    facts = load_facts(path)

    results, rows = [], []
    for cid in sorted(_HAND_TYPED):
        shipped, quote, preds = _HAND_TYPED[cid]
        res = P.evaluate_claim(preds, facts)
        results.append(res)
        rows.append((cid, shipped, res["verdict"], quote, res))

    cov = P.coverage(results)

    print(f"# Phase 0 -- predicate coverage probe\n\nCapture: `{path.name}`  "
          f"({P.PREDICATE_VERSION})\n")
    print("| id | live composer | typed verdict | claim |")
    print("|---|---|---|---|")
    for cid, shipped, verdict, quote, _ in rows:
        print(f"| {cid} | {'shipped' if shipped else 'DEMOTED'} | "
              f"**{verdict}** | {quote} |")

    print(f"\n## Claim verdicts\n\n{json.dumps(cov['claim_verdicts'], indent=2)}")
    print(f"\n## Predicate verdicts\n\n{json.dumps(cov['predicate_verdicts'], indent=2)}")
    print(f"\n## Per fact class\n\n{json.dumps(cov['by_fact_class'], indent=2)}")
    print(f"\n**typed coverage = {cov['typed_coverage']:.1%}** "
          f"(predicates decided / predicates attempted)")

    # The two questions the probe exists to answer.
    recovered = [cid for cid, shipped, verdict, _, _ in rows
                 if not shipped and verdict == P.SATISFIED]
    still_dropped = [cid for cid, shipped, verdict, _, _ in rows
                     if verdict == P.CONTRADICTED]
    hedged = [cid for cid, shipped, verdict, _, _ in rows
              if verdict == P.UNEVALUABLE]
    print(f"\n## Gates\n")
    print(f"- RECOVERED (live composer demoted, typing confirms): {recovered}")
    print(f"- CORRECTLY DROPPED (chart refutes): {still_dropped}")
    print(f"- SHIPS HEDGED (unevaluable, never dropped): {hedged}")
    print(f"- typed coverage >= 80%: "
          f"{'PASS' if cov['typed_coverage'] >= 0.80 else 'FAIL'}")

    for cid, _, verdict, _, res in rows:
        if verdict != P.SATISFIED:
            for r in res["predicates"]:
                if r["verdict"] != P.SATISFIED:
                    print(f"  - claim {cid} [{r['type']}] {r['verdict']}: {r['reason']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
