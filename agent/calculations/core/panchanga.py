"""Panchanga: tithi, vara, nakshatra, yoga, karana, hora, choghadiya, and muhurta-avoidance windows. Drik (ephemeris-based) calculation using Lahiri ayanamsa."""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional

import swisseph as swe


AYANAMSA_FLAG = swe.SIDM_LAHIRI
BOUNDARY_THRESHOLD_PERCENT = 5.0   # nakshatra/tithi boundary flag
REFRACTION_ARCMIN = 34.0           # standard atmospheric refraction


@dataclass(frozen=True)
class PanchangaElement:
    name: str
    index: int
    percent_left: float
    next_name: str
    is_boundary: bool
    transition_time: datetime


@dataclass(frozen=True)
class ChoghadiyaWindow:
    name: str
    quality: str  # "auspicious" | "neutral" | "inauspicious"
    start: datetime
    end: datetime


@dataclass(frozen=True)
class Panchanga:
    moment: datetime
    location: tuple[float, float]  # (lat, lon)
    sunrise: datetime
    sunset: datetime
    tithi: PanchangaElement
    vara: PanchangaElement
    nakshatra: PanchangaElement
    nakshatra_pada: int
    yoga: PanchangaElement
    karana: PanchangaElement
    hora_lord: str
    choghadiya_day: list[ChoghadiyaWindow]
    choghadiya_night: list[ChoghadiyaWindow]
    rahu_kalam: tuple[datetime, datetime]
    yamaganda: tuple[datetime, datetime]
    gulika_kalam: tuple[datetime, datetime]
    abhijit_muhurta: Optional[tuple[datetime, datetime]]
    ayanamsa: float


def _datetime_to_julian_day_ut(moment: datetime) -> float:
    """Convert timezone-aware datetime to Julian Day in UT.

    Raises ValueError if moment is naive (no tzinfo).
    """
    if moment.tzinfo is None:
        raise ValueError("moment must be timezone-aware")
    # Convert to UTC; pyswisseph julday expects UT, fractional hours
    utc = moment.astimezone(timezone.utc)
    hr = (utc.hour + utc.minute / 60.0 + utc.second / 3600.0
          + utc.microsecond / 3_600_000_000.0)
    return swe.julday(utc.year, utc.month, utc.day, hr)


def _julian_day_ut_to_datetime(jd_ut: float, tz: timezone) -> datetime:
    """Convert Julian Day (UT) back to timezone-aware datetime in tz."""
    y, mo, dy, hr = swe.revjul(jd_ut)
    # revjul returns fractional hours; timedelta handles sub-second precision
    utc_dt = datetime(y, mo, dy, tzinfo=timezone.utc) + timedelta(hours=hr)
    return utc_dt.astimezone(tz)


def calculate_sunrise(date_local: datetime, latitude: float,
                      longitude: float) -> datetime:
    """Sunrise for the calendar date of date_local at the given location.

    Uses the Hindu rising definition (disc center at geometric horizon,
    no atmospheric refraction) to match JHora reference output.
    Empirically validated: BIT_DISC_CENTER | BIT_NO_REFRACTION matches
    JHora within ±2s across all 4 reference locations (Session 19 P1.2a).

    Returns timezone-aware datetime in same tz as input.

    Raises ValueError if date_local is naive.
    Raises ValueError if no sunrise on this date (polar latitudes).
    """
    if date_local.tzinfo is None:
        raise ValueError("moment must be timezone-aware")
    if not -66.5 <= latitude <= 66.5:
        raise ValueError(
            f"latitude {latitude} outside v1 supported range [-66.5, 66.5]"
        )
    if not -180 <= longitude <= 180:
        raise ValueError(f"longitude {longitude} outside range [-180, 180]")

    # Anchor search at local midnight of the search date
    midnight = date_local.replace(hour=0, minute=0, second=0, microsecond=0)
    jd_start = _datetime_to_julian_day_ut(midnight)

    # Hindu rising: disc center at geometric horizon (no refraction).
    # pyswisseph rise_trans signature: (tjdut, body, rsmi, geopos, atpress, attemp, flags)
    # geopos convention: (geographic_longitude, geographic_latitude, altitude_m)
    _rise_rsmi = swe.CALC_RISE | swe.BIT_DISC_CENTER | swe.BIT_NO_REFRACTION
    ret, tret = swe.rise_trans(
        jd_start, swe.SUN, _rise_rsmi,
        (longitude, latitude, 0.0), 0.0, 0.0, swe.FLG_SWIEPH,
    )

    if ret != 0:
        raise ValueError(
            f"No sunrise found for lat={latitude}, lon={longitude} on "
            f"{date_local.date()} (polar day or night; ret={ret})"
        )

    return _julian_day_ut_to_datetime(tret[0], date_local.tzinfo)


def calculate_sunset(date_local: datetime, latitude: float,
                     longitude: float) -> datetime:
    """Sunset for the calendar date of date_local at the given location.

    Same Hindu rising definition as calculate_sunrise (disc center,
    geometric horizon, no atmospheric refraction).

    Returns timezone-aware datetime in same tz as input.

    Raises ValueError if date_local is naive.
    Raises ValueError if no sunset on this date (polar latitudes).
    """
    if date_local.tzinfo is None:
        raise ValueError("moment must be timezone-aware")
    if not -66.5 <= latitude <= 66.5:
        raise ValueError(
            f"latitude {latitude} outside v1 supported range [-66.5, 66.5]"
        )
    if not -180 <= longitude <= 180:
        raise ValueError(f"longitude {longitude} outside range [-180, 180]")

    midnight = date_local.replace(hour=0, minute=0, second=0, microsecond=0)
    jd_start = _datetime_to_julian_day_ut(midnight)

    _set_rsmi = swe.CALC_SET | swe.BIT_DISC_CENTER | swe.BIT_NO_REFRACTION
    ret, tret = swe.rise_trans(
        jd_start, swe.SUN, _set_rsmi,
        (longitude, latitude, 0.0), 0.0, 0.0, swe.FLG_SWIEPH,
    )

    if ret != 0:
        raise ValueError(
            f"No sunset found for lat={latitude}, lon={longitude} on "
            f"{date_local.date()} (polar day or night; ret={ret})"
        )

    return _julian_day_ut_to_datetime(tret[0], date_local.tzinfo)


def calculate_panchanga(moment: datetime, latitude: float,
                        longitude: float) -> Panchanga:
    """Compute full Panchanga at given moment + location.

    Args:
        moment: Timezone-aware datetime. Naive datetime raises ValueError.
        latitude: Decimal degrees, positive N, negative S.
            Must be in [-66.5, 66.5] (excludes polar regions per v1 scope guard).
        longitude: Decimal degrees, positive E, negative W.

    Raises ValueError on naive datetime or out-of-scope latitude.
    """
    if moment.tzinfo is None:
        raise ValueError("moment must be timezone-aware")
    if not -66.5 <= latitude <= 66.5:
        raise ValueError(
            f"latitude {latitude} outside v1 supported range [-66.5, 66.5]"
        )
    if not -180 <= longitude <= 180:
        raise ValueError(f"longitude {longitude} outside range [-180, 180]")
    raise NotImplementedError("P1.2b — core five + hora")
