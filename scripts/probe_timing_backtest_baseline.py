"""OFFLINE baseline back-test ($0, no OpenAI): how the CURRENT timing scorer
ranks the dasha window that actually contains each of Sulabh's dated life events.

DECISION THIS SERVES: item-1 (finer timing score) is blind without a before/after
yardstick. This is the BEFORE. It calls the UNCHANGED timing_ranker on Sulabh's
chart, once per event's domain-house set, and for each event reports:
  - the antardasha window that CONTAINS the event date (found from the dasha tree,
    so a window the ranker DROPPED at score 0 is still detected and flagged),
  - that window's score and its RANK in the full domain ranking,
  - the TIE-CLUSTER size at that score (how many windows share it) -- the coarse-
    ness item 1 must reduce,
  - the current #1 window for the domain, for contrast.

Events are a CHECK, never a tuning target: no weight is read from this output.
Marriage Dec-2019 is the design-fit window (S144) -- a regression anchor only,
not evidence of generalisation. Kid Feb-2027 is a forward/expected date, not a
verified outcome -- read it as weak.

    python scripts/probe_timing_backtest_baseline.py
"""
from __future__ import annotations

import datetime as _dt
import os
import shutil
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)
sys.path.insert(0, os.path.join(_ROOT, "scripts"))

from expert_pilot import SULABH  # noqa: E402
from agent.chart_calculator import calculate_chart  # noqa: E402
from agent.astro.static_facts import build_static_facts  # noqa: E402
from agent.astro import timing_ranker  # noqa: E402  (UNCHANGED -- read only)

_WINDOW_DATE_FMT = "%d %b %Y"  # the dasha tree's human format, e.g. "28 Jan 2018"

# Per-event target houses = classical rulerships, matching what the planner emits.
# house_roles only role-weights MARRIAGE (promotion {2,7,11}=1, negation {1,6,10}=0,
# obstacle {8}=0); every set below is promotion-only, so a flat 1.0-weight list is
# byte-identical to house_roles here -- no need to route through it.
EVENTS = [
    # name,                     event date,       domain,        target houses
    ("First job",              "2012-02-01", "career",             [2, 10, 6, 11]),
    ("Back to India",          "2021-11-01", "relocation/foreign", [3, 9, 12, 7]),
    ("First flat (registration)", "2022-07-01", "property/wealth", [4, 2, 11]),
    ("Pashmina flat",          "2024-06-01", "property/wealth",    [4, 2, 11]),
    ("Back to Dubai",          "2025-02-01", "relocation/foreign", [3, 9, 12, 7]),
    ("Marriage [ANCHOR/design-fit]", "2019-12-01", "marriage",     [7, 2, 11]),
    ("First Dubai [= marriage window]", "2019-12-01", "relocation/foreign", [3, 9, 12, 7]),
    ("First kid [FORWARD/weak]", "2027-02-01", "children",         [5, 2, 11]),
]


def _parse(s):
    try:
        return _dt.datetime.strptime(str(s).strip(), _WINDOW_DATE_FMT).date()
    except (ValueError, TypeError):
        return None


def _iter_antardashas(chart_facts):
    """Yield (md_lord, ad_lord, start_str, start_date, end_date) for every AD in
    the tree -- the authoritative list, independent of what the ranker scored."""
    tree = ((chart_facts.get("dasha_periods") or {}).get("mahadasha_tree")) or []
    for node in tree:
        if not isinstance(node, dict):
            continue
        md = (node.get("mahadasha") or {}).get("lord")
        for ad in node.get("antardashas") or []:
            if not isinstance(ad, dict):
                continue
            yield (md, ad.get("lord"), ad.get("start"),
                   _parse(ad.get("start")), _parse(ad.get("end")))


def _containing_ad(chart_facts, event_date):
    """The AD whose [start, end] contains event_date; None if none matches."""
    for md, ad, start_s, start_d, end_d in _iter_antardashas(chart_facts):
        if start_d is None:
            continue
        if start_d <= event_date and (end_d is None or event_date <= end_d):
            return (md, ad, start_s)
    return None


def _ranking(chart_facts, houses, *, tiered):
    """build_timing_ranking's windows with KP tiers ON (tiered) or STRIPPED (the
    flat pre-S161 baseline). Flat = same facts minus planet_signification_tiers,
    which makes the ranker weight every significator house 1.0 (byte-identical to
    the old model) -- so the ONLY difference between the two columns is item 1."""
    if tiered:
        cf = chart_facts
    else:
        kp = dict(chart_facts.get("kp_planet_significations") or {})
        kp.pop("planet_signification_tiers", None)
        cf = dict(chart_facts, kp_planet_significations=kp)
    return (timing_ranker.build_timing_ranking(cf, houses) or {}).get("windows") or []


def _locate(windows, md, ad, start_s):
    """(rank_1based, score, tie_count) of the true window, or (None, 0.0, None) if
    the ranker dropped it (scored 0 toward the target)."""
    idx = next((i for i, w in enumerate(windows)
                if w.get("md_lord") == md and w.get("ad_lord") == ad
                and w.get("start") == start_s), None)
    if idx is None:
        return None, 0.0, None
    score = windows[idx]["score"]
    tie = sum(1 for x in windows if x["score"] == score)
    return idx + 1, score, tie


def _inhorizon(windows, event_date, md, ad, start_s):
    """(rank, N) of the true window among windows overlapping [event_date, +5y] --
    the set a contemporaneous user would actually be shown. This removes the W_RET
    penalty whereby a far-future Saturn return outscores a near-term window on the
    FULL lifetime list but would never appear in the user's answer."""
    horizon_end = timing_ranker._plus_years(
        event_date, timing_ranker.FIVE_YEAR_HORIZON_YEARS)
    inh = [w for w in windows
           if timing_ranker._overlaps_horizon(w, event_date, horizon_end)]
    idx = next((i for i, w in enumerate(inh)
                if w.get("md_lord") == md and w.get("ad_lord") == ad
                and w.get("start") == start_s), None)
    return (idx + 1 if idx is not None else None), len(inh)


def _analyse(chart_facts, name, date_iso, domain, houses):
    event_date = _dt.date.fromisoformat(date_iso)
    flat = _ranking(chart_facts, houses, tiered=False)
    tiered = _ranking(chart_facts, houses, tiered=True)
    lines = [f"### {name}  ({date_iso}) -- {domain}  houses {houses}"]

    if not tiered:
        lines.append("  ranking EMPTY for this domain (no window scored > 0).")
        return "\n".join(lines), None

    target = _containing_ad(chart_facts, event_date)
    if target is None:
        lines.append("  true window: NOT FOUND in dasha tree (date out of range?).")
        return "\n".join(lines), None
    md, ad, start_s = target

    f_rank, f_score, f_tie = _locate(flat, md, ad, start_s)
    t_rank, t_score, t_tie = _locate(tiered, md, ad, start_s)
    f_ih, f_nh = _inhorizon(flat, event_date, md, ad, start_s)
    t_ih, t_nh = _inhorizon(tiered, event_date, md, ad, start_s)

    def _r(x):
        return "DROP" if x is None else str(x)

    lines.append(f"  true window: {md}-{ad} ({start_s})")
    lines.append(f"    FLAT   : score {f_score}  full-rank {_r(f_rank)}/{len(flat)}  "
                 f"tie {f_tie if f_tie is not None else '-'}  "
                 f"in-horizon {_r(f_ih)}/{f_nh}")
    lines.append(f"    TIERED : score {t_score}  full-rank {_r(t_rank)}/{len(tiered)}  "
                 f"tie {t_tie if t_tie is not None else '-'}  "
                 f"in-horizon {_r(t_ih)}/{t_nh}")
    tw = next((w for w in tiered if w.get("md_lord") == md
               and w.get("ad_lord") == ad and w.get("start") == start_s), None)
    if tw:
        lines.append(f"     why: {tw.get('why')}")
    return "\n".join(lines), {
        "name": name, "window": f"{md}-{ad} {start_s}",
        "f_score": f_score, "t_score": t_score,
        "f_rank": f_rank, "t_rank": t_rank, "fn": len(flat), "tn": len(tiered),
        "f_tie": f_tie, "t_tie": t_tie,
        "f_ih": f_ih, "t_ih": t_ih, "f_nh": f_nh, "t_nh": t_nh,
    }


def main() -> int:
    try:
        chart_facts = build_static_facts(calculate_chart(*SULABH))
    except Exception as e:  # fail loud: without a chart there is no baseline
        print(f"FATAL: could not build chart_facts: {type(e).__name__}: {e}")
        return 1

    out = ["# Timing scorer back-test: FLAT (current) vs TIERED (KP-hierarchy, S161)",
           "# Offline, $0, NO OpenAI. Events are a CHECK, not a tuning target.",
           "# Marriage Dec-2019 = design-fit anchor (n/a). Kid Feb-2027 = forward/weak.",
           "# Success = the true window's rank IMPROVES (esp. in-horizon) and its tie",
           "# SHRINKS under TIERED -- NOT 'everything -> rank 1'.",
           ""]
    rows = []
    for name, date_iso, domain, houses in EVENTS:
        try:
            block, row = _analyse(chart_facts, name, date_iso, domain, houses)
        except Exception as e:  # one event must never kill the rest
            block, row = f"### {name}  ({date_iso}) -- ERROR {type(e).__name__}: {e}", None
        out.append(block)
        out.append("")
        if row:
            rows.append(row)

    out.append("## SUMMARY -- FLAT -> TIERED (lower rank + smaller tie = sharper)")
    out.append("# in-horizon = rank among windows a user AT the event date would see")
    out.append("# (the fair metric: a far-future Saturn return never reaches the answer).")
    out.append("")
    out.append("| event | true window | score F->T | full-rank F->T | "
               "tie F->T | in-horizon F->T |")
    out.append("|---|---|---|---|---|---|")

    def _c(x):
        return "DROP" if x is None else x

    for r in rows:
        out.append(
            f"| {r['name']} | {r['window']} | "
            f"{r['f_score']}->{r['t_score']} | "
            f"{_c(r['f_rank'])}/{r['fn']}->{_c(r['t_rank'])}/{r['tn']} | "
            f"{_c(r['f_tie'])}->{_c(r['t_tie'])} | "
            f"{_c(r['f_ih'])}/{r['f_nh']}->{_c(r['t_ih'])}/{r['t_nh']} |")

    text = "\n".join(out)
    print(text)

    runs = os.path.join(_ROOT, "diagnostics", "runs")
    os.makedirs(runs, exist_ok=True)
    ts = _dt.datetime.now(_dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = os.path.join(runs, f"{ts}_timing_backtest_flat_vs_tiered.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write(text + "\n")
    shutil.copyfile(path, os.path.join(_ROOT, "diagnostics", "latest_run.md"))
    print(f"\n[written: {path}  + diagnostics/latest_run.md]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
