"""OFFLINE probe ($0, no OpenAI): the COMPUTED TIMING RANKING Q4 fed the interpreter.

DECISION THIS SERVES: Terra called the strongest relationship window Feb-Jul 2028;
luna called it late-Feb-mid-2027. Both read the SAME rendered ranking block. This
prints that block verbatim (plus every scored window and the significators/houses
behind each) so we can see which window the ranker actually ranks top for the Q4
house set -- i.e. which model reported the fact block faithfully. No model is called.

    python scripts/probe_q4_timing_ranking.py
"""
from __future__ import annotations

import datetime
import os
import shutil
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)
sys.path.insert(0, os.path.join(_ROOT, "scripts"))

from expert_pilot import SULABH  # noqa: E402
from agent.chart_calculator import calculate_chart  # noqa: E402
from agent.astro.static_facts import build_static_facts  # noqa: E402
from agent.astro import timing_ranker, house_roles  # noqa: E402

# Q4 plan, reused verbatim from the 11 Nov key (domains + houses the planner emitted).
DOMAINS = ["career", "marriage", "health", "timing_dasha"]
HOUSES = [1, 6, 7, 10, 11]


def main() -> int:
    chart_facts = build_static_facts(calculate_chart(*SULABH))
    weights = house_roles.weighted_targets(DOMAINS, HOUSES)
    ranking = timing_ranker.build_timing_ranking(chart_facts, weights)

    out = ["# Q4 timing-ranking probe (offline, $0 -- no model called)", "",
           f"target weights (house: weight): {weights}",
           f"scored houses (weight>0): {ranking.get('target_houses')}",
           f"five_year_window: {ranking.get('five_year_window')}",
           f"lifetime_peak: {ranking.get('lifetime_peak')}",
           f"horizon_end: {ranking.get('horizon_end')}", "",
           "ALL SCORED WINDOWS (highest first -- the exact list both models read):"]
    for w in ranking.get("windows", []):
        out.append(f"  {w.get('md_lord')}-{w.get('ad_lord')}  "
                   f"{w.get('start')} -> {w.get('end')}  "
                   f"phase={w.get('phase')}  score={w.get('score')}")
        out.append(f"      why: {w.get('why')}")
    out += ["", "=== RENDERED FACT-BLOCK TEXT (verbatim, as fed to the interpreter) ===",
            "", timing_ranker.render_ranking(ranking)]

    text = "\n".join(out)
    print(text)
    runs = os.path.join(_ROOT, "diagnostics", "runs")
    os.makedirs(runs, exist_ok=True)
    ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = os.path.join(runs, f"{ts}_q4_timing_probe.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write(text + "\n")
    shutil.copyfile(path, os.path.join(_ROOT, "diagnostics", "latest_run.md"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
