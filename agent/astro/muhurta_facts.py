"""Astro Agent -- MUHURTA FACTS composer (Path B, S147).

Makes muhurta (electional timing) answerable on the live interpreter path,
integrated as a NEW FACT CLASS -- not a separate deterministic panel (that was
Option A; superseded S147 in favour of Path-B integration so the planner reads
intent and a MIXED natal+muhurta question is answered in one pass).

CONTRACT (locked S147, Sulabh):
  - The planner decides the horizon from the user's own words and emits EITHER a
    day span (horizon_days, capped) OR a target count of dates (want_count). No
    enumerated phrase list -- free-form interpretation is the planner's job;
    this module is the deterministic engine.
  - Scan is bounded by max_days (730 = 2y safety ceiling): a 1-2 year ask is
    legitimate electional planning, but the scan never runs unbounded. The
    ceiling is a runaway guard, NOT a user-facing limit.
  - ALWAYS returns, for any horizon: the ranked favourable windows, the single
    BEST window, and the EARLIEST GOOD window (they routinely diverge -- the
    best date may be a year out while a strong one is next month). Empty ->
    honest "no good dates" (the caller names the span actually searched, from
    the `searched` block -- never a hardcoded "2 years").
  - Scope = GENERIC favourability only (Chandrabala + Tarabala + Panchaka from
    muhurta_scorer, plus the panchanga-shuddhi limbs). Event-specific muhurta
    (marriage/travel doshas) stays Tier B. Predictive "when will X happen" is
    the timing ranker's job, never this.

MECHANISM:
  - REUSES find_muhurta_windows() UNCHANGED (muhurta_scorer.py) -> the S64
    goldens stay byte-pinned; this module never edits the scorer.
  - Overlays the panchanga limbs by calling score_panchanga_muhurta() at each
    window's MIDPOINT. KNOWN IMPRECISION (flagged, by design for V1): the
    scorer's windows are constant in Chandrabala/Tarabala/Panchaka but NOT in
    tithi/yoga/karana, so a window spanning a tithi/karana flip reports its
    midpoint's panchanga limb. Panchanga is WARNING-ONLY here -- it never
    changes the S64 tier -- so the imprecision annotates, it does not mis-rank.
    Boundary-exact panchanga (adding limb transitions to the refinement set) is
    a V1.1 upgrade.

TIER HANDLING (flagged judgment call, S147):
  - TIER_1 (both scored limbs favourable, no Panchaka) = "auspicious".
  - TIER_2 (one limb favourable) = "acceptable", surfaced but ranked below
    TIER_1 so the answer never overstates a mediocre muhurta as clearly good.
  - none_found fires when NEITHER a TIER_1 nor a TIER_2 window exists in the
    searched span -> the honest "no good dates" message.

WALL-CLOCK: start_jd is a REQUIRED parameter (the caller passes "now"); this
module never reads a clock itself, so its selection logic is reproducible and
its tests pin a fixed start_jd.

FAIL-SOFT: any failure costs the muhurta facts, never the answer -- returns {}.

Python 3.11.
"""
from __future__ import annotations

import logging

import swisseph as swe

from agent.calculations.transits.muhurta_scorer import find_muhurta_windows
from agent.calculations.transits.panchanga_muhurta import score_panchanga_muhurta
from agent.chart_calculator import NAKSHATRAS, SIGNS

logger = logging.getLogger(__name__)

__all__ = ["build_muhurta_facts"]

MAX_SCAN_DAYS = 730.0                       # 2-year runaway ceiling (locked S147)
DEFAULT_TOP_N = 8                           # render cap for days-mode ranking

_FAVOURABLE = ("TIER_1", "TIER_2")
_TIER_RANK = {"TIER_1": 0, "TIER_2": 1, "TIER_3": 2}   # lower = better


def _jd_to_iso(jd: float) -> str:
    """Julian Day (UT) -> 'YYYY-MM-DD HH:MM UT' for the fact block.

    Done here (the composer already depends on swisseph) so pipeline._fact_block
    stays pure string assembly and the interpreter is handed calendar dates, not
    raw Julian Days.
    """
    y, m, d, h = swe.revjul(jd, swe.GREG_CAL)
    hh = int(h)
    mm = int(round((h - hh) * 60))
    if mm == 60:
        hh, mm = hh + 1, 0
    return f"{y:04d}-{m:02d}-{d:02d} {hh:02d}:{mm:02d} UT"


def _window_record(w) -> dict:
    """One MuhurtaWindow + its midpoint panchanga overlay -> a flat dict.

    score_panchanga_muhurta() uses swisseph; this is the ONLY swisseph touch in
    the module and is isolated here so _rank_and_select stays pure and testable
    on synthetic records.
    """
    mid = (w.start_jd + w.end_jd) / 2.0
    pm = score_panchanga_muhurta(mid)
    return {
        "start_jd": w.start_jd,
        "end_jd": w.end_jd,
        "start": _jd_to_iso(w.start_jd),             # calendar date for the fact block
        "end": _jd_to_iso(w.end_jd),
        "tier": w.tier.name,                         # "TIER_1" / "TIER_2" / "TIER_3"
        "favorable_count": w.favorable_count,        # 0-2 (Chandrabala+Tarabala)
        "chandrabala": w.chandrabala.name,
        "tarabala": w.tarabala.name,
        "panchaka": w.panchaka.name,
        "tithi": pm.tithi,
        "yoga": pm.yoga,
        "karana": pm.karana,
        "panchanga_avoid_count": pm.avoid_count,     # 0-3 (tithi/yoga/karana 'avoid')
        "warnings": tuple(w.warnings) + tuple(pm.warnings),
    }


def _rank_and_select(records: list[dict], *, want_count: int | None, top_n: int) -> dict:
    """Pure selection over already-built window records (no swisseph).

    Favourable = TIER_1 or TIER_2. Returns best / earliest_good / windows /
    none_found. Deterministic; unit-tested on synthetic records.
    """
    favourable = [r for r in records if r["tier"] in _FAVOURABLE]

    def rank_key(r: dict) -> tuple:
        # tier first (TIER_1 before TIER_2), then more favourable limbs, then
        # fewer panchanga 'avoid' flags, then earlier in time.
        return (_TIER_RANK[r["tier"]], -r["favorable_count"],
                r["panchanga_avoid_count"], r["start_jd"])

    by_rank = sorted(favourable, key=rank_key)
    by_time = sorted(favourable, key=lambda r: r["start_jd"])

    tier1 = [r for r in by_time if r["tier"] == "TIER_1"]
    tier2 = [r for r in by_time if r["tier"] == "TIER_2"]
    earliest_good = tier1[0] if tier1 else (tier2[0] if tier2 else None)
    best = by_rank[0] if by_rank else None

    if want_count is not None:
        windows = by_time[:want_count]      # the next N good dates, soonest first
    else:
        windows = by_rank[:top_n]           # the strongest few across the span

    return {
        "windows": windows,
        "best": best,
        "earliest_good": earliest_good,
        "none_found": not favourable,
    }


def build_muhurta_facts(
    chart: dict,
    start_jd: float,
    *,
    horizon_days: float | None = None,
    want_count: int | None = None,
    max_days: float = MAX_SCAN_DAYS,
    top_n: int = DEFAULT_TOP_N,
) -> dict:
    """Generic muhurta favourability over a bounded forward scan.

    Exactly ONE of horizon_days / want_count must be given (the planner picks
    which from the user's phrasing). The scan is capped at max_days either way.

    Args:
        chart: calculate_chart() output. Reads lagna_chart['rasi'] / ['nakshatra']
            for the natal Moon's sign (0=Aries..11) and nakshatra (0=Ashwini..26)
            -- the same Path-A derivation find_muhurta_windows expects.
        start_jd: Julian Day (UT) to scan FROM -- the caller's "now". Required;
            never read from a clock here (keeps selection reproducible).
        horizon_days: forward span in days (capped to max_days), OR
        want_count: number of good dates wanted (scan runs out to max_days).
        max_days: runaway ceiling (default 730 = 2 years, locked S147).
        top_n: render cap for the ranked list in days-mode.

    Returns:
        {} if a muhurta scan is not possible (missing/bad natal Moon, bad args,
        or the scan raised). Otherwise:
        {"searched": {"start_jd","end_jd","span_days","mode","capped"},
         "windows": [record, ...],      # ranked (days-mode) or earliest-N (count-mode)
         "best": record | None,
         "earliest_good": record | None,
         "none_found": bool}
        record = {start_jd,end_jd,tier,favorable_count,chandrabala,tarabala,
        panchaka,tithi,yoga,karana,panchanga_avoid_count,warnings}.
        Never raises.
    """
    try:
        if (horizon_days is None) == (want_count is None):
            raise ValueError("pass exactly one of horizon_days / want_count")
        if start_jd is None or start_jd <= 0:
            raise ValueError(f"start_jd must be > 0, got {start_jd}")
        if want_count is not None and want_count <= 0:
            raise ValueError(f"want_count must be > 0, got {want_count}")

        lagna = (chart or {}).get("lagna_chart") or {}
        rasi = lagna.get("rasi")
        nak = lagna.get("nakshatra")
        if rasi not in SIGNS or nak not in NAKSHATRAS:
            logger.warning("muhurta: natal Moon sign/nakshatra not resolvable")
            return {}
        natal_moon_sign = SIGNS.index(rasi)          # 0=Aries..11
        janma_nakshatra = NAKSHATRAS.index(nak)      # 0=Ashwini..26

        if want_count is not None:
            span = max_days
            capped = True
        else:
            span = min(float(horizon_days), max_days)
            capped = float(horizon_days) > max_days
        if span <= 0:
            raise ValueError(f"scan span must be > 0, got {span}")
        end_jd = start_jd + span

        raw = find_muhurta_windows(natal_moon_sign, janma_nakshatra, start_jd, end_jd)
        records = [_window_record(w) for w in raw]
        sel = _rank_and_select(records, want_count=want_count, top_n=top_n)
        sel["searched"] = {
            "start_jd": start_jd,
            "end_jd": end_jd,
            "start": _jd_to_iso(start_jd),
            "end": _jd_to_iso(end_jd),
            "span_days": span,
            "mode": "count" if want_count is not None else "days",
            "capped": capped,
        }
        return sel
    except Exception as exc:  # noqa: BLE001 -- a bad scan costs muhurta, not the answer
        logger.warning("muhurta facts unavailable: %s", exc)
        return {}
