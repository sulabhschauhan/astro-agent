"""
chart_calculator.py
Vedic birth chart engine: pyswisseph, Lahiri ayanamsha, whole-sign houses, multi-location input.
Output must be verified against AstroSage before production use.
"""

import swisseph as swe
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
import pytz
from timezonefinder import TimezoneFinder

from agent.calculations.helpers.house_counting import resolve_house_counting_lagna  # noqa: F401  (backward compat)

# ─── Lookup tables ────────────────────────────────────────────────────────────

SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]
SIGN_LORDS = {
    "Aries": "Mars", "Taurus": "Venus", "Gemini": "Mercury", "Cancer": "Moon",
    "Leo": "Sun", "Virgo": "Mercury", "Libra": "Venus", "Scorpio": "Mars",
    "Sagittarius": "Jupiter", "Capricorn": "Saturn", "Aquarius": "Saturn",
    "Pisces": "Jupiter",
}
NAKSHATRAS = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni",
    "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Vishakha",
    "Anuradha", "Jyeshtha", "Mula", "Purva Ashadha", "Uttara Ashadha",
    "Shravana", "Dhanishtha", "Shatabhisha", "Purva Bhadrapada",
    "Uttara Bhadrapada", "Revati",
]
# Vimshottari nakshatra lords, one per nakshatra (0-indexed, 27 entries)
_NAK_LORDS = (["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu",
               "Jupiter", "Saturn", "Mercury"] * 3)

DASHA_ORDER = ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu",
               "Jupiter", "Saturn", "Mercury"]
DASHA_YEARS = {
    "Ketu": 7, "Venus": 20, "Sun": 6, "Moon": 10, "Mars": 7,
    "Rahu": 18, "Jupiter": 16, "Saturn": 19, "Mercury": 17,
}

_SWE_IDS = {
    "Sun": swe.SUN, "Moon": swe.MOON, "Mars": swe.MARS,
    "Mercury": swe.MERCURY, "Jupiter": swe.JUPITER,
    "Venus": swe.VENUS, "Saturn": swe.SATURN,
}
EXALTATION = {
    "Sun": "Aries", "Moon": "Taurus", "Mars": "Capricorn",
    "Mercury": "Virgo", "Jupiter": "Cancer", "Venus": "Pisces",
    "Saturn": "Libra",
}
DEBILITATION = {
    "Sun": "Libra", "Moon": "Scorpio", "Mars": "Cancer",
    "Mercury": "Pisces", "Jupiter": "Capricorn", "Venus": "Virgo",
    "Saturn": "Aries",
}
_OWN_SIGNS: dict[str, set[str]] = {
    "Sun": {"Leo"}, "Moon": {"Cancer"},
    "Mars": {"Aries", "Scorpio"}, "Mercury": {"Gemini", "Virgo"},
    "Jupiter": {"Sagittarius", "Pisces"}, "Venus": {"Taurus", "Libra"},
    "Saturn": {"Capricorn", "Aquarius"}, "Rahu": set(), "Ketu": set(),
}
# Parashari natural friendships: f=friends, e=enemies, n=neutral
_FRIENDS: dict[str, dict[str, set[str]]] = {
    "Sun":     {"f": {"Moon", "Mars", "Jupiter"},     "e": {"Venus", "Saturn"},     "n": {"Mercury"}},
    "Moon":    {"f": {"Sun", "Mercury"},               "e": set(),                   "n": {"Mars", "Jupiter", "Venus", "Saturn"}},
    "Mars":    {"f": {"Sun", "Moon", "Jupiter"},       "e": {"Mercury"},             "n": {"Venus", "Saturn"}},
    "Mercury": {"f": {"Sun", "Venus"},                 "e": {"Moon"},                "n": {"Mars", "Jupiter", "Saturn"}},
    "Jupiter": {"f": {"Sun", "Moon", "Mars"},          "e": {"Mercury", "Venus"},    "n": {"Saturn"}},
    "Venus":   {"f": {"Mercury", "Saturn"},            "e": {"Sun", "Moon"},         "n": {"Mars", "Jupiter"}},
    "Saturn":  {"f": {"Mercury", "Venus"},             "e": {"Sun", "Moon", "Mars"}, "n": {"Jupiter"}},
}
# Vedic special aspects (house offsets in addition to universal 7th).
# Rahu/Ketu share Jupiter's 5th and 9th special aspects.
_SPECIAL_ASPECTS: dict[str, set[int]] = {
    "Mars": {4, 8},
    "Jupiter": {5, 9},
    "Saturn": {3, 10},
    "Rahu": {5, 9},
    "Ketu": {5, 9},
}

# No longer referenced by to_julian_day, calculate_chart,
# calculate_solar_return, or build_varshaphal_chart — all now resolve the
# birth location's offset via resolve_timezone_offset()/_local_datetime().
# Retained (not removed) per Session 17 Task B3 decision.
_IST = pytz.timezone("Asia/Kolkata")
# Traditional Jyotish planet ordering for display (faster/luminaries first)
_PLANET_ORDER = {p: i for i, p in enumerate(
    ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]
)}
_DATE_FMTS = ("%Y-%m-%d", "%d %B %Y", "%d %b %Y", "%d/%m/%Y", "%d-%m-%Y")
_TIME_FMTS = ("%H:%M:%S", "%H:%M")


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _sign(lon: float) -> str:
    return SIGNS[int(lon / 30) % 12]


def is_boundary_sensitive(degree_in_sign: float, threshold_deg: float = 5.0) -> bool:
    """
    True if a sidereal longitude sits within threshold_deg of either edge
    of its sign (0 deg or 30 deg) — i.e. a small cross-ephemeris residual
    could plausibly flip which sign it falls in.

    CROSS-EPHEMERIS BOUNDARY NOTE:
    Multi-chart investigation (3 charts, 3 epochs spanning 1984-2026) found
    pyswisseph vs AstroSage ayanamsa differs by a constant ~2.2 arcsec, but
    Sun/Moon longitude residuals up to ~48 arcsec were observed and did not
    resolve to any single ephemeris flag combination — an irreducible
    discrepancy (same class as the Vimshottari +-37-day drift, see
    _calc_dasha's DASHA ACCURACY NOTE).
    For boundary-dependent results (Lagna, house cusps, Muntha, ...) this
    residual is amplified by epoch-finding sensitivity: e.g. the ~26 arcsec
    Sun-longitude residual behind calculate_solar_return's ~10m38s epoch
    offset (see its cross-reference comment) produced a ~2.4 deg Lagna
    shift — enough to cross a sign boundary. threshold_deg=5.0 is a
    generous margin covering that amplification without flagging most of
    each sign.
    TUNING NOTE: revisit threshold_deg if more reference charts narrow the
    ~2-48 arcsec residual bound above.
    """
    return degree_in_sign <= threshold_deg or degree_in_sign >= (30 - threshold_deg)


def _whole_sign_house(planet_lon: float, asc_lon: float) -> int:
    # Whole-sign: compare sign indices, not degrees (avoids wrap bug when
    # planet is in same sign as ascendant but at a lower degree).
    return ((int(planet_lon / 30) % 12) - (int(asc_lon / 30) % 12)) % 12 + 1


def _nakshatra(lon: float) -> tuple[str, int, str]:
    s = 360.0 / 27
    idx = int(lon / s) % 27
    pada = int((lon % s) / (s / 4)) + 1
    return NAKSHATRAS[idx], pada, _NAK_LORDS[idx]


def _dignity(planet: str, sign: str) -> str:
    if sign == EXALTATION.get(planet):
        return "Exalted"
    if sign == DEBILITATION.get(planet):
        return "Debilitated"
    if sign in _OWN_SIGNS.get(planet, set()):
        return "Own Sign"
    if planet not in _FRIENDS:
        return "Neutral"
    sl = SIGN_LORDS[sign]
    rel = _FRIENDS[planet]
    if sl in rel["f"]:
        return "Friendly"
    if sl in rel["e"]:
        return "Inimical"
    return "Neutral"


def _add_years(dt: datetime, years: float) -> datetime:
    return dt + timedelta(days=years * 365.25)


def _fmt(dt: datetime) -> str:
    return f"{dt.day} {dt.strftime('%b')} {dt.year}"


def _ordinal(n: int) -> str:
    return {1: "1st", 2: "2nd", 3: "3rd"}.get(n, f"{n}th")


# ─── Geocoding ────────────────────────────────────────────────────────────────

def geocode_place(place: str) -> tuple[float, float]:
    """Return (lat, lon) for a city string using Nominatim."""
    geo = Nominatim(user_agent="astro-agent/1.0")
    try:
        loc = geo.geocode(place, timeout=10)
    except GeocoderTimedOut as exc:
        raise ValueError(f"Geocoding timed out for '{place}'") from exc
    if loc is None:
        raise ValueError(f"Cannot geocode: '{place}'")
    # TODO: add retry (2 attempts, 2s delay) — deferred pending manual test plan
    return loc.latitude, loc.longitude


def geocode_place_candidates(place: str, max_results: int = 5) -> list[dict]:
    """Return up to max_results candidate locations for a place string.

    Each entry: {"display_name": str, "lat": float, "lon": float}.
    display_name is the first two comma-parts of the Nominatim address.
    Returns [] on timeout or no results — never raises.
    """
    geo = Nominatim(user_agent="astro-agent/1.0")
    try:
        results = geo.geocode(place, exactly_one=False, timeout=10) or []
    except GeocoderTimedOut:
        return []
    candidates = []
    for loc in results[:max_results]:
        parts = loc.address.split(",")
        display = ", ".join(p.strip() for p in parts[:2])
        candidates.append({"display_name": display, "lat": loc.latitude, "lon": loc.longitude})
    return candidates


# ─── Timezone Resolution ───────────────────────────────────────────────────────
#
# resolve_timezone_offset() is used by to_julian_day() (and so
# calculate_chart()) to resolve the birth location's UTC offset for the
# natal JD/dasha anchor. _local_datetime() (below) builds on it for the
# "UTC instant -> local display datetime at (lat, lon)" pattern, used by
# calculate_chart() (birth_local) and calculate_solar_return() (and so
# build_varshaphal_chart(), via its epoch).

_TIMEZONE_FINDER: TimezoneFinder | None = None


def _get_timezone_finder() -> TimezoneFinder:
    global _TIMEZONE_FINDER
    if _TIMEZONE_FINDER is None:
        _TIMEZONE_FINDER = TimezoneFinder()
    return _TIMEZONE_FINDER


def resolve_timezone_offset(lat: float, lon: float, dt_naive: datetime) -> float:
    """
    Resolve the UTC offset in hours for (lat, lon) at the given naive local
    datetime.

    Maps coordinates to an IANA timezone (timezonefinder), then resolves the
    historically-correct, DST-aware UTC offset for dt_naive in that zone
    (zoneinfo). The datetime matters, not just the location: the same
    coordinates can have different offsets across history (DST, zone
    redefinitions).

    Args:
        lat: Latitude in decimal degrees.
        lon: Longitude in decimal degrees.
        dt_naive: Naive local datetime (no tzinfo) at this location.

    Returns:
        UTC offset in hours, e.g. 5.5 for IST, 0.0 for GMT, 2.0 for SAST.

    Raises:
        ValueError: dt_naive is not naive, lat/lon are out of range, no
            IANA timezone is found for the coordinates (e.g. open ocean),
            or the resolved timezone name is missing from local tzdata.
    """
    if dt_naive.tzinfo is not None:
        raise ValueError(
            f"resolve_timezone_offset: dt_naive must be naive (no tzinfo), "
            f"got {dt_naive!r}"
        )

    try:
        tz_name = _get_timezone_finder().timezone_at(lat=lat, lng=lon)
    except ValueError as exc:
        raise ValueError(
            f"resolve_timezone_offset: invalid coordinates lat={lat}, lon={lon}: {exc}"
        ) from exc

    if tz_name is None:
        raise ValueError(
            f"resolve_timezone_offset: no IANA timezone found for "
            f"lat={lat}, lon={lon} (likely open ocean / uninhabited)"
        )

    try:
        tz = ZoneInfo(tz_name)
    except ZoneInfoNotFoundError as exc:
        raise ValueError(
            f"resolve_timezone_offset: timezone '{tz_name}' not found in "
            f"local tzdata database"
        ) from exc

    offset = dt_naive.replace(tzinfo=tz).utcoffset()
    if offset is None:
        raise ValueError(
            f"resolve_timezone_offset: could not determine UTC offset for "
            f"'{tz_name}' at {dt_naive}"
        )
    return offset.total_seconds() / 3600.0


def _local_datetime(utc_dt: datetime, lat: float, lon: float) -> datetime:
    """
    Convert a tz-aware UTC datetime to local time at (lat, lon).

    Thin wrapper around resolve_timezone_offset(): resolves the UTC offset
    for (lat, lon) at this instant, then re-expresses utc_dt with that
    fixed-offset tzinfo.

    Args:
        utc_dt: tz-aware UTC datetime.
        lat: Latitude in decimal degrees.
        lon: Longitude in decimal degrees.

    Returns:
        utc_dt re-expressed with a fixed-offset tzinfo for (lat, lon).

    Raises:
        ValueError: propagated from resolve_timezone_offset() if the UTC
            offset for (lat, lon) cannot be resolved. Callers should wrap
            with their own context.
    """
    offset_hours = resolve_timezone_offset(lat, lon, utc_dt.replace(tzinfo=None))
    return utc_dt.astimezone(timezone(timedelta(hours=offset_hours)))


# ─── Julian Day conversion ────────────────────────────────────────────────────

def to_julian_day(dob: str, tob: str, lat: float, lon: float) -> tuple[float, datetime]:
    """
    Parse local birth date/time strings and return (jd_ut, utc_datetime).

    The local UTC offset is resolved from (lat, lon) and the parsed
    date/time via resolve_timezone_offset() — DST-aware and historically
    correct; no longer a hardcoded IST assumption.

    Accepted date formats: YYYY-MM-DD, D Month YYYY, D Mon YYYY, DD/MM/YYYY.
    Accepted time formats: HH:MM:SS, HH:MM.

    Args:
        dob: Date of birth string.
        tob: Time of birth string — local time at (lat, lon).
        lat: Birth location latitude in decimal degrees.
        lon: Birth location longitude in decimal degrees.

    Returns:
        (jd_ut, utc_datetime) — jd_ut is the Julian Day (UT) for pyswisseph;
        utc_datetime is a tz-aware UTC datetime.

    Raises:
        ValueError: unrecognized date/time format, or the UTC offset for
            (lat, lon) at this date/time could not be resolved.
    """
    d = None
    for fmt in _DATE_FMTS:
        try:
            d = datetime.strptime(dob.strip(), fmt).date()
            break
        except ValueError:
            pass
    if d is None:
        raise ValueError(f"Unrecognized date format: '{dob}'")

    t = None
    for fmt in _TIME_FMTS:
        try:
            t = datetime.strptime(tob.strip(), fmt).time()
            break
        except ValueError:
            pass
    if t is None:
        raise ValueError(f"Unrecognized time format: '{tob}'")

    naive_dt = datetime.combine(d, t)
    try:
        offset_hours = resolve_timezone_offset(lat, lon, naive_dt)
    except ValueError as exc:
        raise ValueError(
            f"to_julian_day: could not resolve timezone for dob='{dob}', "
            f"tob='{tob}', lat={lat}, lon={lon}: {exc}"
        ) from exc

    utc_dt = (naive_dt - timedelta(hours=offset_hours)).replace(tzinfo=pytz.utc)
    hr = utc_dt.hour + utc_dt.minute / 60.0 + utc_dt.second / 3600.0
    jd_ut = swe.julday(utc_dt.year, utc_dt.month, utc_dt.day, hr)
    return jd_ut, utc_dt


# ─── Planet positions ─────────────────────────────────────────────────────────

def _calc_planets(jd_ut: float, asc_lon: float) -> dict:
    """Compute sidereal (Lahiri) positions for all 9 grahas."""
    flags = swe.FLG_SWIEPH | swe.FLG_SIDEREAL
    planets: dict[str, dict] = {}

    for name, pid in _SWE_IDS.items():
        xx, ret = swe.calc_ut(jd_ut, pid, flags)
        if ret < 0:
            raise RuntimeError(f"pyswisseph error calculating {name} (retflag={ret})")
        lon = xx[0] % 360
        sign = _sign(lon)
        planets[name] = {
            "longitude": lon,
            "sign": sign,
            "house": _whole_sign_house(lon, asc_lon),
            "dignity": _dignity(name, sign),
            "retrograde": xx[3] < 0,
        }

    rahu_xx, _ = swe.calc_ut(jd_ut, swe.MEAN_NODE, flags)
    rahu_lon = rahu_xx[0] % 360
    ketu_lon = (rahu_lon + 180) % 360
    planets["Rahu"] = {
        "longitude": rahu_lon, "sign": _sign(rahu_lon),
        "house": _whole_sign_house(rahu_lon, asc_lon),
        "dignity": "Neutral", "retrograde": True,
    }
    planets["Ketu"] = {
        "longitude": ketu_lon, "sign": _sign(ketu_lon),
        "house": _whole_sign_house(ketu_lon, asc_lon),
        "dignity": "Neutral", "retrograde": True,
    }
    return planets


# ─── Aspects ─────────────────────────────────────────────────────────────────

def _calc_aspects(planets: dict) -> dict:
    """
    Return conjunctions, per-planet aspect lists, and aspected-by mapping.
    Every planet has a 7th-house aspect; Mars/Jupiter/Saturn have additional special aspects.
    """
    house_map: dict[int, list[str]] = {}
    for name, d in planets.items():
        house_map.setdefault(d["house"], []).append(name)

    conjunctions = [
        f"{' conjunct '.join(sorted(occ, key=lambda p: _PLANET_ORDER.get(p, 99)))} ({_ordinal(h)} house)"
        for h, occ in sorted(house_map.items())
        if len(occ) >= 2
    ]

    aspects_by_planet: dict[str, list[int]] = {}
    aspected_by: dict[str, list[str]] = {}

    for planet, d in planets.items():
        src = d["house"]
        offsets = {7} | _SPECIAL_ASPECTS.get(planet, set())
        aspected_houses = []
        for offset in sorted(offsets):
            th = ((src - 1 + offset - 1) % 12) + 1
            aspected_houses.append(th)
            for occ in house_map.get(th, []):
                if occ != planet:
                    aspected_by.setdefault(occ, []).append(planet)
        aspects_by_planet[planet] = aspected_houses

    return {
        "conjunctions": conjunctions,
        "aspects_by_planet": aspects_by_planet,
        "aspected_by": aspected_by,
    }


# ─── Vimshottari Dasha ────────────────────────────────────────────────────────

def _calc_dasha(moon_lon: float, birth_local: datetime) -> dict:
    """
    Compute Vimshottari dasha timeline from Moon's sidereal nakshatra.
    Returns current mahadasha/antardasha and next-period summaries.
    """
    # DASHA ACCURACY NOTE:
    # Current implementation uses pyswisseph with Lahiri ayanamsha.
    # Known drift: ±37 days at Antardasha level vs AstroSage.
    # Pratyantar dates computed but suppressed from output — wrong lord
    # at this granularity due to drift.
    # Same class of irreducible cross-ephemeris discrepancy as the
    # boundary-sensitivity helper (is_boundary_sensitive) and the
    # solar-return epoch offset (calculate_solar_return) — see their
    # cross-reference comments.
    #
    # BACKUP PLAN — Prokerala API (validated, not built):
    # Endpoint: GET /astrology/kundli/advanced
    # Auth: OAuth 2.0 Client Credentials
    # Credentials: PROKERALA_CLIENT_ID, PROKERALA_CLIENT_SECRET in .env
    # Returns: Mahadasha + Antardasha + Pratyantar in one call
    # Ayanamsa=1 (Lahiri), coordinates as "lat,lon" string
    # datetime as ISO 8601 with +05:30 offset
    # Activate if PDF upload approach fails or API accuracy needed.
    #
    # Dasha boundaries may drift ±37 days vs AstroSage due to ephemeris
    # precision difference in Moon longitude. Not a bug.
    nak_size = 360.0 / 27
    nak_idx = int(moon_lon / nak_size) % 27
    nak_lord = _NAK_LORDS[nak_idx]

    # Fraction of nakshatra already traversed → remaining dasha balance at birth
    elapsed_frac = (moon_lon % nak_size) / nak_size
    remaining_frac = 1.0 - elapsed_frac

    start_idx = DASHA_ORDER.index(nak_lord)
    timeline: list[dict] = []
    cursor = birth_local

    for i in range(27):  # 3 full cycles covers ~360 years; well beyond any life
        lord = DASHA_ORDER[(start_idx + i) % 9]
        yrs = DASHA_YEARS[lord] * remaining_frac if i == 0 else DASHA_YEARS[lord]
        end = _add_years(cursor, yrs)
        timeline.append({"lord": lord, "start": cursor, "end": end})
        cursor = end

    now = datetime.now(tz=birth_local.tzinfo)
    current_maha = next(
        (m for m in timeline if m["start"] <= now < m["end"]), None
    )
    if current_maha is None:
        return {"error": "Current mahadasha not found; verify birth data"}

    # Antardashas within current mahadasha
    m_lord = current_maha["lord"]
    m_start = current_maha["start"]
    m_idx = DASHA_ORDER.index(m_lord)
    m_total = DASHA_YEARS[m_lord]

    ad_list: list[dict] = []
    ad_cursor = m_start
    for i in range(9):
        ad_lord = DASHA_ORDER[(m_idx + i) % 9]
        ad_yrs = (m_total * DASHA_YEARS[ad_lord]) / 120.0
        ad_end = _add_years(ad_cursor, ad_yrs)
        ad_list.append({"lord": ad_lord, "start": ad_cursor, "end": ad_end})
        ad_cursor = ad_end

    current_ad = next(
        (a for a in ad_list if a["start"] <= now < a["end"]), None
    )

    if current_ad:
        ad_idx = next(i for i, a in enumerate(ad_list)
                      if a["start"] == current_ad["start"])
        next_5_ad = ad_list[ad_idx + 1: ad_idx + 6]

        # Not surfaced to users — ±37-day drift
        # causes wrong lord at Pratyantar granularity.
        # Integration point for Prokerala API.
        # Pratyantars within current antardasha
        ad_lord = current_ad["lord"]
        ad_total = DASHA_YEARS[ad_lord]
        ad_pt_idx = DASHA_ORDER.index(ad_lord)
        pt_list: list[dict] = []
        pt_cursor = current_ad["start"]
        for i in range(9):
            pt_lord = DASHA_ORDER[(ad_pt_idx + i) % 9]
            pt_yrs = (m_total * ad_total * DASHA_YEARS[pt_lord]) / 14400
            pt_end = _add_years(pt_cursor, pt_yrs)
            pt_list.append({"lord": pt_lord, "start": pt_cursor, "end": pt_end})
            pt_cursor = pt_end

        current_pt = next(
            (p for p in pt_list if p["start"] <= now < p["end"]), None
        )
        if current_pt:
            pt_idx = next(i for i, p in enumerate(pt_list)
                          if p["start"] == current_pt["start"])
            next_5_pt = pt_list[pt_idx + 1: pt_idx + 6]
        else:
            next_5_pt = []
    else:
        next_5_ad = []
        current_pt = None
        next_5_pt = []

    maha_idx = next(i for i, m in enumerate(timeline)
                    if m["start"] == current_maha["start"])
    next_3_maha = timeline[maha_idx + 1: maha_idx + 4]

    def _ser(d: dict) -> dict:
        return {"lord": d["lord"], "start": _fmt(d["start"]), "end": _fmt(d["end"])}

    return {
        "current_mahadasha": _ser(current_maha),
        "current_antardasha": _ser(current_ad) if current_ad else None,
        "next_5_antardashas": [_ser(a) for a in next_5_ad],
        "next_3_mahadashas": [_ser(m) for m in next_3_maha],
        "current_pratyantar": _ser(current_pt) if current_pt else None,
        "next_5_pratyantars": [_ser(p) for p in next_5_pt],
    }


# ─── Yogas / Doshas ───────────────────────────────────────────────────────────

def _calc_yogas(planets: dict) -> dict:
    """Basic Mangal Dosha and Kalsarpa Yoga checks."""
    mars_house = planets["Mars"]["house"]
    # Traditional Parashari rule: houses 1, 4, 7, 8, 12 only (2nd excluded)
    mangal_dosha = mars_house in {1, 4, 7, 8, 12}

    rahu_lon = planets["Rahu"]["longitude"]
    graha_lons = [planets[g]["longitude"]
                  for g in ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn")]
    normalized = [(lon - rahu_lon) % 360 for lon in graha_lons]
    kalsarpa = (
        all(0 < n < 180 for n in normalized) or
        all(180 < n < 360 for n in normalized)
    )

    return {
        "mangal_dosha": mangal_dosha,
        "kalsarpa_yoga": kalsarpa,
    }


# ─── Public API ───────────────────────────────────────────────────────────────

def calculate_chart(name: str, dob: str, tob: str, place: str) -> dict:
    """
    Compute a complete Vedic birth chart.

    Args:
        name:  Person's name.
        dob:   Date of birth — 'YYYY-MM-DD' or '6 April 1988'.
        tob:   Time of birth, local to `place` — 'HH:MM' or 'HH:MM:SS'.
        place: Birth city string, e.g. 'Calcutta, India'.

    Returns:
        kundali_context dict structured to match kundali_summary.txt sections.
        Verify output against AstroSage before production use.
    """
    swe.set_sid_mode(swe.SIDM_LAHIRI)

    lat, lon_geo = geocode_place(place)
    jd_ut, utc_dt = to_julian_day(dob, tob, lat, lon_geo)
    try:
        birth_local = _local_datetime(utc_dt, lat, lon_geo)
    except ValueError as exc:
        raise ValueError(
            f"calculate_chart: could not resolve timezone for "
            f"lat={lat}, lon={lon_geo}: {exc}"
        ) from exc

    # Tropical ascendant → subtract Lahiri ayanamsha for sidereal
    _, ascmc = swe.houses(jd_ut, lat, lon_geo, b"P")
    ayanamsha = swe.get_ayanamsa_ut(jd_ut)
    asc_lon = (ascmc[0] - ayanamsha) % 360
    asc_sign_idx = int(asc_lon / 30)
    asc_sign = SIGNS[asc_sign_idx]

    planets = _calc_planets(jd_ut, asc_lon)

    moon_lon = planets["Moon"]["longitude"]
    moon_nak, moon_pada, moon_nak_lord = _nakshatra(moon_lon)
    moon_sign = planets["Moon"]["sign"]

    aspect_data = _calc_aspects(planets)

    house_lords = [
        {
            "house": i + 1,
            "sign": SIGNS[(asc_sign_idx + i) % 12],
            "lord": SIGN_LORDS[SIGNS[(asc_sign_idx + i) % 12]],
            "lord_in_house": planets[
                SIGN_LORDS[SIGNS[(asc_sign_idx + i) % 12]]
            ].get("house"),
        }
        for i in range(12)
    ]

    return {
        "birth_details": {
            "name": name,
            "dob": dob,
            "tob": tob,
            "place": place,
            "lat": round(lat, 4),
            "lon": round(lon_geo, 4),
        },
        "lagna_chart": {
            "ascendant": asc_sign,
            "ascendant_lord": SIGN_LORDS[asc_sign],
            "rasi": moon_sign,
            "rasi_lord": SIGN_LORDS[moon_sign],
            "nakshatra": moon_nak,
            "nakshatra_pada": moon_pada,
            "nakshatra_lord": moon_nak_lord,
        },
        "planetary_positions": {
            planet: {
                "house": d["house"],
                "sign": d["sign"],
                "dignity": d["dignity"],
                "retrograde": d["retrograde"],
            }
            for planet, d in planets.items()
        },
        "conjunctions": aspect_data["conjunctions"],
        "house_lord_mapping": house_lords,
        "yogas_doshas": _calc_yogas(planets),
        "aspects_by_planet": aspect_data["aspects_by_planet"],
        "aspected_by": aspect_data["aspected_by"],
        "dasha": _calc_dasha(moon_lon, birth_local),
        "meta": {
            "ayanamsha_lahiri": round(ayanamsha, 4),
            "asc_lon_sidereal": round(asc_lon, 4),
            "jd_ut": round(jd_ut, 6),
        },
    }


def format_kundali_context(chart: dict) -> str:
    """
    Serialize a calculate_chart() dict to a human-readable string
    suitable for passing as kundali_context to astrologer.ask() or
    displaying in Streamlit.
    """
    bd = chart["birth_details"]
    lg = chart["lagna_chart"]
    pp = chart["planetary_positions"]
    hl = chart["house_lord_mapping"]
    da = chart["dasha"]
    yd = chart["yogas_doshas"]

    def _oh(n: int) -> str:
        return f"{_ordinal(n)} house"

    lines = [
        "BIRTH DETAILS",
        f"  Name: {bd['name']}",
        f"  Date of Birth: {bd['dob']}",
        f"  Time of Birth: {bd['tob']}",
        f"  Place of Birth: {bd['place']}",
        "",
        "LAGNA CHART",
        f"  Ascendant: {lg['ascendant']}",
        f"  Ascendant Lord: {lg['ascendant_lord']}",
        f"  Rasi (Moon Sign): {lg['rasi']}",
        f"  Rasi Lord: {lg['rasi_lord']}",
        f"  Nakshatra: {lg['nakshatra']} Pada {lg['nakshatra_pada']}",
        f"  Nakshatra Lord: {lg['nakshatra_lord']}",
        "",
        "PLANETARY POSITIONS",
    ]
    for planet, d in pp.items():
        retro = " (R)" if d["retrograde"] else ""
        lines.append(
            f"  {planet}: {_oh(d['house'])}, {d['sign']}, {d['dignity']}{retro}"
        )

    lines += ["", "CONJUNCTIONS"]
    lines += [f"  {c}" for c in chart["conjunctions"]] or ["  None"]

    lines += ["", "HOUSE-LORD MAPPING"]
    for h in hl:
        lines.append(
            f"  {_ordinal(h['house'])} House: {h['sign']}, "
            f"Lord {h['lord']} in {_oh(h['lord_in_house'])}"
        )

    lines += [
        "",
        "YOGAS AND DOSHAS",
        f"  Mangal Dosha: {'Yes' if yd['mangal_dosha'] else 'No'}",
        f"  Kalsarpa Yoga: {'Yes' if yd['kalsarpa_yoga'] else 'No'}",
        "",
        "DASHA TIMELINE",
        f"  Current Mahadasha: {da['current_mahadasha']['lord']} "
        f"({da['current_mahadasha']['start']} – {da['current_mahadasha']['end']})",
    ]
    if da.get("current_antardasha"):
        ad = da["current_antardasha"]
        lines.append(
            f"  Current Antardasha: {ad['lord']} ({ad['start']} – {ad['end']})"
        )

    next_ads = da.get("next_5_antardashas") or []
    if next_ads:
        lines.append("")
        lines.append("UPCOMING ANTARDASHAS (next 5 sub-periods)")
        for a in next_ads:
            lines.append(f"  {a['lord']}: {a['start']} – {a['end']}")

    next_mahas = da.get("next_3_mahadashas") or []
    if next_mahas:
        lines.append("")
        lines.append("UPCOMING MAHADASHAS (next 3)")
        for m in next_mahas:
            lines.append(f"  {m['lord']}: {m['start']} – {m['end']}")

    return "\n".join(lines)


# ─── Solar Return (Varshaphal epoch) ──────────────────────────────────────────
#
# CROSS-EPHEMERIS NOTE: diagnostic comparison against AstroSage's published
# 2026 Varshaphal epoch found this function's root ~10m38s later than
# AstroSage's (a ~26 arcsec natal-Sun-longitude residual). Same class of
# irreducible cross-ephemeris discrepancy as the Vimshottari +-37-day drift
# (_calc_dasha's DASHA ACCURACY NOTE) and the reason build_varshaphal_chart
# flags Lagna via is_boundary_sensitive — a small residual here can shift
# the resulting Lagna by a couple of degrees.

def calculate_solar_return(natal_data: dict, target_year: int) -> dict:
    """
    Find the Varshaphal (solar return) epoch: the exact moment in
    target_year when the Sun's sidereal longitude (Lahiri ayanamsha)
    matches its longitude at the natal moment.

    Epoch only — does NOT build the Varshaphal chart (Lagna/houses/Muntha).

    Args:
        natal_data: dict as returned by calculate_chart(). Must contain
            meta["jd_ut"] (natal Julian Day, UT) — the natal sidereal Sun
            longitude is derived from this — and birth_details["lat"]/
            ["lon"] (the birth location's coordinates, used to resolve
            local_datetime's UTC offset).
        target_year: Gregorian year (UTC) in which to find the return.

    Returns:
        {
          "utc_datetime": tz-aware datetime (UTC),
          "local_datetime": tz-aware datetime (fixed UTC offset resolved
              for the birth location via resolve_timezone_offset),
          "sun_longitude": float,        # sidereal Sun lon at found epoch
          "natal_sun_longitude": float,
          "jd_ut": float,
        }

    Raises:
        RuntimeError: natal_data missing required fields, a pyswisseph
            calculation error, the bisection root-finder fails to
            bracket/converge, or the birth location's timezone offset
            could not be resolved.
    """
    swe.set_sid_mode(swe.SIDM_LAHIRI)

    try:
        natal_jd = natal_data["meta"]["jd_ut"]
        lat = natal_data["birth_details"]["lat"]
        lon_geo = natal_data["birth_details"]["lon"]
    except KeyError as exc:
        raise RuntimeError(
            f"calculate_solar_return: natal_data missing required field {exc}"
        ) from exc

    def _sun_lon(jd: float) -> float:
        xx, ret = swe.calc_ut(jd, swe.SUN, swe.FLG_SWIEPH | swe.FLG_SIDEREAL)
        if ret < 0:
            raise RuntimeError(f"pyswisseph error calculating Sun (retflag={ret})")
        return xx[0] % 360

    natal_sun_lon = _sun_lon(natal_jd)

    def _signed_diff(jd: float) -> float:
        # Sun lon minus natal lon, wrapped to (-180, 180] so the Sun's
        # ~1deg/day prograde motion produces a single monotonic zero
        # crossing for bisection, regardless of where on the 0/360
        # boundary the natal longitude falls.
        return (_sun_lon(jd) - natal_sun_lon + 180) % 360 - 180

    # Initial guess: same calendar month/day/hour in target_year. Sidereal
    # year (~365.2564d) vs the Gregorian calendar drifts ~0.011d/year, so
    # even decades apart this guess lands well within +-5 days of the
    # true return.
    _, natal_mo, natal_dy, natal_hr = swe.revjul(natal_jd)
    guess_jd = swe.julday(target_year, natal_mo, natal_dy, natal_hr)

    # +-5 day bracket: Sun moves ~0.99 deg/day, so this comfortably spans
    # the drift above on either side of the guess.
    lo, hi = guess_jd - 5.0, guess_jd + 5.0
    f_lo, f_hi = _signed_diff(lo), _signed_diff(hi)
    if not (f_lo < 0 < f_hi):
        raise RuntimeError(
            f"calculate_solar_return: could not bracket solar return for "
            f"target_year={target_year} (f_lo={f_lo:.4f} deg, "
            f"f_hi={f_hi:.4f} deg around jd {guess_jd:.4f})"
        )

    # Tolerance 1e-5 deg ~= 0.9s of time at the Sun's ~1deg/day rate.
    # A 10-day bracket needs ~log2(10 / 1e-5) ~= 20 halvings; 100 is a
    # generous cap that still fails fast if something is wrong.
    TOL_DEG = 1e-5
    MAX_ITER = 100
    for _ in range(MAX_ITER):
        mid = (lo + hi) / 2.0
        f_mid = _signed_diff(mid)
        if abs(f_mid) < TOL_DEG:
            root_jd = mid
            break
        if f_mid < 0:
            lo = mid
        else:
            hi = mid
    else:
        raise RuntimeError(
            f"calculate_solar_return: root-finder did not converge for "
            f"target_year={target_year} after {MAX_ITER} iterations "
            f"(residual={f_mid:.6f} deg)"
        )

    y, mo, dy, hr = swe.revjul(root_jd)
    utc_dt = datetime(y, mo, dy, tzinfo=pytz.utc) + timedelta(hours=hr)

    try:
        local_dt = _local_datetime(utc_dt, lat, lon_geo)
    except ValueError as exc:
        raise RuntimeError(
            f"calculate_solar_return: could not resolve timezone for "
            f"lat={lat}, lon={lon_geo}: {exc}"
        ) from exc

    return {
        "utc_datetime": utc_dt,
        "local_datetime": local_dt,
        "sun_longitude": round(_sun_lon(root_jd), 6),
        "natal_sun_longitude": round(natal_sun_lon, 6),
        "jd_ut": round(root_jd, 6),
    }


# ─── Varshaphal (Solar Return) Chart ──────────────────────────────────────────

def build_varshaphal_chart(natal_data: dict, target_year: int) -> dict:
    """
    Build the Varshaphal (solar return) chart for target_year: Lagna,
    Rasi, and full planet-to-house placements at the solar-return epoch,
    cast for the natal birth location.

    Chart placements only — Muntha and Mudda Dasha are follow-on work.

    Args:
        natal_data: dict as returned by calculate_chart(). Must contain
            meta["jd_ut"] (passed to calculate_solar_return) and
            birth_details["lat"]/birth_details["lon"] — the natal birth
            location's coordinates from geocode_place(), the same
            coordinates used to cast the natal Lagna.
        target_year: Gregorian year (UTC) for the solar return.

    Returns:
        {
          "epoch": {...},  # calculate_solar_return() output
          "lagna": str,
          "lagna_lord": str,
          "lagna_degree_in_sign": float,    # 0-30, position within lagna sign
          "lagna_boundary_sensitive": bool, # see is_boundary_sensitive()
          "rasi": str,
          "rasi_lord": str,
          "planetary_positions": {
              planet: {"house", "sign", "dignity", "retrograde"}, ...
          },
        }

    Raises:
        RuntimeError: natal_data missing required fields, a
            calculate_solar_return failure, or a pyswisseph error while
            constructing the return-epoch chart.
    """
    try:
        lat = natal_data["birth_details"]["lat"]
        lon_geo = natal_data["birth_details"]["lon"]
    except KeyError as exc:
        raise RuntimeError(
            f"build_varshaphal_chart: natal_data missing required field {exc}"
        ) from exc

    epoch = calculate_solar_return(natal_data, target_year)
    jd_ut = epoch["jd_ut"]

    swe.set_sid_mode(swe.SIDM_LAHIRI)

    try:
        # Duplicated from calculate_chart()'s Lagna/planet block (not
        # extracted — calculate_chart() is the production D1 path with no
        # regression coverage; refactoring it risks that path to save ~8
        # lines here). Natal-specific steps (dasha, aspects, yogas,
        # house-lord mapping) are intentionally not computed.
        _, ascmc = swe.houses(jd_ut, lat, lon_geo, b"P")
        ayanamsha = swe.get_ayanamsa_ut(jd_ut)
        asc_lon = (ascmc[0] - ayanamsha) % 360
        asc_sign = SIGNS[int(asc_lon / 30) % 12]
        planets = _calc_planets(jd_ut, asc_lon)
    except Exception as exc:
        raise RuntimeError(
            f"build_varshaphal_chart: chart construction failed for "
            f"target_year={target_year} (jd_ut={jd_ut}): {exc}"
        ) from exc

    moon_sign = planets["Moon"]["sign"]
    lagna_degree_in_sign = asc_lon % 30

    return {
        "epoch": epoch,
        "lagna": asc_sign,
        "lagna_lord": SIGN_LORDS[asc_sign],
        "lagna_degree_in_sign": round(lagna_degree_in_sign, 4),
        "lagna_boundary_sensitive": is_boundary_sensitive(lagna_degree_in_sign),
        "rasi": moon_sign,
        "rasi_lord": SIGN_LORDS[moon_sign],
        "planetary_positions": {
            planet: {
                "house": d["house"],
                "sign": d["sign"],
                "dignity": d["dignity"],
                "retrograde": d["retrograde"],
            }
            for planet, d in planets.items()
        },
    }


# ─── Muntha ────────────────────────────────────────────────────────────────

def calculate_muntha(natal_data: dict, varshaphal_data: dict, target_year: int, astrosage_parsed_data: dict | None = None) -> dict:
    """
    Compute Muntha: the natal Lagna sign advanced by age-in-years, placed
    as a bhav (Whole Sign house) relative to the Varshaphal Lagna.

    age = target_year - birth_year is deterministic and does not depend on
    the solar-return epoch (see playbook_export/decisions/
    ayanamsa-investigation.md, "Muntha design implication").

    Args:
        natal_data: dict as returned by calculate_chart(). Must contain
            birth_details["dob"] and lagna_chart["ascendant"] (natal
            Lagna sign).
        varshaphal_data: dict as returned by build_varshaphal_chart(). Must
            contain "lagna", "lagna_degree_in_sign", and
            "lagna_boundary_sensitive".
        target_year: Gregorian year of the Varshaphal.
        astrosage_parsed_data: optional dict as returned by astrosage_parser
            .extract_varshaphal_lagna_year() -- see
            resolve_house_counting_lagna(). Defaults to None (use this
            pipeline's computed Lagna for resolved_bhav).

    Returns:
        {
          "muntha_sign": str,
          "bhav_primary": int,          # 1-12, from computed Varshaphal Lagna (preserved)
          "bhav_alternate": int,        # only present if lagna_boundary_sensitive (preserved)
          "ambiguous": bool,            # (preserved)
          "resolved_bhav": int,         # 1-12, from resolve_house_counting_lagna
          "bhav_source": str,           # "astrosage" | "computed"
          "bhav_boundary_sensitive": bool,
        }
        bhav_primary/bhav_alternate/ambiguous are preserved for backward
        compatibility. resolved_bhav is the recommended field for new
        consumers: uses AstroSage's own stated Varshaphal Lagna when
        available and year-matched (source="astrosage"), else this
        pipeline's computed Lagna (source="computed").
        When varshaphal_data["lagna_boundary_sensitive"] is True, the
        alternate Varshaphal Lagna (previous sign if lagna_degree_in_sign <
        15, else next sign) yields bhav_alternate alongside bhav_primary —
        a single bhav would assert false confidence on what may be a
        categorical interpretive difference (different bhav = different
        life domain). When False, bhav_alternate is omitted.

    Raises:
        ValueError: natal_data or varshaphal_data is missing a required
            field, birth_details["dob"] cannot be parsed, or the resolved
            house-counting Lagna sign is not a recognized sign name.
    """
    try:
        dob = natal_data["birth_details"]["dob"]
        natal_lagna = natal_data["lagna_chart"]["ascendant"]
    except KeyError as exc:
        raise ValueError(
            f"calculate_muntha: natal_data missing required field {exc}"
        ) from exc

    try:
        varshaphal_lagna = varshaphal_data["lagna"]
        lagna_degree_in_sign = varshaphal_data["lagna_degree_in_sign"]
        boundary_sensitive = varshaphal_data["lagna_boundary_sensitive"]
    except KeyError as exc:
        raise ValueError(
            f"calculate_muntha: varshaphal_data missing required field {exc}"
        ) from exc

    birth_year = None
    for fmt in _DATE_FMTS:
        try:
            birth_year = datetime.strptime(dob.strip(), fmt).year
            break
        except ValueError:
            pass
    if birth_year is None:
        raise ValueError(f"calculate_muntha: unrecognized date format: '{dob}'")

    age = target_year - birth_year
    natal_lagna_idx = SIGNS.index(natal_lagna)
    muntha_idx = (natal_lagna_idx + age) % 12
    muntha_sign = SIGNS[muntha_idx]

    varshaphal_lagna_idx = SIGNS.index(varshaphal_lagna)
    bhav_primary = ((muntha_idx - varshaphal_lagna_idx) % 12) + 1

    resolved = resolve_house_counting_lagna(varshaphal_data, astrosage_parsed_data, target_year)
    try:
        resolved_lagna_idx = SIGNS.index(resolved["lagna_sign"])
    except ValueError as exc:
        raise ValueError(
            f"calculate_muntha: resolved house-counting Lagna "
            f"'{resolved['lagna_sign']}' is not a recognized sign"
        ) from exc
    resolved_bhav = ((muntha_idx - resolved_lagna_idx) % 12) + 1

    if boundary_sensitive:
        if lagna_degree_in_sign < 15:
            alt_lagna_idx = (varshaphal_lagna_idx - 1) % 12
        else:
            alt_lagna_idx = (varshaphal_lagna_idx + 1) % 12
        bhav_alternate = ((muntha_idx - alt_lagna_idx) % 12) + 1

        return {
            "muntha_sign": muntha_sign,
            "bhav_primary": bhav_primary,
            "bhav_alternate": bhav_alternate,
            "ambiguous": True,
            "resolved_bhav": resolved_bhav,
            "bhav_source": resolved["source"],
            "bhav_boundary_sensitive": resolved["boundary_sensitive"],
        }

    return {
        "muntha_sign": muntha_sign,
        "bhav_primary": bhav_primary,
        "ambiguous": False,
        "resolved_bhav": resolved_bhav,
        "bhav_source": resolved["source"],
        "bhav_boundary_sensitive": resolved["boundary_sensitive"],
    }



# ─── Mudda Dasha (Varshaphal Sub-Period Dasha) ────────────────────────────

def calculate_mudda_dasha(natal_data: dict, varshaphal_data: dict, target_year: int, astrosage_parsed_data: dict | None = None) -> list[dict]:
    """
    Compute the Mudda Dasha: the 9-period Varshaphal sub-period dasha for
    target_year, in cyclic Vimshottari order starting from a lord derived
    from the natal Moon's first Mahadasha lord and age.

    Formula (validated against AstroSage's published 9-period Mudda Dasha
    table; see tests/manual/mudda_dasha_*_check.py for the diagnostics that
    led here):
      1. starting_lord_index = (natal_first_mahadasha_lord_index + age) % 9,
         where age = target_year - birth_year, and
         natal_first_mahadasha_lord_index = DASHA_ORDER.index(natal_data
         ["lagna_chart"]["nakshatra_lord"]) -- the lord whose Mahadasha runs
         first at birth.
      2. 9 periods in cyclic DASHA_ORDER starting from that lord.
      3. Each lord's share = (DASHA_YEARS[lord] / 120) * 365 days, summed
         cumulatively (unrounded) from the Varshaphal epoch; each
         cumulative endpoint (not each period's share independently) is
         rounded to the nearest day to get period_end.
      4. bhav = each lord's whole-sign house offset from
         resolve_house_counting_lagna(varshaphal_data, astrosage_parsed_data,
         target_year)'s resolved Lagna sign -- i.e. recomputed from
         varshaphal_data["planetary_positions"][lord]["sign"], not read
         directly from ["house"] (which is always relative to this
         pipeline's own computed Lagna).

    Args:
        natal_data: dict as returned by calculate_chart(). Must contain
            birth_details["dob"] and lagna_chart["nakshatra_lord"].
        varshaphal_data: dict as returned by build_varshaphal_chart(). Must
            contain epoch["local_datetime"], "lagna",
            "lagna_boundary_sensitive", and planetary_positions (with a
            "sign" entry for every DASHA_ORDER lord).
        target_year: Gregorian year of the Varshaphal.
        astrosage_parsed_data: optional dict as returned by astrosage_parser
            .extract_varshaphal_lagna_year() -- see
            resolve_house_counting_lagna(). Defaults to None (use this
            pipeline's computed Lagna).

    Returns:
        list of 9 dicts, in cyclic order starting from the computed
        starting lord:
        {
          "lord": str,
          "bhav": int,             # 1-12, from the resolved house-counting Lagna
          "period_start": str,     # _fmt()-formatted date
          "period_end": str,       # _fmt()-formatted date
          "cumulative_days": int,  # rounded days from epoch to period_end
        }

    Raises:
        ValueError: natal_data or varshaphal_data is missing a required
            field, birth_details["dob"] cannot be parsed,
            lagna_chart["nakshatra_lord"] is not a recognized Vimshottari
            lord, or the resolved house-counting Lagna sign is not a
            recognized sign name.
    """
    try:
        dob = natal_data["birth_details"]["dob"]
        natal_dasha_lord = natal_data["lagna_chart"]["nakshatra_lord"]
    except KeyError as exc:
        raise ValueError(
            f"calculate_mudda_dasha: natal_data missing required field {exc}"
        ) from exc

    try:
        epoch_dt = varshaphal_data["epoch"]["local_datetime"]
        planetary_positions = varshaphal_data["planetary_positions"]
    except KeyError as exc:
        raise ValueError(
            f"calculate_mudda_dasha: varshaphal_data missing required field {exc}"
        ) from exc

    resolved_lagna = resolve_house_counting_lagna(varshaphal_data, astrosage_parsed_data, target_year)
    try:
        lagna_idx = SIGNS.index(resolved_lagna["lagna_sign"])
    except ValueError as exc:
        raise ValueError(
            f"calculate_mudda_dasha: resolved house-counting Lagna "
            f"'{resolved_lagna['lagna_sign']}' is not a recognized sign"
        ) from exc

    birth_year = None
    for fmt in _DATE_FMTS:
        try:
            birth_year = datetime.strptime(dob.strip(), fmt).year
            break
        except ValueError:
            pass
    if birth_year is None:
        raise ValueError(f"calculate_mudda_dasha: unrecognized date format: '{dob}'")

    try:
        natal_lord_idx = DASHA_ORDER.index(natal_dasha_lord)
    except ValueError as exc:
        raise ValueError(
            f"calculate_mudda_dasha: unrecognized natal nakshatra lord "
            f"'{natal_dasha_lord}'"
        ) from exc

    age = target_year - birth_year
    start_idx = (natal_lord_idx + age) % 9

    periods: list[dict] = []
    cursor = epoch_dt
    raw_cumulative = 0.0
    for i in range(9):
        lord = DASHA_ORDER[(start_idx + i) % 9]
        raw_cumulative += (DASHA_YEARS[lord] / 120.0) * 365
        cumulative_days = round(raw_cumulative)
        period_end = epoch_dt + timedelta(days=cumulative_days)

        try:
            planet_sign = planetary_positions[lord]["sign"]
        except KeyError as exc:
            raise ValueError(
                f"calculate_mudda_dasha: varshaphal_data planetary_positions "
                f"missing lord '{lord}': {exc}"
            ) from exc

        try:
            bhav = ((SIGNS.index(planet_sign) - lagna_idx) % 12) + 1
        except ValueError as exc:
            raise ValueError(
                f"calculate_mudda_dasha: planetary_positions['{lord}']['sign'] "
                f"'{planet_sign}' is not a recognized sign"
            ) from exc

        periods.append({
            "lord": lord,
            "bhav": bhav,
            "period_start": _fmt(cursor),
            "period_end": _fmt(period_end),
            "cumulative_days": cumulative_days,
        })
        cursor = period_end

    return periods


def compute_porphyry_house_cusps(jd_ut: float, lat: float, lon: float) -> dict[int, float]:
    """Sidereal Porphyry ('Sripati' in JHora) house cusp longitudes.

    Distinct from the whole-sign house scheme used elsewhere in this module.
    Required by Bhava Dig Bala (agent/calculations/strength/bhava_bala.py),
    which needs real trisected cusps — PyJHora's own Bhava Dig Bala formula
    reads these via bhava_method=2 ('Sripati method' in its drik.bhaava_madhya),
    which is mathematically equivalent to pyswisseph's hsys=b'O' (Porphyry):
    both trisect the arc between the four angular cusps (Asc/IC/Desc/MC, which
    are house-system-invariant) to place the eight intermediate cusps. See
    this session's PyJHora investigation report for the verbatim source.

    Args:
        jd_ut: Julian Day (UT).
        lat: birth latitude.
        lon: birth longitude.

    Returns:
        {1: cusp1_lon, ..., 12: cusp12_lon} — absolute sidereal longitude
        (0-360, house 1 = Ascendant) of each house cusp.

    Raises:
        RuntimeError: pyswisseph failure.
    """
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    try:
        cusps, _ascmc = swe.houses_ex(jd_ut, lat, lon, b'O', swe.FLG_SIDEREAL)
    except Exception as exc:
        raise RuntimeError(
            f"compute_porphyry_house_cusps: swe.houses_ex raised "
            f"at jd_ut={jd_ut}, lat={lat}, lon={lon}: {exc}"
        ) from exc
    # pyswisseph's houses_ex cusps tuple is 0-indexed with cusps[0] == house 1
    # (unlike the underlying C API, which is 1-indexed with a dummy slot 0).
    return {h: cusps[h - 1] % 360.0 for h in range(1, 13)}
