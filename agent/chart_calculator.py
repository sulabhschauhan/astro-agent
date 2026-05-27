"""
chart_calculator.py
Vedic birth chart engine: pyswisseph, Lahiri ayanamsha, whole-sign houses, IST input.
Output must be verified against AstroSage before production use.
"""

import swisseph as swe
from datetime import datetime, timedelta
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
import pytz


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


# ─── Julian Day conversion ────────────────────────────────────────────────────

def to_julian_day(dob: str, tob: str) -> tuple[float, datetime]:
    """
    Parse IST birth date/time strings and return (jd_ut, utc_datetime).
    Accepted date formats: YYYY-MM-DD, D Month YYYY, D Mon YYYY, DD/MM/YYYY.
    Accepted time formats: HH:MM:SS, HH:MM.
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

    ist_dt = _IST.localize(datetime.combine(d, t))
    utc_dt = ist_dt.astimezone(pytz.utc)
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

def _calc_dasha(moon_lon: float, birth_ist: datetime) -> dict:
    """
    Compute Vimshottari dasha timeline from Moon's sidereal nakshatra.
    Returns current mahadasha/antardasha and next-period summaries.
    """
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
    cursor = birth_ist

    for i in range(27):  # 3 full cycles covers ~360 years; well beyond any life
        lord = DASHA_ORDER[(start_idx + i) % 9]
        yrs = DASHA_YEARS[lord] * remaining_frac if i == 0 else DASHA_YEARS[lord]
        end = _add_years(cursor, yrs)
        timeline.append({"lord": lord, "start": cursor, "end": end})
        cursor = end

    now = datetime.now(tz=birth_ist.tzinfo)
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
    else:
        next_5_ad = []

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
        tob:   Time of birth in IST — 'HH:MM' or 'HH:MM:SS'.
        place: Birth city string, e.g. 'Calcutta, India'.

    Returns:
        kundali_context dict structured to match kundali_summary.txt sections.
        Verify output against AstroSage before production use.
    """
    swe.set_sid_mode(swe.SIDM_LAHIRI)

    lat, lon_geo = geocode_place(place)
    jd_ut, utc_dt = to_julian_day(dob, tob)
    birth_ist = utc_dt.astimezone(_IST)

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
        "dasha": _calc_dasha(moon_lon, birth_ist),
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

    return "\n".join(lines)
