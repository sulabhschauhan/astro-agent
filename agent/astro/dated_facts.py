"""Astro Agent -- DATED TIMELINE FACTS dispatcher (Path B, S152).

The compose side of the S152 dated-compose socket for the TIMELINE-kind
capabilities -- ingress, combustion, masa (see capability_registry.kind).

ONE SCAN, MANY SLICES. All three capabilities are projections of the SAME sky
over the SAME window, so `build_timeline` is called EXACTLY ONCE per answer,
with a horizon wide enough for the widest capability the plan actually asked
for, and each capability then TRIMS its own slice out of the one result. This
is the whole reason the socket does not copy muhurta's one-composer-per-
capability shape (S151 finding): muhurta is a live per-question scan with its
own horizon; the timeline trio shares a single build. Scanning the sky once per
capability would be the bespoke cabling the S151 lock forbade.

SELECTION IS THE INTERPRETER'S, NOT THE PLANNER'S. These facts carry NO typed
planner param (no {planet, house}). The full trimmed set is attached to the
fact block and the interpreter picks the slice the question is about -- exactly
how every other fact class works (yogas, transits, dasha). The only dated
capability that needs a compute param is muhurta (its horizon), and that already
lives on the Plan.

HORIZON. Per-capability scan horizon (days), the MINIMUM that guarantees the
capability's answer exists in the window:
  * ingress    = 1100 (~3.01 y): Saturn is the slowest sign-changer among the
                 seven moving grahas (~2.46 y per sign), so its NEXT ingress is
                 always inside 1100 days. The lunar nodes are not scanned by the
                 engine (ingress_scan.DEFAULT_BODIES), so they set no bound.
  * combustion = 400: every taragraha is combust several times a year, so the
                 near-term window (trimmed to NEAR_COMBUSTION_DAYS below) is
                 always populated; 400 only gives the shared-cache a little reuse
                 headroom past the trim.
  * masa       = 400: the current month plus ~13 upcoming, ample for "this month
                 / next month".
The dispatcher scans at the MAX horizon over the requested capabilities, so a
plan asking only `masa` never pays for a 3-year ingress scan.

BEYOND THE HORIZON is the normal flow, not a special path: a question about a
date past the scanned window simply finds no matching event in the trimmed
facts, and the interpreter says so (its directive requires naming the window).
A truly distant ask (> ~3 y) is rare and is a future live-extend, not built here.

FAIL-SOFT, like every other fact composer on Path B: any failure costs the dated
facts, never the answer -- returns {}. Never raises.

Python 3.11.
"""
from __future__ import annotations

import datetime as _dt
import logging

import swisseph as swe

from agent.astro.build_timeline import build_timeline
from agent.chart_calculator import SIGNS

logger = logging.getLogger(__name__)

__all__ = ["build_timeline_facts", "SCAN_DAYS", "NEAR_COMBUSTION_DAYS"]

# Per-capability scan horizon in days (see module docstring for the derivation).
SCAN_DAYS: dict[str, int] = {
    "ingress": 1100,
    "combustion": 400,
    "masa": 400,
}

# Combustion is trimmed to the near term: a window that is current or begins
# within this many days. THRESHOLD (S152): 180 days is half a year, long enough
# that every taragraha has at least one combustion in view (each is combust
# ~1-3 times a year) and short enough that the fact block is not flooded with a
# year of windows. SCOPE GUARD: trimming only; the 400-day scan still bounds what
# exists. TUNING NOTE: raise toward 365 if a "later this year" combustion ask is
# observed being missed; there is no correctness risk either way, only recall.
NEAR_COMBUSTION_DAYS = 180.0


def _jd_to_iso(jd: float) -> str:
    """Julian Day (UT) -> 'YYYY-MM-DD HH:MM UT' for the fact block.

    Isolated here (this module already depends on swisseph via build_timeline)
    so pipeline._fact_block stays pure string assembly. Mirrors
    muhurta_facts._jd_to_iso rather than importing it (no cross-composer coupling).
    """
    y, m, d, h = swe.revjul(jd, swe.GREG_CAL)
    hh = int(h)
    mm = int(round((h - hh) * 60))
    if mm == 60:
        hh, mm = hh + 1, 0
    return f"{y:04d}-{m:02d}-{d:02d} {hh:02d}:{mm:02d} UT"


def _sign(idx) -> str | None:
    """Rashi index (0 = Aries) -> sign name, or None if out of range/not an int."""
    if isinstance(idx, int) and 0 <= idx < len(SIGNS):
        return SIGNS[idx]
    return None


def trim_ingress(events: list[dict]) -> dict:
    """Next sign change per moving graha, from the projected ingress events.

    `events` are build_timeline's projected ingress records (time-ordered). One
    row per body -- the earliest upcoming crossing -- since that is the "when
    does X next change sign / enter a house" the capability answers.
    """
    seen: dict[str, dict] = {}
    for e in events or []:
        body = e.get("body")
        if not body or body in seen:
            continue  # events are time-sorted, so the first seen is the earliest
        seen[body] = {
            "body": body.title(),
            "date": _jd_to_iso(e["jd"]),
            "from_sign": _sign(e.get("from_index")),
            "to_sign": _sign(e.get("to_index")),
            "to_house_from_lagna": e.get("to_house_from_lagna"),
            "to_house_from_moon": e.get("to_house_from_moon"),
            "retrograde": bool(e.get("retrograde")),
        }
    ordered = sorted(seen.values(), key=lambda r: r["date"])
    return {"events": ordered}


def trim_combustion(intervals: list[dict], now_jd: float,
                    near_days: float = NEAR_COMBUSTION_DAYS) -> dict:
    """Combustion windows that are current or begin within `near_days`."""
    out: list[dict] = []
    horizon = now_jd + near_days
    for iv in intervals or []:
        start = iv.get("start_jd")
        end = iv.get("end_jd")
        if start is None or end is None:
            continue
        if end < now_jd or start > horizon:
            continue  # already over, or too far out for "near term"
        out.append({
            "planet": iv.get("planet"),
            "start": _jd_to_iso(start),
            "end": _jd_to_iso(end),
            "ongoing": start <= now_jd <= end,
            "retrograde_at_mid": bool(iv.get("retrograde_at_mid")),
        })
    out.sort(key=lambda r: r["start"])
    return {"windows": out}


def trim_masa(months: list[dict], now_jd: float, *, upcoming: int = 2) -> dict:
    """The lunar month containing `now_jd` plus the next `upcoming` complete ones.

    A month's Sanskrit name is passed through ONLY when the engine supplied one;
    an intercalary month (sankranti_count != 1) carries name_sa=None by design
    (S148 lock) and is reported by its count, never named here.
    """
    complete = [m for m in (months or []) if m.get("complete")
                and m.get("start_jd") is not None and m.get("end_jd") is not None]
    complete.sort(key=lambda m: m["start_jd"])

    def _row(m: dict) -> dict:
        return {
            "start": _jd_to_iso(m["start_jd"]),
            "end": _jd_to_iso(m["end_jd"]),
            "sankranti_count": m.get("sankranti_count"),
            "name_sa": m.get("name_sa"),            # None for an intercalary month
            "masa_index": m.get("masa_index"),
        }

    current = None
    rest: list[dict] = []
    for m in complete:
        if m["start_jd"] <= now_jd < m["end_jd"]:
            current = _row(m)
        elif m["start_jd"] >= now_jd:
            rest.append(_row(m))
    return {"current": current, "upcoming": rest[:upcoming]}


def build_timeline_facts(chart: dict, wanted_caps, *,
                         as_of: _dt.date | None = None,
                         now_jd: float | None = None,
                         builder=build_timeline) -> dict:
    """Compose the requested TIMELINE-kind fact classes from ONE shared scan.

    Args:
        chart: calculate_chart() output. build_timeline reads only Moon longitude
            and the sidereal ascendant from it; a chart it cannot project costs
            the facts, not the answer.
        wanted_caps: iterable of timeline capability ids the plan routed
            (subset of {"ingress","combustion","masa"}). Unknown ids are ignored.
        as_of: window anchor date (default: today UTC). Injected in tests.
        now_jd: "now" for trimming current/next (default: this instant UT).
            Injected in tests so selection is reproducible.
        builder: injected for tests; defaults to build_timeline.

    Returns:
        {fact_key: slice_dict, ...} for each requested, populated capability, e.g.
        {"ingress": {"events":[...], "window":{...}}, ...}. {} when nothing could
        be built (unprojectable chart, scan error, or no recognised capability).
        Never raises.
    """
    try:
        wanted = [c for c in (wanted_caps or []) if c in SCAN_DAYS]
        if not wanted:
            return {}
        if as_of is None:
            as_of = _dt.datetime.now(_dt.timezone.utc).date()
        if now_jd is None:
            _n = _dt.datetime.now(_dt.timezone.utc)
            now_jd = swe.julday(_n.year, _n.month, _n.day,
                                _n.hour + _n.minute / 60.0 + _n.second / 3600.0)

        horizon = max(SCAN_DAYS[c] for c in wanted)
        tl = builder(chart, as_of, horizon_days=horizon)
        if not tl or not tl.get("projected"):
            logger.warning("dated_facts: timeline not projected (%s)",
                           (tl or {}).get("chart_error") or (tl or {}).get("shared_error"))
            return {}

        window = {"start": _jd_to_iso(swe.julday(as_of.year, as_of.month, as_of.day, 0.0)),
                  "end_date": tl.get("horizon_end")}

        out: dict = {}
        if "ingress" in wanted:
            slc = trim_ingress(tl.get("ingress") or [])
            if slc["events"]:
                out["ingress"] = {**slc, "window": window}
        if "combustion" in wanted:
            slc = trim_combustion(tl.get("combustion") or [], now_jd)
            if slc["windows"]:
                out["combustion"] = {**slc, "window": window}
        if "masa" in wanted:
            slc = trim_masa(tl.get("masa") or [], now_jd)
            if slc["current"] or slc["upcoming"]:
                out["masa"] = {**slc, "window": window}
        return out
    except Exception as exc:  # noqa: BLE001 -- dated facts, never the answer
        logger.warning("dated_facts unavailable: %s", exc)
        return {}
