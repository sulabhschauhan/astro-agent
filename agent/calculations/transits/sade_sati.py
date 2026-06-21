"""Sade Sati and Dhaiya — Saturn transit over natal Moon.

Purpose: detect current Sade Sati status from natal Moon sign.

LOCKED DECISIONS (Session 20):
- Boundaries computed from natal Moon SIGN (Janma Rashi), NOT nakshatra.
  Matches BPHS, AstroSage, Prokerala, Drik Panchang, mainstream Indian
  astrologer convention (KN Rao, BV Raman, Sanjay Rath). Nakshatra-based
  Sade Sati is essentially absent from mainstream practice.
- Phase taxonomy:
    NONE     -- Saturn not in 12/1/2 from natal Moon
    RISING   -- Saturn in 12th from Moon (Dhaiya 1)
    PEAK     -- Saturn in 1st from Moon (Dhaiya 2, Janma Shani)
    SETTING  -- Saturn in 2nd from Moon (Dhaiya 3)
- Boundary search algorithm: binary search on monthly granularity, refine to
  daily. Bounded ~30 swe.calc_ut calls per entry/exit boundary.
- Retrograde-induced double-ingress handling: deferred to P2.2.2
  implementation prompt. Dataclass currently carries simple entry_jd /
  exit_jd; if double-ingress complications arise in fixture validation, the
  contract may extend at that time.
"""

import enum
from dataclasses import dataclass


class SadeSatiPhase(enum.Enum):
    NONE = enum.auto()
    RISING = enum.auto()
    PEAK = enum.auto()
    SETTING = enum.auto()


@dataclass(frozen=True)
class SadeSatiStatus:
    phase: SadeSatiPhase
    entry_jd: float | None      # None when phase is NONE
    exit_jd: float | None       # None when phase is NONE
    days_elapsed: int | None    # None when phase is NONE
    days_remaining: int | None  # None when phase is NONE


def compute_sade_sati(jd_ut: float, natal_moon_lon: float) -> SadeSatiStatus:
    """Determine Sade Sati status at jd_ut given natal Moon's sidereal
    longitude. Returns phase and active-window boundaries (None if phase is
    NONE).

    Args:
        jd_ut: Julian Day (UT) of the moment being evaluated.
        natal_moon_lon: Natal Moon's sidereal longitude in degrees.

    Returns:
        SadeSatiStatus with phase and boundary/duration fields.

    Raises:
        NotImplementedError: pending P2.2.2 implementation.
    """
    # TODO(P2.2.2): wire to agent.calculations.helpers.ephemeris once that
    # wrapper is built out (currently a stub per Session 19); until then,
    # the real implementation follows navamsa.py's direct swe.calc_ut
    # convention for the boundary-search swe.calc_ut calls.
    raise NotImplementedError("P2.2.2 — pending implementation; design locked Session 20")
