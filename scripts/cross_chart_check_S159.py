"""S159 Part B -- CROSS-CHART ANSWER CHECK (Sheridan, David, Surbhi).

LIVE OpenAI. Exactly 15 planner + 15 interpreter calls (3 charts x 5 questions,
each answer_question = 1 planner call + 1 interpreter call in expert mode; the
composer/silence-gate LLM paths do not run in expert mode). One retry per failure.
NO other live call: geocoding is served from tests/fixtures/geocoded_locations.json
(the same fixture conftest uses), so no live Nominatim lookup is made.

WHAT THIS IS. The 39 Oct-Nov captures are all Sulabh's chart and expert_pilot.py
is hard-wired to it (handover S159). This runs the PRODUCTION answer path on the
other three reference charts to surface crashes, refusals, wrong hard facts, zone
handling for non-India births (Durban/London -> Part A birthplace fallback), and
wording rules. It does NOT judge whether the astrology is good (nobody on the
project can -- handover).

PATH. Exactly what frontend/app.py does: calculate_chart() -> build_static_facts()
-> answer_question(expert=True, history=None, birth_time_confident=False,
display_tz=None). display_tz=None exercises Part A's birthplace-zone fallback for
the dated (muhurta) question, which is the non-India zone handling this part checks.
NO edits under agent/ or frontend/.

OUTPUT. diagnostics/runs/<UTC>_cross_chart.md -- per question: plan, model, tokens,
seconds, warnings, refused/errored + reason, and the answer as the user sees it
(answer_view.render_user_answer). The mechanical MATCH/MISMATCH checks against each
chart's oracles are done SEPARATELY (by the design session reading this output),
not here.

PRIVACY. The output holds real charts -> diagnostics/runs/*_cross_chart.md is
gitignored (added S159). Confirm before running that `git check-ignore` matches it.

RUN (on a machine with OpenAI access + swisseph + the corpus):
    python scripts/cross_chart_check_S159.py
"""
from __future__ import annotations

import datetime as _dt
import json
import logging
import os
import sys
import time
import warnings
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
os.chdir(_REPO_ROOT)  # so relative data/corpus paths resolve as in production

# --- geocoding: serve from the captured fixture, no live Nominatim call --------
# Mirrors tests/conftest.py so the only live calls are the 15 + 15 OpenAI ones.
from geopy.location import Location
import agent.chart_calculator as _cc

_FIXTURE = json.loads(
    (_REPO_ROOT / "tests" / "fixtures" / "geocoded_locations.json").read_text("utf-8"))


class _FixtureNominatim:
    def __init__(self, *a, **k):
        pass

    def geocode(self, query, *, exactly_one=True, timeout=None, **k):
        d = _FIXTURE[query]  # KeyError here = a place not in the fixture: add it first
        loc = Location(d["address"], (d["latitude"], d["longitude"], 0), d["raw"])
        return loc if exactly_one else [loc]


_cc.Nominatim = _FixtureNominatim

from agent.chart_calculator import calculate_chart
from agent.astro.static_facts import build_static_facts
from agent.astro.pipeline import answer_question
from agent.astro import answer_view

# --- the matrix (canonical calculate_chart inputs, from the oracle fixtures) ----
CHARTS = [
    ("Sheridan", "27 May 1984", "08:00", "Durban, South Africa"),
    ("David",    "19 Jan 1976", "22:00", "London, UK"),
    ("Surbhi",   "11 Sep 1992", "10:30", "Patna, India"),
]

QUESTIONS = [
    "Give me the big picture of my life and how the next few years look",
    "When will things get better for my career / money?",
    "What does my chart say about marriage?",
    "Will I own my own house?",
    "good date to start something important in the next few months?",
]


class _WarnCollector(logging.Handler):
    """Collect WARNING+ log records emitted during one answer."""
    def __init__(self):
        super().__init__(level=logging.WARNING)
        self.records: list[str] = []

    def emit(self, record):
        try:
            self.records.append(f"{record.name}: {record.getMessage()}")
        except Exception:  # noqa: BLE001 -- logging must never break the run
            pass


def _plan_summary(plan) -> str:
    try:
        return (f"domains={list(getattr(plan, 'domains', []) or [])}, "
                f"houses={list(getattr(plan, 'houses', []) or [])}, "
                f"time_scope={getattr(plan, 'time_scope', '?')}, "
                f"capabilities={list(getattr(plan, 'capabilities', []) or [])}, "
                f"in_scope={getattr(plan, 'in_scope', '?')}, "
                f"source={getattr(plan, 'source', '?')}")
    except Exception as e:  # noqa: BLE001
        return f"(plan unreadable: {e})"


def _answer_once(cf, chart, q):
    """One production answer. Returns (result_dict | None, error_str | None)."""
    try:
        return answer_question(
            q, cf, chart=chart, history=None,
            expert=True, birth_time_confident=False, display_tz=None), None
    except Exception as e:  # noqa: BLE001 -- recorded; one retry handled by caller
        return None, f"{type(e).__name__}: {e}"


def run() -> Path:
    out_dir = _REPO_ROOT / "diagnostics" / "runs"
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = _dt.datetime.now(_dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_path = out_dir / f"{stamp}_cross_chart.md"

    root_logger = logging.getLogger()
    blocks: list[str] = [
        f"# S159 Part B -- cross-chart answer check\n",
        f"- ran (UTC): {stamp}\n"
        f"- path: production (calculate_chart -> build_static_facts -> "
        f"answer_question), expert mode, no history, birth time APPROXIMATE "
        f"(KP excluded), display_tz=None (birthplace-zone fallback)\n"
        f"- charts: {', '.join(c[0] for c in CHARTS)} | questions per chart: "
        f"{len(QUESTIONS)}\n"
        f"- expected live calls: {len(CHARTS) * len(QUESTIONS)} planner + "
        f"{len(CHARTS) * len(QUESTIONS)} interpreter\n",
    ]

    for name, dob, tob, place in CHARTS:
        print(f"\n=== {name} ({dob} {tob}, {place}) ===", file=sys.stderr)
        blocks.append(f"\n---\n\n## {name} ({dob} {tob}, {place})\n")
        try:
            chart = calculate_chart(name, dob, tob, place)
            cf = build_static_facts(chart)
        except Exception as e:  # noqa: BLE001 -- a chart that will not build is a finding
            blocks.append(f"\n**CHART BUILD FAILED: {type(e).__name__}: {e}** "
                          f"-- all {len(QUESTIONS)} questions skipped for this chart.\n")
            print(f"  CHART BUILD FAILED: {e}", file=sys.stderr)
            continue

        for i, q in enumerate(QUESTIONS, 1):
            collector = _WarnCollector()
            root_logger.addHandler(collector)
            t0 = time.perf_counter()
            with warnings.catch_warnings(record=True) as pywarns:
                warnings.simplefilter("always")
                res, err = _answer_once(cf, chart, q)
                if err is not None:                      # one retry per failure
                    print(f"  Q{i} failed ({err}); retrying once", file=sys.stderr)
                    res, err = _answer_once(cf, chart, q)
            secs = round(time.perf_counter() - t0, 1)
            root_logger.removeHandler(collector)

            warn_lines = list(collector.records) + [
                f"pywarn: {w.category.__name__}: {w.message}" for w in pywarns]

            blocks.append(f"\n### Q{i}. {q}\n")
            if res is None:
                blocks.append(f"- **ERRORED (after one retry): {err}**\n")
                print(f"  Q{i}: ERRORED {err}", file=sys.stderr)
                if warn_lines:
                    blocks.append("- warnings:\n" + "\n".join(f"  - {w}" for w in warn_lines) + "\n")
                continue

            plan = res.get("plan")
            refused = bool(res.get("refused"))
            reason = res.get("reason") or res.get("refusal_reason") or ""
            try:
                shown = answer_view.render_user_answer(res)
            except Exception as e:  # noqa: BLE001
                shown = f"(render_user_answer failed: {type(e).__name__}: {e})\n\nraw answer:\n{res.get('answer')}"

            blocks.append(
                f"- plan: {_plan_summary(plan)}\n"
                f"- model: {res.get('model')} | tokens(approx payload): {res.get('tokens')} "
                f"| seconds: {secs}\n"
                f"- refused/errored: {'YES -- ' + reason if refused else 'no'}\n"
                f"- warnings: {'none' if not warn_lines else ''}\n"
            )
            if warn_lines:
                blocks.append("\n".join(f"  - {w}" for w in warn_lines) + "\n")
            blocks.append(f"\n**Answer as the user sees it:**\n\n{shown}\n")
            print(f"  Q{i}: ok model={res.get('model')} tokens={res.get('tokens')} "
                  f"secs={secs} refused={refused}", file=sys.stderr)

    out_path.write_text("".join(blocks), encoding="utf-8")
    print(f"\n[cross-chart] written -> {out_path}", file=sys.stderr)
    print(str(out_path))
    return out_path


if __name__ == "__main__":
    run()
