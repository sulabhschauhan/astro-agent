"""Mangal Dosha (Kuja Dosha) calculator -- P2.4.5.

Dosha definition: Mars in houses 1, 2, 4, 7, 8, or 12 from any of three
reference points (Lagna, Moon, or Venus). Any single reference point
triggering is sufficient to consider the native Manglik.

V1 cancellation rules:
  C1: Mars in own sign -- Aries (0) or Scorpio (7). Source: BPHS.
  C2: Mars exalted -- Capricorn (9). Source: BPHS.
  C3: Mars debilitated -- Cancer (3). Source: Jataka Parijata.
  C5: Jupiter conjuncts Mars (same sign) OR Jupiter aspects Mars via
      Whole Sign 5th, 7th, or 9th aspect. Source: BPHS.
      Test: jupiter_sign == mars_sign, OR
            ((jupiter_sign - mars_sign) % 12) + 1 in {5, 7, 9}.
  C7: Lagna is Cancer (3) or Leo (4) -- Mars becomes Yogakaraka (lord of
      a trine and a kendra simultaneously). Source: Jataka Parijata.

Cancellation rules excluded from V1:
  C4 (movable sign): Rule is fragmented across sources and not found in
      BPHS. Deferred to V1.1 pending source reconciliation.
  C6 (mutual Manglik): Requires two charts -- when both natives have
      has_dosha=True the doshas are said to neutralise each other.
      This is a compatibility-layer concern, not a single-chart property.
      See MANGAL_CANCELLATION_C6_MUTUAL_MANGLIK below and evaluate at
      the ashtakoot.py caller level.
  Navamsa-based rules: Require D9 chart data, out of V1 scope.
  Age-28 rule: Modern/pop astrology convention, no classical source.

Severity note: AstroSage reports "Low"/"No" Mangal Dosha labels. V1 outputs
is_cancelled (boolean) but NOT severity classification. Severity tiers
(Low/Medium/High based on trigger count or classical severity weights) are
deferred to V1.1.
"""

from dataclasses import dataclass

MANGAL_DOSHA_HOUSES: frozenset = frozenset({1, 2, 4, 7, 8, 12})

MANGAL_CANCELLATION_C6_MUTUAL_MANGLIK = "C6_mutual_manglik_requires_two_charts"
# C6 note: evaluate at ashtakoot.py caller level -- call compute_mangal_dosha
# on both charts and check both has_dosha=True; this function has no two-chart
# awareness by design.

_SIGN_NAMES = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]
_SIGN_TO_IDX: dict[str, int] = {s: i for i, s in enumerate(_SIGN_NAMES)}


@dataclass(frozen=True)
class MangalDoshaResult:
    has_dosha: bool        # Mars in a dosha house from at least one reference point
    dosha_triggers: tuple  # reference point names that triggered, e.g. ("Lagna", "Moon")
    cancellations: tuple   # rule keys that fired, e.g. ("C1_mars_own_sign",)
    is_cancelled: bool     # has_dosha=True AND at least one cancellation fired
    details: dict          # mars_sign, lagna_sign, moon_sign, venus_sign, jupiter_sign
                           # (all 0-11) + mars_house_from_lagna/moon/venus (all 1-12)
    warnings: tuple


def _house_from(mars_sign: int, ref_sign: int) -> int:
    """Whole-sign house distance from ref_sign to mars_sign, range 1-12."""
    return ((mars_sign - ref_sign) % 12) + 1


def _check_c1(mars_sign: int) -> bool:
    return mars_sign in (0, 7)  # Aries or Scorpio -- Mars own signs (BPHS)


def _check_c2(mars_sign: int) -> bool:
    return mars_sign == 9  # Capricorn -- Mars exaltation (BPHS)


def _check_c3(mars_sign: int) -> bool:
    return mars_sign == 3  # Cancer -- Mars debilitation (Jataka Parijata)


def _check_c5(mars_sign: int, jupiter_sign: int) -> bool:
    """Jupiter conjuncts Mars (same sign) OR aspects Mars via Whole Sign
    5th/7th/9th aspect (BPHS).

    The aspect check ((jupiter_sign - mars_sign) % 12) + 1 in {5, 7, 9}
    is equivalent to asking whether Jupiter's 5th, 7th, or 9th special
    aspect (i.e. the sign at offset +4/+6/+8 from Jupiter) lands on Mars:
    e.g. Jupiter at Capricorn (9), Mars at Taurus (1): ((9-1)%12)+1=9 --
    Jupiter is in Mars's 9th, i.e. Mars is in Jupiter's 5th (9+4)%12=1.
    """
    if jupiter_sign == mars_sign:
        return True
    return ((jupiter_sign - mars_sign) % 12) + 1 in {5, 7, 9}


def _check_c7(lagna_sign: int) -> bool:
    return lagna_sign in (3, 4)  # Cancer or Leo -- Mars is Yogakaraka (Jataka Parijata)


def compute_mangal_dosha(chart_data: dict) -> MangalDoshaResult:
    """Compute Mangal Dosha for a single native.

    Args:
        chart_data: dict as returned by calculate_chart(). Reads:
            chart_data["lagna_chart"]["ascendant"] -- Lagna sign string
            chart_data["planetary_positions"]["Mars"]["sign"]
            chart_data["planetary_positions"]["Moon"]["sign"]
            chart_data["planetary_positions"]["Venus"]["sign"]
            chart_data["planetary_positions"]["Jupiter"]["sign"]

    Returns:
        MangalDoshaResult (frozen dataclass).

    Raises:
        ValueError: required field missing from chart_data, or a sign
            string is not a recognised Vedic sign name.
    """
    try:
        lagna_str = chart_data["lagna_chart"]["ascendant"]
        pp = chart_data["planetary_positions"]
        mars_str = pp["Mars"]["sign"]
        moon_str = pp["Moon"]["sign"]
        venus_str = pp["Venus"]["sign"]
        jupiter_str = pp["Jupiter"]["sign"]
    except KeyError as exc:
        raise ValueError(
            f"compute_mangal_dosha: chart_data missing required field {exc}"
        ) from exc

    def _to_idx(sign_str: str, field: str) -> int:
        try:
            return _SIGN_TO_IDX[sign_str]
        except KeyError:
            raise ValueError(
                f"compute_mangal_dosha: unrecognised sign '{sign_str}' "
                f"in field '{field}'"
            ) from None

    lagna_sign = _to_idx(lagna_str, "lagna_chart.ascendant")
    mars_sign = _to_idx(mars_str, "planetary_positions.Mars.sign")
    moon_sign = _to_idx(moon_str, "planetary_positions.Moon.sign")
    venus_sign = _to_idx(venus_str, "planetary_positions.Venus.sign")
    jupiter_sign = _to_idx(jupiter_str, "planetary_positions.Jupiter.sign")

    h_lagna = _house_from(mars_sign, lagna_sign)
    h_moon = _house_from(mars_sign, moon_sign)
    h_venus = _house_from(mars_sign, venus_sign)

    triggers: list[str] = []
    if h_lagna in MANGAL_DOSHA_HOUSES:
        triggers.append("Lagna")
    if h_moon in MANGAL_DOSHA_HOUSES:
        triggers.append("Moon")
    if h_venus in MANGAL_DOSHA_HOUSES:
        triggers.append("Venus")

    has_dosha = len(triggers) > 0
    cancellations: list[str] = []

    if has_dosha:
        if _check_c1(mars_sign):
            cancellations.append("C1_mars_own_sign")
        if _check_c2(mars_sign):
            cancellations.append("C2_mars_exalted")
        if _check_c3(mars_sign):
            cancellations.append("C3_mars_debilitated")
        if _check_c5(mars_sign, jupiter_sign):
            cancellations.append("C5_jupiter_influence")
        if _check_c7(lagna_sign):
            cancellations.append("C7_yogakaraka_lagna")

    return MangalDoshaResult(
        has_dosha=has_dosha,
        dosha_triggers=tuple(triggers),
        cancellations=tuple(cancellations),
        is_cancelled=has_dosha and len(cancellations) > 0,
        details={
            "mars_sign": mars_sign,
            "lagna_sign": lagna_sign,
            "moon_sign": moon_sign,
            "venus_sign": venus_sign,
            "jupiter_sign": jupiter_sign,
            "mars_house_from_lagna": h_lagna,
            "mars_house_from_moon": h_moon,
            "mars_house_from_venus": h_venus,
        },
        warnings=(),
    )
