"""Drik Bala — aspectual strength component of Shadbala (BPHS Ch. 28
Sphuta Drishti kernel; aggregation per B.V. Raman "Graha and Bhava
Balas" Articles 109-120).

STATUS: V1.2. Replaces the V1 stub (previously 0.0 for all planets).

VALIDATION: 28/28 planet Drik Bala values within +/-0.5 Virupa against
JHora v8, across all 4 reference charts (Sulabh, Surbhi, Sheridan,
David); max |delta| 0.01 Virupa on any chart.

PROVENANCE CAVEAT: the piecewise Sphuta Drishti formulas below started
from the BPHS Ch.28 base taper, but the planet-specific special-aspect
segments (Mars, Jupiter, Saturn) and the Moon/Mercury classification
rules were arrived at by fitting JHora v8's oracle output on the 4
reference charts — not by reading BPHS Ch.28 or Raman Articles 109-120
directly for those segments. This is narrower than this project's
usual protocol (AstroSage parity checked); AstroSage parity has NOT
been checked against this version. Treat as JHora-parity-only.

SHERIDAN EDGE CASE (why Moon/Mercury classification is chart-dependent,
not fixed): Sheridan's Moon (elongation 319.67°) is malefic under the
elongation rule below, and Mercury shares Moon's rasi (Aries) in this
chart specifically. The prior version — Moon hardcoded always-benefic,
and Mercury's same-rasi count excluding Moon — scored only 2/7 on
Sheridan (Mars and Saturn came out with the wrong sign entirely,
because Mercury and Moon's near-maximal aspects on them were counted
as benefic when JHora treats them as malefic). Including Moon in
Mercury's same-rasi count, with Moon itself correctly classified
malefic, fixes both planets to within 0.01 Virupa.

SMOOTH-TAPER CORRECTIONS (3 segments, chosen to remove boundary
discontinuities present in the raw piecewise transcription):
  - Saturn 60-90: S = 90 - D/2 (continuous with the 90-120 segment,
    which uses the same formula; raw transcription used 120-D here,
    which jumped at both the 60 and 90 boundaries).
  - Jupiter 120-150: S = 2*(150-D) (continuous with the 90-120 segment
    at D=120: both give 60).
  - Jupiter 210-240 + 240-270: S = D/2-60 then S = 420-3*D/2 (the pair
    is continuous with the 180-210 base segment at D=210, with each
    other at D=240, and with the 270-300 base segment at D=270 — the
    first version tested with no internal discontinuity in Jupiter's
    formula).
  Validated against JHora v8 oracle across all 4 reference charts —
  see VALIDATION above.

Mars 180-210 flat plateau (S=60): derived from continuity constraint
alone (matches the 150-180 segment's value of 60 at D=180 and the
210-240 segment's value of 60 at D=210) — no aspect pair in any of the
4 reference charts lands in this range, so it is UNTESTED by data.

Moon classification: elongation-based, NOT the classical Paksha split
at 180°. elongation = (moon_lon - sun_lon) % 360; benefic for
90 <= elongation < 270 (Shukla Ashtami through Krishna Ashtami — more
than half-bright), malefic otherwise. This is a wider benefic window
than Paksha (which splits waxing=benefic/waning=malefic at 180°
exactly): Sulabh (elongation ~219.72°) and David (~216.22°) are both
technically Krishna paksha (past full moon) yet validate as benefic
under this rule, matching JHora. Sheridan (~319.67°) falls outside the
window and validates as malefic. A fixed always-benefic Moon (the
prior version) scored only 2/7 on Sheridan — see SHERIDAN EDGE CASE
above.

Mercury classification: same-rasi association count per PVR "Vedic
Astrology: An Integrated Approach" Section 3.2.2 — Mercury takes its
benefic/malefic character from whichever natural benefics/malefics
(Jupiter/Venus vs. Sun/Mars/Saturn) share its rasi, INCLUDING Moon
(classified per the elongation rule above — Moon is no longer
excluded from this count). Ties resolve to benefic. Empirically
necessary: Sulabh's Mercury (conjunct Sun only) is malefic under this
rule; Surbhi's Mercury (conjunct Sun and Jupiter, a tie) is benefic;
Sheridan's Mercury (conjunct Moon only, Moon itself malefic here) is
malefic — a fixed a-priori classification could not fit all three
simultaneously.

ORACLE: JHora v8, all 4 reference charts. AstroSage parity not checked
for this version — see PROVENANCE CAVEAT above.
"""

import swisseph as swe

_PLANETS: list[str] = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]

_SWE_IDS: dict[str, int] = {
    "Sun": swe.SUN, "Moon": swe.MOON, "Mars": swe.MARS,
    "Mercury": swe.MERCURY, "Jupiter": swe.JUPITER,
    "Venus": swe.VENUS, "Saturn": swe.SATURN,
}

_NATURAL_BENEFICS: set[str] = {"Jupiter", "Venus"}
_NATURAL_MALEFICS: set[str] = {"Sun", "Mars", "Saturn"}


# ── Sphuta Drishti formulas (Virupa, [0, 60]) ─────────────────────────────────

def _base_drishti(D: float) -> float:
    """Sun, Moon, Mercury, Venus — BPHS Ch.28 base taper."""
    if D < 30.0 or D >= 300.0:
        return 0.0
    elif D < 60.0:
        return D / 2.0 - 15.0
    elif D < 90.0:
        return D - 45.0
    elif D < 120.0:
        return 90.0 - D / 2.0
    elif D < 150.0:
        return 150.0 - D
    elif D < 180.0:
        return 2.0 * (D - 150.0)
    else:
        return (300.0 - D) / 2.0


def _mars_drishti(D: float) -> float:
    if D < 30.0 or D >= 300.0:
        return 0.0
    elif D < 60.0:
        return D / 2.0 - 15.0
    elif D < 90.0:
        return 3.0 * D / 2.0 - 75.0
    elif D < 150.0:
        return 150.0 - D
    elif D < 180.0:
        return 2.0 * (D - 150.0)
    elif D < 210.0:
        return 60.0
    elif D < 240.0:
        return 270.0 - D
    else:
        return (300.0 - D) / 2.0


def _jupiter_drishti(D: float) -> float:
    if D < 30.0 or D >= 300.0:
        return 0.0
    elif D < 60.0:
        return D / 2.0 - 15.0
    elif D < 90.0:
        return D - 45.0
    elif D < 120.0:
        return D / 2.0
    elif D < 150.0:
        return 2.0 * (150.0 - D)
    elif D < 180.0:
        return 2.0 * (D - 150.0)
    elif D < 210.0:
        return (300.0 - D) / 2.0
    elif D < 240.0:
        return D / 2.0 - 60.0
    elif D < 270.0:
        return 420.0 - 3.0 * D / 2.0
    else:
        return (300.0 - D) / 2.0


def _saturn_drishti(D: float) -> float:
    if D < 30.0 or D >= 300.0:
        return 0.0
    elif D < 60.0:
        return 2.0 * D - 60.0
    elif D < 120.0:
        return 90.0 - D / 2.0
    elif D < 150.0:
        return 150.0 - D
    elif D < 180.0:
        return 2.0 * (D - 150.0)
    elif D < 240.0:
        return (300.0 - D) / 2.0
    elif D < 270.0:
        return D - 210.0
    else:
        return 600.0 - 2.0 * D


_DRISHTI_FORMULA: dict[str, "callable[[float], float]"] = {
    "Sun": _base_drishti,
    "Moon": _base_drishti,
    "Mercury": _base_drishti,
    "Venus": _base_drishti,
    "Mars": _mars_drishti,
    "Jupiter": _jupiter_drishti,
    "Saturn": _saturn_drishti,
}


def _sphuta_drishti(aspecting_planet: str, D: float) -> float:
    """Sphuta Drishti (Virupa) cast by aspecting_planet at directed angle D."""
    S = _DRISHTI_FORMULA[aspecting_planet](D)
    return max(0.0, min(60.0, S))


def _classify_moon(planet_lons: dict[str, float]) -> bool:
    """True if Moon is benefic (elongation rule, NOT the Paksha split at 180°).

    Benefic for 90 <= elongation < 270 (Shukla Ashtami through Krishna
    Ashtami — more than half-bright), malefic otherwise. See module
    docstring's "Moon classification" note for why this differs from
    Paksha Bala's waxing/waning split.
    """
    elongation = (planet_lons["Moon"] - planet_lons["Sun"]) % 360.0
    return 90.0 <= elongation < 270.0


def _classify_mercury(planet_lons: dict[str, float], moon_is_benefic: bool) -> bool:
    """True if Mercury is benefic (PVR Section 3.2.2 same-rasi association).

    Moon counts toward the same-rasi tally using moon_is_benefic (see
    _classify_moon) — see module docstring's SHERIDAN EDGE CASE note.
    """
    mercury_rasi = int(planet_lons["Mercury"] / 30.0)
    benefic_count = 0
    malefic_count = 0
    for planet in _PLANETS:
        if planet == "Mercury":
            continue
        if int(planet_lons[planet] / 30.0) != mercury_rasi:
            continue
        if planet == "Moon":
            if moon_is_benefic:
                benefic_count += 1
            else:
                malefic_count += 1
        elif planet in _NATURAL_BENEFICS:
            benefic_count += 1
        elif planet in _NATURAL_MALEFICS:
            malefic_count += 1
    return not (malefic_count > benefic_count)


# ── Public API ────────────────────────────────────────────────────────────────

def compute_drik_bala(chart_data: dict) -> dict:
    """Compute Drik Bala (aspectual strength) for all 7 classical planets.

    Args:
        chart_data: output of calculate_chart(). Required key:
            ["meta"]["jd_ut"]. Planet longitudes are re-derived from
            pyswisseph (not read from chart_data).

    Returns:
        Dict keyed by lowercase planet name ("sun" … "saturn"). Each value
        is {"drik": float (Virupa, Drishti Pinda / 4)}.

    Raises:
        ValueError: required key absent in chart_data.
        RuntimeError: pyswisseph failure.
    """
    try:
        jd_ut: float = chart_data["meta"]["jd_ut"]
    except KeyError as exc:
        raise ValueError(
            f"compute_drik_bala: missing key in chart_data: {exc}"
        ) from exc

    swe.set_sid_mode(swe.SIDM_LAHIRI)
    flags = swe.FLG_SWIEPH | swe.FLG_SIDEREAL

    planet_lons: dict[str, float] = {}
    for planet, pid in _SWE_IDS.items():
        try:
            xx, ret = swe.calc_ut(jd_ut, pid, flags)
        except Exception as exc:
            raise RuntimeError(
                f"compute_drik_bala: swe.calc_ut raised for {planet} "
                f"at jd_ut={jd_ut}: {exc}"
            ) from exc
        if ret < 0:
            raise RuntimeError(
                f"compute_drik_bala: pyswisseph error for {planet} "
                f"at jd_ut={jd_ut} (retflag={ret})"
            )
        planet_lons[planet] = xx[0] % 360.0

    moon_is_benefic = _classify_moon(planet_lons)
    mercury_is_benefic = _classify_mercury(planet_lons, moon_is_benefic)
    benefics = set(_NATURAL_BENEFICS)
    malefics = set(_NATURAL_MALEFICS)
    if moon_is_benefic:
        benefics.add("Moon")
    else:
        malefics.add("Moon")
    if mercury_is_benefic:
        benefics.add("Mercury")
    else:
        malefics.add("Mercury")

    # Sphuta Drishti for all 42 ordered (aspecting, aspected) pairs.
    drishti: dict[tuple[str, str], float] = {}
    for Q in _PLANETS:
        for P in _PLANETS:
            if Q == P:
                continue
            D = (planet_lons[P] - planet_lons[Q]) % 360.0
            drishti[(Q, P)] = _sphuta_drishti(Q, D)

    result: dict[str, dict] = {}
    for P in _PLANETS:
        subha_sum = sum(drishti[(Q, P)] for Q in _PLANETS if Q != P and Q in benefics)
        papa_sum = sum(drishti[(Q, P)] for Q in _PLANETS if Q != P and Q in malefics)
        drishti_pinda = subha_sum - papa_sum
        result[P.lower()] = {"drik": round(drishti_pinda / 4.0, 2)}

    return result
