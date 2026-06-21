"""Transit-to-natal and transit-to-transit aspect detection.

Purpose: aspects cast by transit planets onto natal placements.

LOCKED DECISIONS (Session 20):
- Reuses aspect math from agent.calculations.core.aspects -- specifically
  signs_aspected_by() / does_planet_aspect_sign() / aspects_between(). Do
  NOT reimplement drishti rules; this module is wiring only.
- Sign-name bridging: the aspects API uses string sign names ("Aries"..
  "Pisces"), while TransitPlacement carries integer sign (1-12). This
  module owns the int->string conversion at the call boundary. A single
  SIGN_NAMES tuple is defined here as the conversion source; do NOT add
  yet-another canonical sign list elsewhere.
- ASPECTING_PLANETS (9 planets, nodes included) from core.aspects is the
  authoritative aspect-source set. Rahu/Ketu casting 5/7/9 graha drishti is
  the locked P1.3 decision -- do not re-debate.
- Aspect targets: natal planets (P2.2.3 primary scope). Natal house cusps
  via whole-sign are free derivations; expose as a secondary target type
  but mark with a TODO if specific fixture validation isn't planned yet.
"""

from dataclasses import dataclass

from agent.calculations.transits.gochara import TransitSnapshot

# Exists ONLY to bridge TransitPlacement's integer-sign convention (1-12) to
# the string-sign convention used by agent.calculations.core.aspects. Do not
# import this elsewhere -- call sites that need sign names should pull from
# core.aspects directly.
SIGN_NAMES: tuple[str, ...] = (
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
)


@dataclass(frozen=True)
class TransitAspect:
    aspecting_planet: str        # transit planet name
    aspecting_sign: int          # 1-12, sign the transit planet occupies
    target_type: str             # "natal_planet" or "natal_house"
    target_label: str            # planet name or house number as string
    aspect_house_number: int     # 5/7/9/etc. -- which classical aspect position


def compute_transit_aspects(
    snapshot: TransitSnapshot, natal_placements: tuple
) -> tuple[TransitAspect, ...]:
    """Compute aspects cast by transit planets in `snapshot` onto natal
    placements. Returns tuple of all aspect events found.

    Type of natal_placements left intentionally loose for now -- will be
    tightened at P2.2.3 prompt time once we know whether natal placements
    come from chart_calculator's dict-based output or a future dataclass
    equivalent.

    Raises:
        NotImplementedError: pending P2.2.3 implementation.
    """
    # TODO(P2.2.3): wire to agent.calculations.core.aspects
    # (signs_aspected_by / does_planet_aspect_sign / aspects_between) for
    # the actual drishti math; this module stays wiring-only per the locked
    # design above.
    raise NotImplementedError("P2.2.3 — pending implementation; design locked Session 20")
