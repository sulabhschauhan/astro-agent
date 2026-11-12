"""Astro Agent -- DISPLAY TIME ZONE for dated answers (Part A, S159).

Dated answers (muhurta windows, planetary ingress, combustion) are STORED as UT
instants and must be SHOWN in the user's own zone -- people act on a date where
they live now. Conversion happens HERE, at the point the answer text is assembled
(pipeline._fact_block), NEVER in stored/cached data: the shared sky cache and the
per-chart caches hold instants and stay zone-free (S149 two-tier rule; S157
accelerant-never-a-gate). Dasha periods and the lunar-month (masa) block are OUT
of scope by ruling (S159): dasha is unchanged; masa's date is the first sunrise
at the user's place (S148), which needs lat/lon, not just a zone.

ZONE RESOLUTION (S159 ruling): browser zone -> birthplace zone -> UT.
  1. a valid IANA name passed from the frontend (st.context.timezone), else
  2. the birthplace zone from the chart's lat/lon (timezonefinder), else
  3. "UT" (last resort; the stored '... UT' strings are left exactly as they are).

DST is correct by construction: each instant is localized with its OWN date via
zoneinfo, so a window spanning a daylight-saving change converts each end on its
own offset.

LEAF module: stdlib + a lazy timezonefinder import (only for the birthplace
fallback). Imports nothing from agent.*. Python 3.11.
"""
from __future__ import annotations

import datetime as _dt
import logging
import re
from zoneinfo import ZoneInfo

logger = logging.getLogger(__name__)

__all__ = ["UT", "resolve_display_zone", "localize_ut", "localize_dated_facts"]

UT = "UT"

# The EXACT format both composers emit (muhurta_facts/dated_facts._jd_to_iso).
# Converting is keyed on this format, so the transform is shape-agnostic: any
# string that is not a UT instant is passed through untouched.
_UT_RE = re.compile(r"^(\d{4})-(\d{2})-(\d{2}) (\d{2}):(\d{2}) UT$")

# ONLY these fact classes are localized. masa (sunrise-at-place, S148) and the
# dasha timeline are deliberately excluded (S159 ruling).
_DATED_KEYS = ("muhurta", "ingress", "combustion")


def _is_loadable(name) -> bool:
    """True if `name` is an IANA zone zoneinfo can load."""
    if not isinstance(name, str) or not name or name == UT:
        return False
    try:
        ZoneInfo(name)
        return True
    except Exception:  # noqa: BLE001 -- an unknown/garbage zone must fall through
        return False


def _birthplace_zone(lat, lon):
    """IANA zone at (lat, lon) via timezonefinder, or None. Lazy import: the
    data load is heavy and only the fallback path needs it. Never raises."""
    if lat is None or lon is None:
        return None
    try:
        from timezonefinder import TimezoneFinder
        name = TimezoneFinder().timezone_at(lat=float(lat), lng=float(lon))
        return name if _is_loadable(name) else None
    except Exception as exc:  # noqa: BLE001 -- fallback must never raise
        logger.warning("tz_display: birthplace zone lookup failed: %s", exc)
        return None


def resolve_display_zone(display_tz, lat, lon) -> str:
    """Browser zone -> birthplace zone -> UT. Returns an IANA name or 'UT'.

    `display_tz` is the frontend's best guess (st.context.timezone); it wins when
    it is a loadable IANA name. Otherwise the birthplace zone from the chart's
    lat/lon. Otherwise 'UT', which leaves the stored instants unchanged.
    """
    if _is_loadable(display_tz):
        return display_tz
    return _birthplace_zone(lat, lon) or UT


def localize_ut(value, zone) -> str:
    """Rewrite one 'YYYY-MM-DD HH:MM UT' string into `zone`, labelled with the
    zone name, e.g. '2027-06-03 03:58 (Asia/Dubai)'. A non-matching string, a
    non-string, or zone == 'UT' is returned unchanged."""
    if zone == UT or not isinstance(value, str):
        return value
    m = _UT_RE.match(value)
    if not m:
        return value
    y, mo, d, hh, mm = (int(g) for g in m.groups())
    try:
        local = _dt.datetime(y, mo, d, hh, mm, tzinfo=_dt.timezone.utc) \
            .astimezone(ZoneInfo(zone))
    except Exception:  # noqa: BLE001 -- a bad zone leaves the UT string intact
        return value
    return f"{local:%Y-%m-%d %H:%M} ({zone})"


def _localize_tree(obj, zone):
    """Recursively rewrite every UT instant string inside `obj` into `zone`."""
    if isinstance(obj, str):
        return localize_ut(obj, zone)
    if isinstance(obj, dict):
        return {k: _localize_tree(v, zone) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_localize_tree(v, zone) for v in obj]
    return obj


def localize_dated_facts(facts: dict, zone: str) -> dict:
    """Return a COPY of `facts` with the muhurta / ingress / combustion UT
    instants rewritten into `zone` (labelled). masa, the dasha timeline and
    everything else are untouched, and the input `facts` (which may be a cache
    object) is NEVER mutated -- the conversion lives only in the copy the answer
    text is written from. zone == 'UT' (or falsy) is a no-op that returns the
    SAME object, so a UT-only answer and every cache stay byte-identical.
    """
    if not zone or zone == UT or not isinstance(facts, dict):
        return facts
    out = dict(facts)
    for key in _DATED_KEYS:
        sub = facts.get(key)
        if isinstance(sub, dict):
            out[key] = _localize_tree(sub, zone)
    return out
