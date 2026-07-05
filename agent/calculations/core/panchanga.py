"""Panchanga: tithi, vara, nakshatra, yoga, karana, hora, choghadiya, and muhurta-avoidance windows. Drik (ephemeris-based) calculation using Lahiri ayanamsa.

EPHEMERIS NOTE (Session 52 migration): calculate_panchanga()'s Moon/Sun
longitude+speed lookups delegate to helpers/ephemeris.py's
sidereal_position(). calculate_sunrise()/calculate_sunset()'s
swe.rise_trans() calls are a separate pyswisseph API (not swe.calc_ut())
and are out of this migration's scope.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional

import swisseph as swe

from agent.calculations.helpers import ephemeris

from ._panchanga_tables import (
    TITHI_NAMES, NAKSHATRA_NAMES, YOGA_NAMES, KARANA_SEQ,
    VARA_NAMES, VARA_LORD_INDEX, HORA_SEQ,
    CHOGHADIYA_NAMES, CHOGHADIYA_QUALITY, CHOG_NIGHT_START,
    RAHU_KALAM_SLOT, YAMAGANDA_SLOT, GULIKA_KALAM_SLOT,
)


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

    swe.set_sid_mode(AYANAMSA_FLAG)
    jd_ut = _datetime_to_julian_day_ut(moment)
    # get_ayanamsa_ut() is a separate pyswisseph API (not swe.calc_ut()) --
    # inlined here, out of this migration's scope (chart_calculator.py
    # repeats this same set_sid_mode + get_ayanamsa_ut pair inline in 3
    # places; no shared wrapper for it exists).
    ayanamsa = swe.get_ayanamsa_ut(jd_ut)

    # Session 52 migration: delegates to helpers/ephemeris.py's
    # sidereal_position() (Moon/Sun both need longitude + signed speed
    # here); calc_ut failures now surface as ephemeris.EphemerisError (a
    # RuntimeError subclass) naming the planet id and jd_ut.
    moon_pos = ephemeris.sidereal_position(jd_ut, swe.MOON)
    sun_pos = ephemeris.sidereal_position(jd_ut, swe.SUN)

    moon_lon: float = moon_pos.longitude
    moon_speed: float = moon_pos.speed   # deg/day; positive = direct
    sun_lon: float = sun_pos.longitude
    sun_speed: float = sun_pos.speed

    # Elongation: sidereal Moon minus Sun, forced into [0, 360)
    elong: float = (moon_lon - sun_lon) % 360
    elong_speed: float = moon_speed - sun_speed  # ~12 deg/day, always positive

    # ── Tithi ─────────────────────────────────────────────────────────────────
    TITHI_SPAN = 12.0
    tithi_idx = int(elong / TITHI_SPAN)
    within_tithi = elong % TITHI_SPAN
    tithi_pct_left = (1.0 - within_tithi / TITHI_SPAN) * 100.0
    tithi_trans_dt = _julian_day_ut_to_datetime(
        jd_ut + (TITHI_SPAN - within_tithi) / elong_speed, moment.tzinfo
    )
    tithi = PanchangaElement(
        name=TITHI_NAMES[tithi_idx],
        index=tithi_idx,
        percent_left=tithi_pct_left,
        next_name=TITHI_NAMES[(tithi_idx + 1) % 30],
        is_boundary=tithi_pct_left < BOUNDARY_THRESHOLD_PERCENT,
        transition_time=tithi_trans_dt,
    )

    # ── Nakshatra ──────────────────────────────────────────────────────────────
    NAK_SPAN = 360.0 / 27
    nak_idx = int(moon_lon / NAK_SPAN) % 27
    within_nak = moon_lon % NAK_SPAN
    nak_pct_left = (1.0 - within_nak / NAK_SPAN) * 100.0
    nakshatra_pada = int(within_nak / (NAK_SPAN / 4)) + 1
    nak_trans_dt = _julian_day_ut_to_datetime(
        jd_ut + (NAK_SPAN - within_nak) / moon_speed, moment.tzinfo
    )
    nakshatra = PanchangaElement(
        name=NAKSHATRA_NAMES[nak_idx],
        index=nak_idx,
        percent_left=nak_pct_left,
        next_name=NAKSHATRA_NAMES[(nak_idx + 1) % 27],
        is_boundary=nak_pct_left < BOUNDARY_THRESHOLD_PERCENT,
        transition_time=nak_trans_dt,
    )

    # ── Yoga ───────────────────────────────────────────────────────────────────
    YOGA_SPAN = 360.0 / 27
    yoga_sum = (moon_lon + sun_lon) % 360
    yoga_idx = int(yoga_sum / YOGA_SPAN) % 27
    within_yoga = yoga_sum % YOGA_SPAN
    yoga_pct_left = (1.0 - within_yoga / YOGA_SPAN) * 100.0
    yoga_speed = moon_speed + sun_speed   # ~14 deg/day
    yoga_trans_dt = _julian_day_ut_to_datetime(
        jd_ut + (YOGA_SPAN - within_yoga) / yoga_speed, moment.tzinfo
    )
    yoga = PanchangaElement(
        name=YOGA_NAMES[yoga_idx],
        index=yoga_idx,
        percent_left=yoga_pct_left,
        next_name=YOGA_NAMES[(yoga_idx + 1) % 27],
        is_boundary=False,
        transition_time=yoga_trans_dt,
    )

    # ── Karana ─────────────────────────────────────────────────────────────────
    KARANA_SPAN = 6.0
    karana_idx = int(elong / KARANA_SPAN) % 60
    within_karana = elong % KARANA_SPAN
    karana_pct_left = (1.0 - within_karana / KARANA_SPAN) * 100.0
    karana_trans_dt = _julian_day_ut_to_datetime(
        jd_ut + (KARANA_SPAN - within_karana) / elong_speed, moment.tzinfo
    )
    karana = PanchangaElement(
        name=KARANA_SEQ[karana_idx],
        index=karana_idx,
        percent_left=karana_pct_left,
        next_name=KARANA_SEQ[(karana_idx + 1) % 60],
        is_boundary=False,
        transition_time=karana_trans_dt,
    )

    # ── Sunrise / Sunset ───────────────────────────────────────────────────────
    sunrise = calculate_sunrise(moment, latitude, longitude)
    sunset = calculate_sunset(moment, latitude, longitude)

    # ── Vara ───────────────────────────────────────────────────────────────────
    # The Vedic day starts at sunrise; pre-sunrise moments belong to yesterday.
    if moment >= sunrise:
        vara_sunrise = sunrise
        sr_next = calculate_sunrise(moment + timedelta(days=1), latitude, longitude)
    else:
        vara_sunrise = calculate_sunrise(moment - timedelta(days=1), latitude, longitude)
        sr_next = sunrise

    vara_weekday = vara_sunrise.weekday()          # 0=Mon … 6=Sun (Python convention)
    vara_name = VARA_NAMES[vara_weekday]
    vara_dur_sec = (sr_next - vara_sunrise).total_seconds()
    vara_elapsed_sec = (moment - vara_sunrise).total_seconds()
    vara_pct_left = (1.0 - vara_elapsed_sec / vara_dur_sec) * 100.0
    vara = PanchangaElement(
        name=vara_name,
        index=vara_weekday,
        percent_left=vara_pct_left,
        next_name=VARA_NAMES[(vara_weekday + 1) % 7],
        is_boundary=False,
        transition_time=sr_next,
    )

    # ── Hora (24 flat 1-hour segments, sunrise to next sunrise) ──────────────────
    # PVR: "Each day starts at sunrise and ends at next day's sunrise. This period
    # is divided into 24 equal parts and they are called horas." (see
    # _pvr_spec_reference.json "hora" entry for exact page ref/quote.) hora_n =
    # floor(elapsed_seconds_since_sunrise / 3600) — flat 60-min segments anchored
    # at sunrise, NOT proportional to day_length. Validated against all 4 JHora
    # fixtures (e.g. Sulabh -> Mars); a day_length/12-proportional model gives
    # Jupiter for that fixture, which is wrong.
    # Distinct from Choghadiya/Rahu Kalam/Yamaganda/Gulika Kalam (day_length/8)
    # and Abhijit Muhurta (day_length/15), which ARE proportional — do not
    # confuse the two segmentation models.
    hora_n = int(vara_elapsed_sec / 3600)
    hora_lord = HORA_SEQ[(VARA_LORD_INDEX[vara_name] + hora_n) % 7]

    # ── Day / Night arc durations ─────────────────────────────────────────────
    # Reuse vara_sunrise / sunset / sr_next — do NOT recompute.
    day_dur_sec   = (sunset - vara_sunrise).total_seconds()
    night_dur_sec = (sr_next - sunset).total_seconds()
    day_seg_sec   = day_dur_sec / 8    # one choghadiya / kalam segment
    night_seg_sec = night_dur_sec / 8

    # ── Choghadiya day ────────────────────────────────────────────────────────
    # 8 equal segments sunrise→sunset; seeded by VARA_LORD_INDEX (same as hora).
    _day_ci = VARA_LORD_INDEX[vara_name]
    choghadiya_day = [
        ChoghadiyaWindow(
            name=CHOGHADIYA_NAMES[(_day_ci + n) % 7],
            quality=CHOGHADIYA_QUALITY[(_day_ci + n) % 7],
            start=vara_sunrise + timedelta(seconds=n * day_seg_sec),
            end=vara_sunrise + timedelta(seconds=(n + 1) * day_seg_sec),
        )
        for n in range(8)
    ]

    # ── Choghadiya night ──────────────────────────────────────────────────────
    # 8 equal segments sunset→sr_next; night start index from CHOG_NIGHT_START.
    _night_ci = CHOG_NIGHT_START[vara_name]
    choghadiya_night = [
        ChoghadiyaWindow(
            name=CHOGHADIYA_NAMES[(_night_ci + n) % 7],
            quality=CHOGHADIYA_QUALITY[(_night_ci + n) % 7],
            start=sunset + timedelta(seconds=n * night_seg_sec),
            end=sunset + timedelta(seconds=(n + 1) * night_seg_sec),
        )
        for n in range(8)
    ]

    # ── Rahu Kalam / Yamaganda / Gulika Kalam ─────────────────────────────────
    # Each occupies one day-arc segment (day_length/8) at a vara-indexed slot.
    # Night versions deferred to v2 (day-arc only in v1).
    def _day_window(slot: int) -> tuple[datetime, datetime]:
        return (
            vara_sunrise + timedelta(seconds=slot * day_seg_sec),
            vara_sunrise + timedelta(seconds=(slot + 1) * day_seg_sec),
        )

    rahu_kalam   = _day_window(RAHU_KALAM_SLOT[vara_weekday])
    yamaganda    = _day_window(YAMAGANDA_SLOT[vara_weekday])
    gulika_kalam = _day_window(GULIKA_KALAM_SLOT[vara_weekday])

    # ── Abhijit Muhurta ───────────────────────────────────────────────────────
    # Definition: 8th of 15 equal daytime muhurtas (each = day_length/15).
    # Center = vara_sunrise + 7.5/15 × day_length = exact midpoint of day arc.
    # Source: Muhurtha-Chinthamani ("A Muhurta is equal to the 15th part of
    # the Dinamaana"; 15 named muhurtas, Abhijit is the 8th — starts at 7/15).
    # PVR's book was searched but does not cover this topic.
    # DISCREPANCY NOTE: some modern apps use a fixed 48-minute window; that
    # value assumes a standard 30-ghati (12-hour) day. Classical definition is
    # proportional (day_length/15); this implementation follows the classical form.
    muhurta_sec = day_dur_sec / 15
    abhijit_muhurta: Optional[tuple[datetime, datetime]] = (
        vara_sunrise + timedelta(seconds=7 * muhurta_sec),
        vara_sunrise + timedelta(seconds=8 * muhurta_sec),
    )

    return Panchanga(
        moment=moment,
        location=(latitude, longitude),
        sunrise=sunrise,
        sunset=sunset,
        tithi=tithi,
        vara=vara,
        nakshatra=nakshatra,
        nakshatra_pada=nakshatra_pada,
        yoga=yoga,
        karana=karana,
        hora_lord=hora_lord,
        choghadiya_day=choghadiya_day,
        choghadiya_night=choghadiya_night,
        rahu_kalam=rahu_kalam,
        yamaganda=yamaganda,
        gulika_kalam=gulika_kalam,
        abhijit_muhurta=abhijit_muhurta,
        ayanamsa=ayanamsa,
    )
