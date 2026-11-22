"""Varsha Pravesh (Tajaka annual return) instant + annual D1 cast.

Sub-engine A only: no Muntha, year-lord, dashas.

CONVENTIONS (oracle-validated vs JHora, data/default_user/jhora_sulabh_varshaphal.md):
  Lahiri (SIDM_LAHIRI, 0, 0); positions FLG_SWIEPH|FLG_TRUEPOS; ayanamsa =
  get_ayanamsa_ex_ut (true, nutation on); Swiss .se1 files via set_ephe_path.
  Return = TRUE sidereal solar return (Newton root-find on the sidereal Sun
  back to the natal sidereal Sun), not a mean-year step.

Cast place: birthplace by default (Raman; doctrine ratified S156);
residence via cast_lat/cast_lon.

boundary_flag THRESHOLD: 2.0 deg, derived from +/-8 min birth-time
uncertainty (Lagna moves ~15"/s of time -> 8 min ~ 2 deg). Scope guard:
annual-Lagna sign assignment only. Tuning note: widen if birth-time
rectification uncertainty exceeds +/-8 min.
"""

import swisseph as swe

from agent.calculations.helpers.ephemeris import (
    EphemerisError,
    sidereal_longitude_true,
    sidereal_position_true,
)

# The Swiss .se1 ephemeris path is now configured process-globally at import
# time by agent.calculations.helpers.ephemeris_config (pulled in transitively
# via the helpers.ephemeris import above), so the whole engine -- this module
# included -- runs on .se1. This module no longer sets or restores the path
# itself: the S156 set/restore dance existed ONLY because the rest of the
# engine ran on the Moshier fallback, which is no longer the case (S162).

BOUNDARY_DEG = 2.0
_SUN_RATE = 0.9856091  # mean deg/day, Newton step denominator
_MAX_ITER = 50
_TOL_DEG = 1e-9  # ~3.6e-6 arcsec

_BODIES = [
    ("Sun", swe.SUN), ("Moon", swe.MOON), ("Mars", swe.MARS),
    ("Mercury", swe.MERCURY), ("Jupiter", swe.JUPITER), ("Venus", swe.VENUS),
    ("Saturn", swe.SATURN), ("Rahu", swe.MEAN_NODE),
]


def _wrap(d: float) -> float:
    """Wrap to (-180, 180]."""
    return (d + 180.0) % 360.0 - 180.0


def compute_varsha_pravesh(natal_jd_ut, natal_lat, natal_lon, target_year,
                           cast_lat=None, cast_lon=None):
    """Return {pravesh_jd_ut, ascendant_sid, planets_sid, boundary_flag, cast_place}.

    Raises:
        EphemerisError / RuntimeError on ephemeris failure or non-convergence.
    """
    lat = natal_lat if cast_lat is None else cast_lat
    lon = natal_lon if cast_lon is None else cast_lon

    lam0 = sidereal_longitude_true(natal_jd_ut, swe.SUN)
    try:
        jd = swe.julday(target_year, 4, 6, 0.0)
    except Exception as exc:
        raise RuntimeError(f"varsha_pravesh: julday failed for {target_year}: {exc}") from exc

    for _ in range(_MAX_ITER):
        err = _wrap(sidereal_longitude_true(jd, swe.SUN) - lam0)
        jd -= err / _SUN_RATE
        if abs(err) < _TOL_DEG:
            break
    else:
        raise RuntimeError(
            f"varsha_pravesh: root-find did not converge for {target_year} "
            f"(residual {err:.3e} deg)")

    # Longitude AND signed daily speed in one pass (FLG_SPEED leaves the
    # longitude byte-identical to the old sidereal_longitude_true call, so the
    # JHora-oracle longitude tests are unaffected). Speed sign gives retrograde,
    # which the Tajika Ithasala/Ishrafa direction needs (S169).
    planets, speeds = {}, {}
    for name, pid in _BODIES:
        pos = sidereal_position_true(jd, pid)
        planets[name] = pos.longitude
        speeds[name] = pos.speed
    planets["Ketu"] = (planets["Rahu"] + 180.0) % 360.0
    speeds["Ketu"] = speeds["Rahu"]   # Ketu moves identically to Rahu

    try:
        swe.set_sid_mode(swe.SIDM_LAHIRI, 0, 0)
        _ret, ayan = swe.get_ayanamsa_ex_ut(jd, swe.FLG_SWIEPH)
        cusps, ascmc = swe.houses_ex(jd, lat, lon, b"P")
    except Exception as exc:
        raise RuntimeError(f"varsha_pravesh: ascendant cast failed at jd={jd}: {exc}") from exc
    asc = (ascmc[0] - ayan) % 360.0

    in_sign = asc % 30.0
    return {
        "pravesh_jd_ut": jd,
        "ascendant_sid": asc,
        "planets_sid": planets,
        "planet_speeds": speeds,            # signed deg/day; < 0 == retrograde
        "retrograde": frozenset(n for n, s in speeds.items() if s < 0),
        "boundary_flag": in_sign < BOUNDARY_DEG or in_sign > 30.0 - BOUNDARY_DEG,
        "cast_place": {"lat": lat, "lon": lon},
    }
