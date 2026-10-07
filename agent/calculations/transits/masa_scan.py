"""Ephemeris driver for the lunar-month (masa) calendar.

Thin by design: it obtains two instant lists from the scanner and hands them to
`core/masa.build_masa_intervals`, which holds the rule. Nothing here decides
anything about calendars.

  lunations : n_divisions=2 over (moon - sun) % 360.  Crossing into index 0 is a
              new moon, into index 1 a full moon. n=2 (a 180-deg band) is used
              rather than n=30, because this module has no business producing a
              second tithi series -- `core/panchanga.py` is the sole tithi source
              and stays that way.
  sankrantis: n_divisions=12 over the Sun's sidereal longitude.

TWO THINGS THIS MODULE EXISTS TO GET RIGHT
------------------------------------------
1. OVER-SCAN AND TRIM. `scan_quantised_crossings` can only report a CHANGE of
   index, so it cannot see a crossing lying exactly at the start of its span, and
   the first/last months of any naive window are clipped. A clipped month's
   sankranti count is a count over a fragment, so a perfectly ordinary month at
   the window edge would report zero sankrantis -- indistinguishable from the real
   zero-sankranti month, and plausible enough that nobody would spot-check it.
   So both scans run over [start - MARGIN, end + MARGIN] and the result is trimmed
   back; `MasaInterval.complete` carries the guarantee.

2. THE DATE A MONTH STARTS ON IS NOT THE TIMEZONE OF ITS INSTANT. A masa begins
   at a new-moon INSTANT, which is global; but a panchanga DAY begins at SUNRISE,
   so the month's civil start date is the date of the FIRST SUNRISE AFTER that
   instant at the user's own place. Simply localising the instant is wrong for
   every lunation falling between sunrise and midnight -- the majority of them.
   `core/panchanga.py` already takes the Vedic day boundary seriously for vara;
   `resolve_local_dates` below inherits the same rule from the same function
   rather than re-deriving a weaker one.
   This is why the INSTANTS are chart- and place-independent (and cacheable once
   for every chart) while the DATES are not, and are resolved separately.

Python 3.11.
"""
from __future__ import annotations

import datetime as _dt
import logging

import swisseph as swe

from agent.calculations.core import panchanga
from agent.calculations.core.masa import (
    SYNODIC_MONTH_DAYS, MasaInterval, build_masa_intervals,
)
from agent.calculations.helpers import ephemeris
from agent.calculations.helpers.discrete_scan import scan_quantised_crossings
from agent.calculations.transits.ingress_scan import (
    AYANAMSA_NAME, MAX_ABS_SPEED_DEG_PER_DAY, scan_divisional_ingresses,
)

logger = logging.getLogger(__name__)

__all__ = ["scan_masa_calendar", "resolve_local_dates", "OVER_SCAN_DAYS",
           "ELONGATION_RATE_BOUND"]

# Over-scan margin on EACH side, days. THRESHOLD (S148): one mean synodic month
# plus a day. Justification: the longest possible clipped fragment at either edge
# is one whole lunation, so one synodic month is the minimum that guarantees the
# first and last REPORTED months are whole; the extra day absorbs the ~0.7-day
# spread between the mean synodic month and a real one (measured 29.28-29.81 d
# across 2026). SCOPE GUARD: guarantees completeness of the trimmed result only;
# it is not a claim about any month outside the requested window. TUNING NOTE: it
# costs two extra lunations of scanning and nothing else -- raise it, never lower.
OVER_SCAN_DAYS = SYNODIC_MONTH_DAYS + 1.0

# Rate bound for the ELONGATION angle (moon - sun). NOT the Moon's own bound:
# the composed angle's rate is |moon_speed - sun_speed|, so a caller passing the
# Moon's 16.0 would be passing a bound for the wrong quantity. MEASURED (S148,
# 0.25-day steps, 2010-2040): max |moon_speed - sun_speed| = 14.3885 deg/day,
# rounded up. See ingress_scan.MAX_ABS_SPEED_DEG_PER_DAY for the same discipline.
ELONGATION_RATE_BOUND = 15.0


def _elongation(jd_ut: float) -> float:
    """Moon minus Sun sidereal longitude, [0, 360). The ayanamsa cancels here --
    both terms carry it -- so this quantity is frame-independent; the SANKRANTIS
    are not, which is why the result records the ayanamsa."""
    return (ephemeris.sidereal_longitude(jd_ut, swe.MOON)
            - ephemeris.sidereal_longitude(jd_ut, swe.SUN)) % 360.0


def scan_masa_calendar(start_jd: float, end_jd: float, *,
                       tol_jd: float = 1e-6) -> dict:
    """The amanta lunar-month calendar covering [start_jd, end_jd).

    Returns:
        {
          "scanned": {start_jd, end_jd, over_scan_days, ayanamsa, nirayana},
          "months":  [MasaInterval, ...]   # complete months overlapping the window
          "new_moons": [jd, ...], "full_moons": [jd, ...],
          "sankrantis": [(jd, rashi_index), ...],
        }
        Only months whose own span overlaps the requested window are returned, and
        every returned month has `complete=True`.

    Raises:
        ValueError: start_jd > end_jd.
        ephemeris.EphemerisError: a pyswisseph read failed mid-scan.
    """
    if start_jd > end_jd:
        raise ValueError(f"start_jd ({start_jd}) must be <= end_jd ({end_jd})")
    lo, hi = start_jd - OVER_SCAN_DAYS, end_jd + OVER_SCAN_DAYS

    lunations = scan_quantised_crossings(
        _elongation, 2, lo, hi,
        rate_bound=ELONGATION_RATE_BOUND, tol_jd=tol_jd,
    )
    new_moons = [c.jd for c in lunations if c.to_index == 0]
    full_moons = [c.jd for c in lunations if c.to_index == 1]
    sankrantis = [(c.jd, c.to_index)
                  for c in scan_divisional_ingresses("sun", lo, hi,
                                                     n_divisions=12, tol_jd=tol_jd)]

    months = build_masa_intervals(new_moons, sankrantis, sankranti_span=(lo, hi))
    # Trim to the requested window: keep a month that OVERLAPS it, drop any whose
    # completeness the over-scan did not actually buy.
    kept = [m for m in months
            if m.complete and m.end_jd > start_jd and m.start_jd < end_jd]
    return {
        "scanned": {"start_jd": start_jd, "end_jd": end_jd,
                    "over_scan_days": OVER_SCAN_DAYS,
                    "ayanamsa": AYANAMSA_NAME, "nirayana": True},
        "months": kept,
        "new_moons": new_moons,
        "full_moons": full_moons,
        "sankrantis": sankrantis,
    }


def _first_sunrise_on_or_after(jd_ut: float, tz: _dt.tzinfo,
                               latitude: float, longitude: float) -> _dt.datetime:
    """The first sunrise at (lat, lon) strictly after `jd_ut`.

    The Vedic day the month begins on. Delegates to panchanga.calculate_sunrise
    so there is exactly one sunrise definition in the project (disc centre,
    geometric horizon, no refraction -- validated against JHora at S19).
    """
    y, mo, dy, hr = swe.revjul(jd_ut)
    instant = (_dt.datetime(y, mo, dy, tzinfo=_dt.timezone.utc)
               + _dt.timedelta(hours=hr)).astimezone(tz)
    # Look back one day as well: the instant's own local date may have a sunrise
    # that is still ahead of it only when the instant is pre-dawn.
    for offset in (-1, 0, 1, 2):
        probe = instant + _dt.timedelta(days=offset)
        sunrise = panchanga.calculate_sunrise(probe, latitude, longitude)
        if sunrise > instant:
            return sunrise
    raise ValueError(
        f"no sunrise found after jd_ut={jd_ut} at lat={latitude}, lon={longitude}"
    )


def resolve_local_dates(months: list[MasaInterval], *, tz: _dt.tzinfo,
                        latitude: float, longitude: float) -> list[dict]:
    """Attach place-resolved civil dates to place-independent month intervals.

    `tz`, `latitude` and `longitude` are REQUIRED and have no defaults: there is
    no such thing as the civil date of a masa without a place, and a default here
    would be a silent one-day error rather than a missing argument.

    Returns one dict per month:
        start_date   -- ISO date of the first sunrise after the opening new moon
        end_date     -- same, for the closing new moon (the NEXT month's first day)
        end_date_inclusive -- the last day belonging to this month
        name_sa, masa_index, sankranti_count, start_jd, end_jd, complete
    `end_date_inclusive` exists so a renderer can never print a half-open bound as
    if it were a date the user's month still covers.

    Raises:
        ValueError: a latitude outside panchanga's supported range, or no sunrise
            (both propagated from calculate_sunrise -- polar latitudes are out of
            v1 scope and must refuse, not approximate).
    """
    out: list[dict] = []
    for m in months:
        start = _first_sunrise_on_or_after(m.start_jd, tz, latitude, longitude)
        end = _first_sunrise_on_or_after(m.end_jd, tz, latitude, longitude)
        out.append({
            "start_jd": m.start_jd,
            "end_jd": m.end_jd,
            "start_date": start.date().isoformat(),
            "end_date": end.date().isoformat(),
            "end_date_inclusive": (end.date() - _dt.timedelta(days=1)).isoformat(),
            "masa_index": m.masa_index,
            "name_sa": m.name_sa,
            "sankranti_count": m.sankranti_count,
            "complete": m.complete,
        })
    return out
