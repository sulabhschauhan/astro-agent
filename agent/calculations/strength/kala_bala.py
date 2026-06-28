"""Kala Bala — temporal strength component of Shadbala.

BPHS 27.7-20, Raman "Graha and Bhava Balas" Ch. 4-7.

Known divergences (V1):
- Ayana Bala: uses PyJHora constants (24.0 + adj) * 1.25, not Raman's 23.45 * 1.2793.
- Paksha Bala Moon: not doubled (AstroSage shows Moon=13.24, same as malefic value).
  PyJHora doubles Moon; BPHS 27.11 text is ambiguous; AstroSage wins.
- Abda/Masa Bala: BPHS-compliant (Mesha Sankranti weekday / solar month ingress weekday).
  PyJHora incorrectly uses birth weekday for both (placeholder bug).
- Hora Bala: proportional horas (day_length/12, night_length/12), not fixed 60-min horas.
  AstroSage parity requires proportional; JHora uses fixed-60-min.
"""

import logging
from datetime import datetime, timedelta, timezone

import swisseph as swe

from agent.calculations.core.panchanga import calculate_sunrise, calculate_sunset

logger = logging.getLogger(__name__)

_PLANETS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]

_SWE_IDS = {
    "Sun": swe.SUN, "Moon": swe.MOON, "Mars": swe.MARS,
    "Mercury": swe.MERCURY, "Jupiter": swe.JUPITER,
    "Venus": swe.VENUS, "Saturn": swe.SATURN,
}

# Day-strong (diurnal): get nathonnatha score directly; Night-strong: get 60 - score
_DAY_STRONG   = frozenset({"Sun", "Jupiter", "Venus"})
_NIGHT_STRONG = frozenset({"Moon", "Mars", "Saturn"})
# Mercury is always 60

# Tara Grahas participate in Yuddha Bala
_TARA_GRAHAS = frozenset({"Mars", "Mercury", "Jupiter", "Venus", "Saturn"})

# Raman "Graha and Bhava Balas", confirmed PyJHora const.py
# SENSITIVE_TO: yuddha_bala_disc_constants
_DISC_DIAMETER = {
    "Mars": 9.4, "Mercury": 6.6, "Jupiter": 190.4, "Venus": 16.6, "Saturn": 158.0
}

# pyswisseph day_of_week: 0=Monday, 1=Tuesday, 2=Wednesday, 3=Thursday,
#                         4=Friday, 5=Saturday, 6=Sunday
_WEEKDAY_LORD = {
    0: "Moon", 1: "Mars", 2: "Mercury", 3: "Jupiter",
    4: "Venus", 5: "Saturn", 6: "Sun",
}

_HORA_SEQ = ["Sun", "Venus", "Mercury", "Moon", "Saturn", "Jupiter", "Mars"]

_FLAGS_SID = swe.FLG_SWIEPH | swe.FLG_SIDEREAL
_FLAGS_EQ  = swe.FLG_SWIEPH | swe.FLG_SIDEREAL | swe.FLG_EQUATORIAL


# ── Private helpers ────────────────────────────────────────────────────────────

def _jd_to_utc_datetime(jd_ut: float) -> datetime:
    y, mo, d, h = swe.revjul(jd_ut)
    return datetime(y, mo, d, tzinfo=timezone.utc) + timedelta(hours=h)


def _solar_day_refs(birth_utc: datetime, lat: float, lon: float):
    """Return (sunrise, sunset) for the Vedic solar day containing birth_utc.

    If birth is before today's sunrise, use previous day's sunrise/sunset.
    Both datetimes are timezone-aware in the solar timezone.
    """
    solar_tz = timezone(timedelta(hours=lon / 15.0))
    birth_local = birth_utc.astimezone(solar_tz)
    sunrise_today = calculate_sunrise(birth_local, lat, lon)
    if birth_local < sunrise_today:
        yesterday = birth_local - timedelta(days=1)
        return (
            calculate_sunrise(yesterday, lat, lon),
            calculate_sunset(yesterday, lat, lon),
        )
    return sunrise_today, calculate_sunset(birth_local, lat, lon)


def _sun_sign(jd: float) -> int:
    """Return Sun's sidereal sign 0=Aries…11=Pisces at given JD."""
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    xx, _ = swe.calc_ut(jd, swe.SUN, _FLAGS_SID)
    return int(xx[0] % 360.0 / 30)


def _mesha_sankranti_jd(birth_jd: float) -> float:
    """Return the JD of Mesha Sankranti (Sun enters Aries) for the year of birth.

    Walks forward from birth_jd-370 to find the Pisces→Aries crossing, then
    bisects to sub-minute precision.
    """
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    # Coarse scan: step daily, look for Pisces(11)→Aries(0) crossing
    step = 1.0
    jd = birth_jd - 370.0
    prev_sign = _sun_sign(jd)
    crossing_jd = None
    for _ in range(400):
        jd += step
        cur_sign = _sun_sign(jd)
        if prev_sign == 11 and cur_sign == 0:
            crossing_jd = jd - step
            break
        prev_sign = cur_sign
    if crossing_jd is None:
        raise RuntimeError("_mesha_sankranti_jd: could not find Mesha Sankranti near JD=%s" % birth_jd)
    # Bisect to 1e-6 JD precision (~0.09 s)
    lo, hi = crossing_jd, crossing_jd + step
    for _ in range(40):
        mid = (lo + hi) / 2.0
        if _sun_sign(mid) == 0:
            hi = mid
        else:
            lo = mid
    return (lo + hi) / 2.0


def _find_recent_sun_ingress(birth_jd: float) -> float:
    """Return the JD when Sun entered its current sign, just before birth_jd."""
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    target_sign = _sun_sign(birth_jd)
    # Walk backward in 1-day steps until sign changes
    step = 1.0
    jd = birth_jd
    for _ in range(35):
        jd -= step
        if _sun_sign(jd) != target_sign:
            # crossing is between jd and jd+step
            lo, hi = jd, jd + step
            for _ in range(40):
                mid = (lo + hi) / 2.0
                if _sun_sign(mid) == target_sign:
                    hi = mid
                else:
                    lo = mid
            return (lo + hi) / 2.0
    raise RuntimeError("_find_recent_sun_ingress: could not find ingress near JD=%s" % birth_jd)


# ── Sub-component functions ────────────────────────────────────────────────────

def _nathonnatha_bala(jd_ut: float, lat: float, lon: float) -> dict:
    """Nathonnatha Bala: strength based on distance from nearest solar midnight.

    Day-strong planets are strongest at noon; night-strong at midnight.
    Mercury always gets 60.
    """
    birth_utc = _jd_to_utc_datetime(jd_ut)
    sunrise, sunset = _solar_day_refs(birth_utc, lat, lon)

    day_secs   = (sunset - sunrise).total_seconds()
    night_secs = 86400.0 - day_secs

    # Solar midnight = midpoint of night arc
    prev_midnight = sunrise - timedelta(seconds=night_secs / 2.0)
    next_midnight = sunset  + timedelta(seconds=night_secs / 2.0)

    solar_tz    = timezone(timedelta(hours=lon / 15.0))
    birth_local = birth_utc.astimezone(solar_tz)

    arc_prev = abs((birth_local - prev_midnight).total_seconds())
    arc_next = abs((birth_local - next_midnight).total_seconds())
    arc_secs = min(arc_prev, arc_next)

    # Convert to Virupas: arc in hours / 12 * 60, clamped [0, 60]
    t_diff = min(60.0, arc_secs / 3600.0 / 12.0 * 60.0)

    result = {}
    for p in _PLANETS:
        if p == "Mercury":
            result[p] = 60.0
        elif p in _DAY_STRONG:
            result[p] = round(t_diff, 4)
        else:  # night-strong
            result[p] = round(60.0 - t_diff, 4)
    return result


def _paksha_bala(jd_ut: float) -> dict:
    """Paksha Bala: strength from lunar phase (Moon–Sun elongation).

    Benefics strong in Shukla (waxing); malefics strong in Krishna (waning).
    Moon and Mercury follow their classification (no doubling of Moon).
    """
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    moon_lon = swe.calc_ut(jd_ut, swe.MOON, _FLAGS_SID)[0][0] % 360.0
    sun_lon  = swe.calc_ut(jd_ut, swe.SUN,  _FLAGS_SID)[0][0] % 360.0

    tithi_f = ((moon_lon - sun_lon) % 360.0) / 12.0  # 0.0–30.0

    if tithi_f < 15.0:  # Shukla paksha (waxing)
        benefic_val = tithi_f * 4.0
        malefic_val = (15.0 - tithi_f) * 4.0
    else:               # Krishna paksha (waning)
        benefic_val = (30.0 - tithi_f) * 4.0
        malefic_val = (tithi_f - 15.0) * 4.0

    # Paksha Bala: only Jupiter/Venus are benefics per Raman + AstroSage parity.
    # Moon and Mercury use malefic formula regardless of waxing/waning.
    # Source: AstroSage Sulabh fixture (all non-Jup/Ven = 13.24 in Krishna paksha).
    _PAKSHA_BENEFICS = {"Jupiter", "Venus"}
    result = {}
    for p in _PLANETS:
        if p in _PAKSHA_BENEFICS:   # benefic formula
            result[p] = round(benefic_val, 4)
        else:                        # malefic formula for all others
            result[p] = round(malefic_val, 4)
    return result


def _thribhaga_bala(jd_ut: float, lat: float, lon: float) -> dict:
    """Thribhaga Bala: planet ruling the current third of day/night.

    Jupiter always receives 60. Day is divided into 3 parts (Mercury, Sun, Saturn
    for day-thirds) and night into 3 parts (Moon, Venus, Mars for night-thirds).
    The ruling planet of the current third gets 60; others get 0.
    """
    birth_utc = _jd_to_utc_datetime(jd_ut)
    sunrise, sunset = _solar_day_refs(birth_utc, lat, lon)

    solar_tz    = timezone(timedelta(hours=lon / 15.0))
    birth_local = birth_utc.astimezone(solar_tz)
    sunrise_loc = sunrise.astimezone(solar_tz)
    sunset_loc  = sunset.astimezone(solar_tz)

    day_secs   = (sunset_loc - sunrise_loc).total_seconds()
    night_secs = 86400.0 - day_secs
    third_day   = day_secs   / 3.0
    third_night = night_secs / 3.0

    # Thribhaga lords for day-thirds and night-thirds (BPHS 27.13)
    day_lords   = ["Mercury", "Sun",  "Saturn"]
    night_lords = ["Moon",    "Venus", "Mars"]

    lord = None
    if sunrise_loc <= birth_local <= sunset_loc:
        idx = int((birth_local - sunrise_loc).total_seconds() / third_day)
        idx = min(idx, 2)
        lord = day_lords[idx]
    else:
        # Night: handle cross-midnight
        if birth_local >= sunset_loc:
            time_into_night = (birth_local - sunset_loc).total_seconds()
        else:
            # Before sunrise: offset from previous sunset
            prev_sunset = sunset_loc - timedelta(hours=24)
            time_into_night = (birth_local - prev_sunset).total_seconds()
        idx = int(time_into_night / third_night)
        idx = min(idx, 2)
        lord = night_lords[idx]

    result = {}
    for p in _PLANETS:
        if p == "Jupiter" or p == lord:
            result[p] = 60.0
        else:
            result[p] = 0.0
    return result


def _abda_bala(birth_jd: float) -> dict:
    """Abda Bala: planet ruling the year (lord of weekday of Mesha Sankranti).

    BPHS 27.14. The year-lord is the weekday lord of the moment Sun enters Aries.
    """
    sankranti_jd = _mesha_sankranti_jd(birth_jd)
    weekday = swe.day_of_week(sankranti_jd)
    lord = _WEEKDAY_LORD[weekday]
    return {p: 15.0 if p == lord else 0.0 for p in _PLANETS}


def _masa_bala(birth_jd: float) -> dict:
    """Masa Bala: planet ruling the month (lord of weekday of solar month ingress).

    BPHS 27.15. The month-lord is the weekday lord of Sun's most recent sign ingress.
    """
    sankranti_jd = _find_recent_sun_ingress(birth_jd)
    weekday = swe.day_of_week(sankranti_jd)
    lord = _WEEKDAY_LORD[weekday]
    return {p: 30.0 if p == lord else 0.0 for p in _PLANETS}


def _vara_bala(birth_jd: float) -> dict:
    """Vara Bala: planet ruling the weekday of birth.

    BPHS 27.16. The weekday lord gets 45 Virupas.
    """
    weekday = swe.day_of_week(birth_jd)
    lord = _WEEKDAY_LORD[weekday]
    return {p: 45.0 if p == lord else 0.0 for p in _PLANETS}


def _hora_bala(birth_jd: float, lat: float, lon: float) -> dict:
    """Hora Bala: planet ruling the proportional hora at birth.

    Uses proportional horas (day_length/12, night_length/12), not fixed 60-min horas.
    AstroSage parity requires proportional; JHora uses fixed 60-min (divergence).
    """
    birth_utc = _jd_to_utc_datetime(birth_jd)
    sunrise, sunset = _solar_day_refs(birth_utc, lat, lon)

    solar_tz    = timezone(timedelta(hours=lon / 15.0))
    birth_local = birth_utc.astimezone(solar_tz)
    sunrise_loc = sunrise.astimezone(solar_tz)
    sunset_loc  = sunset.astimezone(solar_tz)

    day_secs        = (sunset_loc - sunrise_loc).total_seconds()
    night_secs      = 86400.0 - day_secs
    day_hora_secs   = day_secs   / 12.0
    night_hora_secs = night_secs / 12.0

    # Hora sequence starts with weekday lord
    weekday    = swe.day_of_week(birth_jd)
    start_lord = _WEEKDAY_LORD[weekday]
    start_idx  = _HORA_SEQ.index(start_lord)

    if sunrise_loc <= birth_local <= sunset_loc:
        time_into_day = (birth_local - sunrise_loc).total_seconds()
        hora_index = int(time_into_day / day_hora_secs)
        hora_index = min(hora_index, 11)
    else:
        # Night hora
        if birth_local >= sunset_loc:
            time_into_night = (birth_local - sunset_loc).total_seconds()
        else:
            prev_sunset = sunset_loc - timedelta(hours=24)
            time_into_night = (birth_local - prev_sunset).total_seconds()
        hora_index = 12 + int(time_into_night / night_hora_secs)
        hora_index = min(hora_index, 23)

    lord = _HORA_SEQ[(start_idx + hora_index) % 7]
    return {p: 60.0 if p == lord else 0.0 for p in _PLANETS}


def _ayana_bala(birth_jd: float) -> dict:
    """Ayana Bala: strength from declination (north/south position).

    Uses PyJHora constants: (24.0 + adjusted_declination) * 1.25.
    Sun's value is doubled (special rule, BPHS 27.17).
    Moon and Saturn are south-strong (negated declination).
    Mercury uses absolute declination (always positive).
    """
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    # Declination is equatorial, not ecliptic — FLG_SIDEREAL must NOT be
    # applied here. Ayanamsa shifts ecliptic longitude, not equatorial latitude.
    flags_eq = swe.FLG_SWIEPH | swe.FLG_EQUATORIAL
    result = {}
    for p in _PLANETS:
        pid = _SWE_IDS[p]
        xx, _ = swe.calc_ut(birth_jd, pid, flags_eq)
        decl = xx[1]  # ecliptic latitude when equatorial flag used gives declination

        if p in ("Moon", "Saturn"):
            adj = -decl
        elif p == "Mercury":
            adj = abs(decl)
        else:
            adj = decl

        ab = (24.0 + adj) * 1.25
        if p == "Sun":
            ab *= 2.0
        result[p] = round(max(0.0, ab), 4)
    return result


def _yuddha_bala(
    birth_jd: float,
    planet_lons: dict,
    planet_lats: dict,
    sthana_result,
    dig_result,
    nath: dict,
    paksha: dict,
    thrib: dict,
    abda: dict,
    masa: dict,
    vara: dict,
    hora: dict,
) -> dict:
    """Yuddha Bala: strength gained/lost from planetary war.

    War only occurs between Tara Grahas when abs(lon diff) <= 1.0°.
    Victor = planet with higher ecliptic latitude.
    Strength transfer = (victor's subtotal - defeated's subtotal) /
                        abs(disc_diameter[v] - disc_diameter[d]).
    """
    yuddha = {p.lower(): 0.0 for p in _PLANETS}

    if sthana_result is None or dig_result is None:
        logger.warning("_yuddha_bala: sthana_result or dig_result is None; skipping Yuddha")
        return yuddha

    tara_list = [p for p in _PLANETS if p in _TARA_GRAHAS]

    for i, p1 in enumerate(tara_list):
        for p2 in tara_list[i + 1:]:
            lon1 = planet_lons.get(p1)
            lon2 = planet_lons.get(p2)
            if lon1 is None or lon2 is None:
                continue
            abs_diff = abs(lon1 - lon2)
            abs_diff = min(abs_diff, 360.0 - abs_diff)
            if abs_diff > 1.0:
                continue

            # Determine victor by latitude
            lat1 = planet_lats.get(p1, 0.0)
            lat2 = planet_lats.get(p2, 0.0)
            victor   = p1 if lat1 >= lat2 else p2
            defeated = p2 if victor == p1 else p1

            # Partial Kala Bala (excludes Ayana and Yuddha itself)
            def _kala_partial(p):
                return (nath[p] + paksha[p] + thrib[p] +
                        abda[p] + masa[p] + vara[p] + hora[p])

            def _sthan_total(p):
                sd = sthana_result.get(p.lower(), {})
                return sd.get("sthan_total", 0.0)

            def _dig_val(p):
                dd = dig_result.get(p.lower(), {})
                return dd.get("dig", 0.0)

            tri_v = _sthan_total(victor)   + _dig_val(victor)   + _kala_partial(victor)
            tri_d = _sthan_total(defeated) + _dig_val(defeated) + _kala_partial(defeated)

            disc_v = _DISC_DIAMETER.get(victor, 1.0)
            disc_d = _DISC_DIAMETER.get(defeated, 1.0)
            denom  = abs(disc_v - disc_d)
            if denom < 1e-9:
                logger.warning("_yuddha_bala: disc diameter difference near zero for %s vs %s", victor, defeated)
                continue

            yb = (tri_v - tri_d) / denom
            yuddha[victor.lower()]   = round(yuddha[victor.lower()] + yb, 4)
            yuddha[defeated.lower()] = round(yuddha[defeated.lower()] - yb, 4)

    return yuddha


# ── Public API ─────────────────────────────────────────────────────────────────

def compute_kala_bala(
    chart_data: dict,
    sthana_result=None,
    dig_result=None,
) -> dict:
    """Compute Kala Bala (temporal strength) for all 7 classical planets.

    Args:
        chart_data: output of calculate_chart(). Required keys:
            ["meta"]["jd_ut"], ["birth_details"]["lat"], ["birth_details"]["lon"].
        sthana_result: output of compute_sthana_bala() — needed for Yuddha Bala.
        dig_result: output of compute_dig_bala() — needed for Yuddha Bala.

    Returns:
        Dict keyed by lowercase planet name. Each value is a dict with keys:
        nathonnatha, paksha, thribhaga, abda, masa, vara, hora, ayana, yuddha,
        kala_total  (all in Virupas).
    """
    try:
        jd_ut: float = chart_data["meta"]["jd_ut"]
        lat: float   = chart_data["birth_details"]["lat"]
        lon: float   = chart_data["birth_details"]["lon"]
    except KeyError as exc:
        raise ValueError(f"compute_kala_bala: missing key in chart_data: {exc}") from exc

    swe.set_sid_mode(swe.SIDM_LAHIRI)

    # Derive planet longitudes and latitudes for Yuddha
    planet_lons: dict[str, float] = {}
    planet_lats: dict[str, float] = {}
    for p, pid in _SWE_IDS.items():
        xx, _ = swe.calc_ut(jd_ut, pid, _FLAGS_SID)
        planet_lons[p] = xx[0] % 360.0
        planet_lats[p] = xx[1]

    nath   = _nathonnatha_bala(jd_ut, lat, lon)
    paksha = _paksha_bala(jd_ut)
    thrib  = _thribhaga_bala(jd_ut, lat, lon)
    abda   = _abda_bala(jd_ut)
    masa   = _masa_bala(jd_ut)
    vara   = _vara_bala(jd_ut)
    hora   = _hora_bala(jd_ut, lat, lon)
    ayana  = _ayana_bala(jd_ut)
    yuddha = _yuddha_bala(
        jd_ut, planet_lons, planet_lats,
        sthana_result, dig_result,
        nath, paksha, thrib, abda, masa, vara, hora,
    )

    result = {}
    for p in _PLANETS:
        key = p.lower()
        total = (nath[p] + paksha[p] + thrib[p] + abda[p] +
                 masa[p] + vara[p] + hora[p] + ayana[p] + yuddha[key])
        result[key] = {
            "nathonnatha": round(nath[p],   4),
            "paksha":      round(paksha[p], 4),
            "thribhaga":   round(thrib[p],  4),
            "abda":        round(abda[p],   4),
            "masa":        round(masa[p],   4),
            "vara":        round(vara[p],   4),
            "hora":        round(hora[p],   4),
            "ayana":       round(ayana[p],  4),
            "yuddha":      round(yuddha[key], 4),
            "kala_total":  round(total,     4),
        }
    return result
