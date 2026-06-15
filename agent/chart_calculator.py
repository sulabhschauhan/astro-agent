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
            longitude is derived from this.
        target_year: Gregorian year (UTC) in which to find the return.

    Returns:
        {
          "utc_datetime": tz-aware datetime (UTC),
          "local_datetime": tz-aware datetime (Asia/Kolkata),
          "sun_longitude": float,        # sidereal Sun lon at found epoch
          "natal_sun_longitude": float,
          "jd_ut": float,
        }

    Raises:
        RuntimeError: natal_data missing required fields, a pyswisseph
            calculation error, or the bisection root-finder fails to
            bracket/converge.
    """
    swe.set_sid_mode(swe.SIDM_LAHIRI)

    try:
        natal_jd = natal_data["meta"]["jd_ut"]
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
    local_dt = utc_dt.astimezone(_IST)

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
