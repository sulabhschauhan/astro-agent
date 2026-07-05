"""Shared pyswisseph sidereal-longitude wrapper.

CITATION:
  Closes the Session 44 ephemeris-consolidation debt (CLAUDE.md Locked
  Decisions: "Ephemeris consolidation debt (Session 44 flag) -- 12
  independent swe.calc_ut() call sites ... Extract to helpers/ephemeris.py
  per existing TODO markers"). A repo-wide grep found hand-rolled
  swe.calc_ut() call sites, each carrying a
  "# TODO: extract to helpers/ephemeris.py" marker, in:
    agent/calculations/strength/chesta_bala.py
    agent/calculations/strength/kala_bala.py
    agent/calculations/strength/dig_bala.py
    agent/calculations/strength/sthana_bala.py
    agent/calculations/transits/panchaka.py
    agent/calculations/transits/tarabala.py
    agent/calculations/transits/chandrabala.py
    agent/calculations/transits/sade_sati.py
    agent/calculations/transits/gochara.py
    agent/calculations/vargas/navamsa.py
    agent/calculations/core/panchanga.py
    agent/infra/chart_profile.py
    agent/calculations/core/combustion.py
  This module is the wrapper those 13 call sites are meant to migrate to.
  Migration itself is explicitly OUT OF SCOPE here and lands in separate
  follow-up prompts, one call site (or small group) at a time -- this
  prompt creates helpers/ephemeris.py only; no existing call site is
  touched.

Convention mirrored (confirmed against panchaka.py's
_moon_sidereal_longitude, chart_profile.py's _koota_natal_info_from_chart /
_saturn_sidereal_sign, and combustion.py's compute_combustion): every call
sets swe.set_sid_mode(swe.SIDM_LAHIRI) immediately before swe.calc_ut, uses
swe.FLG_SWIEPH | swe.FLG_SIDEREAL (plus swe.FLG_SPEED where daily motion is
needed -- see chart_calculator.py's _calc_planets, whose missing FLG_SPEED
was the Session 51 retrograde bug), and returns xx[0] % 360.0 for longitude.

Scope (YAGNI): no swe.set_topo, no ayanamsa parameterization (Lahiri is
hardcoded, matching every existing call site), no caching. This wrapper
does exactly what the 13 call sites above already do, nothing more.
"""

from dataclasses import dataclass

import swisseph as swe


class EphemerisError(RuntimeError):
    """A pyswisseph ephemeris calculation failed for a specific planet/JD.

    Canonical version of this exception shape (mirrors panchaka.py's
    EphemerisError, which originated it). Call sites migrating to this
    module should import EphemerisError from here rather than keeping
    their own copy.
    """

    def __init__(self, jd_ut: float, planet: int, detail: str):
        self.jd_ut = jd_ut
        self.planet = planet
        self.detail = detail
        super().__init__(
            f"ephemeris: calculation failed for planet={planet} at "
            f"jd_ut={jd_ut}: {detail}"
        )


@dataclass(frozen=True)
class SiderealPosition:
    longitude: float  # sidereal degrees, [0, 360)
    speed: float      # deg/day, signed (negative == retrograde)


def sidereal_longitude(jd_ut: float, planet: int) -> float:
    """Sidereal (Lahiri) longitude of `planet` at `jd_ut`, in [0, 360).

    Args:
        jd_ut: Julian Day (UT) of the moment being evaluated.
        planet: a swe planet constant (swe.SUN .. swe.MEAN_NODE).

    Raises:
        EphemerisError: the underlying pyswisseph call failed or returned
            an error retflag.
    """
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    flags = swe.FLG_SWIEPH | swe.FLG_SIDEREAL
    try:
        xx, ret = swe.calc_ut(jd_ut, planet, flags)
    except Exception as exc:
        raise EphemerisError(jd_ut, planet, str(exc)) from exc
    if ret < 0:
        raise EphemerisError(jd_ut, planet, f"retflag={ret}")
    return xx[0] % 360.0


def sidereal_position(jd_ut: float, planet: int) -> SiderealPosition:
    """Sidereal (Lahiri) longitude and signed daily speed of `planet`.

    This is the seam chart_calculator.py's retrograde logic and
    combustion.py's re-derived longitudes will migrate to (both need
    speed alongside longitude, per the Session 51 FLG_SPEED fix).

    Args:
        jd_ut: Julian Day (UT) of the moment being evaluated.
        planet: a swe planet constant (swe.SUN .. swe.MEAN_NODE).

    Raises:
        EphemerisError: the underlying pyswisseph call failed or returned
            an error retflag.
    """
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    flags = swe.FLG_SWIEPH | swe.FLG_SIDEREAL | swe.FLG_SPEED
    try:
        xx, ret = swe.calc_ut(jd_ut, planet, flags)
    except Exception as exc:
        raise EphemerisError(jd_ut, planet, str(exc)) from exc
    if ret < 0:
        raise EphemerisError(jd_ut, planet, f"retflag={ret}")
    return SiderealPosition(longitude=xx[0] % 360.0, speed=xx[3])
