"""Ghatika, Hora and Bhava Lagna -- the time-rate special lagnas.

All three advance from the Sun's SIDEREAL longitude at the sunrise that
begins the Vedic day of birth, at a fixed rate per unit of elapsed time:

    Bhava Lagna     30 deg per  2 hours     (1 rasi per 5 ghatis)
    Hora Lagna      30 deg per  1 hour      (1 rasi per 2.5 ghatis)
    Ghatika Lagna   30 deg per 24 minutes   (1 rasi per ghati)

A ghati is 24 minutes, so the Ghatika rate is 75 deg of arc per hour.

THE VEDIC DAY BOUNDARY IS THE POINT THAT GOES WRONG. The day runs sunrise
to sunrise, so a birth BEFORE sunrise belongs to the previous calendar day's
sunrise. Sulabh's 00:30 birth is such a case: using the same morning's
sunrise puts the elapsed time NEGATIVE and lands every special lagna a third
of a zodiac away. `_governing_sunrise` walks back a day when needed.

NO EPHEMERIS OF ITS OWN beyond the Sun's position and sunrise, both taken
from modules that already own them (`helpers.ephemeris`, `core.panchanga`) --
this module adds arithmetic, not astronomy.

Python 3.11.
"""
from __future__ import annotations

from datetime import datetime, timedelta

import swisseph as swe

from agent.calculations.core.panchanga import calculate_sunrise
from agent.calculations.helpers.ephemeris import sidereal_longitude

_SIGNS = ("Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra",
          "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces")

# degrees of arc advanced per hour elapsed since sunrise
RATE_DEG_PER_HOUR = {
    "bhava_lagna": 15.0,    # 30 deg / 2 h
    "hora_lagna": 30.0,     # 30 deg / 1 h
    "ghati_lagna": 75.0,    # 30 deg / 0.4 h (one ghati)
}


class SpecialLagnaError(ValueError):
    """Raised when a special lagna cannot be computed from the inputs given."""


def _governing_sunrise(moment: datetime, latitude: float,
                       longitude: float) -> datetime:
    """The sunrise that opens the Vedic day containing `moment`.

    Same calendar date when the birth is at or after that day's sunrise;
    the PREVIOUS day's sunrise otherwise.
    """
    todays = calculate_sunrise(moment, latitude, longitude)
    if moment >= todays:
        return todays
    return calculate_sunrise(moment - timedelta(days=1), latitude, longitude)


def _to_jd_ut(moment: datetime) -> float:
    u = moment.astimezone(tz=moment.tzinfo.utcoffset(moment) and
                          __import__("datetime").timezone.utc)
    return swe.julday(u.year, u.month, u.day,
                      u.hour + u.minute / 60 + u.second / 3600)


def compute_special_lagnas(moment: datetime, latitude: float,
                           longitude: float) -> dict:
    """All three special lagnas for a birth moment.

    Returns {name: {"longitude": float, "sign": str, "degree_in_sign": float}}.
    Raises SpecialLagnaError on a naive datetime or an unusable location.
    """
    if moment.tzinfo is None:
        raise SpecialLagnaError("moment must be timezone-aware")
    try:
        sunrise = _governing_sunrise(moment, latitude, longitude)
    except ValueError as e:
        raise SpecialLagnaError(f"sunrise unavailable: {e}") from e

    elapsed_hours = (moment - sunrise).total_seconds() / 3600.0
    if elapsed_hours < 0:
        raise SpecialLagnaError(
            f"birth precedes its governing sunrise by {-elapsed_hours:.3f} h")

    try:
        sun_at_sunrise = sidereal_longitude(_to_jd_ut(sunrise), swe.SUN)
    except Exception as e:  # noqa: BLE001 -- surfaced with context, never silent
        raise SpecialLagnaError(f"Sun longitude at sunrise failed: {e}") from e

    out = {}
    for name, rate in RATE_DEG_PER_HOUR.items():
        lon = (sun_at_sunrise + rate * elapsed_hours) % 360.0
        out[name] = {
            "longitude": round(lon, 4),
            "sign": _SIGNS[int(lon // 30)],
            "degree_in_sign": round(lon % 30, 4),
        }
    out["_sunrise_used"] = sunrise.isoformat()
    out["_elapsed_hours"] = round(elapsed_hours, 4)
    out["_sun_at_sunrise"] = round(sun_at_sunrise, 4)
    return out
