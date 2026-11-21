"""S160 A2 -- LIVE A/B routing probe for the dasha_lookup capability.

TRUST GATE (not a pytest). Sends 6 LAYMAN questions through the REAL planner (live
gpt-4o via planner._default_llm) and checks, DETERMINISTICALLY in Python, that each
routes correctly. Real users ask layman questions, NOT dasha jargon -- the probe
mirrors that, with ONE explicit-term lookup for the power-user case.

Minimum set: 6 calls, each covering a DISTINCT routing boundary (WS#3, no filler):
  L1  plain lookup fires                         -> dasha_lookup, domains == []
  L2  "how long until my period changes"         -> HARD: 'when'-shaped but a LOOKUP
  L3  explicit "current mahadasha"               -> explicit-term lookup still routes
  P1  "when will I get married"                  -> prediction stays corpus (timing_dasha)
  P2  "when will my career take off"             -> HARD: layman prediction, no dasha word
  R1  "what's going on in my life right now"     -> TRAP: vague reading must NOT be yanked

No anchored judgment (WS#9): the LLM plans independently; Python compares the plan to
the expected route.

RUN (live -- needs OPENAI_API_KEY; 6 planner calls, gpt-4o):
    python -m scripts.probe_dasha_routing_S160
Output -> diagnostics/latest_run.md (truncated first, overwrite-only per the convention).
"""
from __future__ import annotations

import os
import sys
import traceback

from agent.astro import planner

# (id, question, expected_route). expected_route in {"lookup","prediction","reading"}.
PROBES = [
    # -- LOOKUPS (expect computed-only: dasha_lookup, domains == []) -------------
    ("L1", "Which planet's period am I going through right now?", "lookup"),
    ("L2", "How long until my current period changes?", "lookup"),   # HARD: 'when'-shaped, still a lookup
    ("L3", "What's my current mahadasha?", "lookup"),                # explicit term (power user)
    # -- PREDICTIONS (expect corpus: timing_dasha, NO dasha_lookup) --------------
    ("P1", "When will I get married?", "prediction"),
    ("P2", "When will my career finally take off?", "prediction"),   # HARD: layman, no dasha word
    # -- VAGUE READING (the trap: must NOT become a bare lookup) -----------------
    ("R1", "What's going on in my life right now?", "reading"),
]


def _route_ok(expected: str, domains: list[str], caps: list[str]) -> bool:
    has_dl = "dasha_lookup" in caps
    if expected == "lookup":
        return has_dl and domains == []
    if expected == "prediction":
        return (not has_dl) and ("timing_dasha" in domains)
    if expected == "reading":
        return (not has_dl) and bool(domains)
    return False


def main() -> int:
    rows = []
    fails = 0
    pred_read_fail = 0  # the quality-regression class (P*/R*), tracked separately
    for pid, q, expected in PROBES:
        try:
            plan = planner.plan_question(q)
            domains = list(plan.domains or [])
            caps = list(plan.capabilities or [])
            ok = _route_ok(expected, domains, caps)
            if not ok:
                fails += 1
                if expected in ("prediction", "reading"):
                    pred_read_fail += 1
            rows.append((pid, expected, q, domains, caps, plan.time_scope,
                         plan.in_scope, "PASS" if ok else "FAIL"))
        except Exception as e:  # a planner failure is itself a FAIL, logged
            fails += 1
            pred_read_fail += 1
            rows.append((pid, expected, q, ["<error>"], [repr(e)], "", "", "FAIL"))
            traceback.print_exc()

    ship = "SHIP" if pred_read_fail == 0 else "DO NOT SHIP -- revert"
    lines = [
        "# S160 A2 -- dasha_lookup live routing probe",
        "",
        f"**{len(PROBES) - fails}/{len(PROBES)} PASS** (planner=gpt-4o live, temp=0). "
        f"Quality-regression rows (P*/R*) failing: **{pred_read_fail}** -> **{ship}**.",
        "",
        "| id | expect | route | domains | capabilities | time_scope | in_scope | question |",
        "|----|--------|-------|---------|--------------|-----------|----------|----------|",
    ]
    for pid, expected, q, domains, caps, ts, insc, verdict in rows:
        lines.append(
            f"| {pid} | {expected} | **{verdict}** | {domains} | {caps} | {ts} | "
            f"{insc} | {q} |"
        )
    lines += [
        "",
        "## Decision rule",
        "- **P1/P2/R1 FAIL = silent quality regression** (prediction or vague reading "
        "misrouted to the bare lookup, losing corpus doctrine + timing_ranker). ANY "
        "such fail => `git checkout -- ` the three files; the carve-out wording needs work.",
        "- **L1/L2/L3 FAIL = the optimization did not fire** (lookup still took the "
        "corpus path). Costs tokens, NOT quality -- acceptable to ship, worth a note.",
        "- gpt-4o at temp 0 is not fully deterministic on borderline items; re-run a "
        "lone flip once before treating it as a verdict (S123 variance posture).",
    ]
    report = "\n".join(lines) + "\n"

    os.makedirs("diagnostics", exist_ok=True)
    with open("diagnostics/latest_run.md", "w", encoding="utf-8") as fh:
        fh.write(report)

    print(report)
    print(f"\n[probe] diagnostics/latest_run.md -- {len(PROBES) - fails}/{len(PROBES)} "
          f"PASS; quality-regression fails={pred_read_fail}")
    return 1 if pred_read_fail else 0


if __name__ == "__main__":
    sys.exit(main())
