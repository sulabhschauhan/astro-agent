"""Drik Bala — aspectual strength component of Shadbala (BPHS 27.26).

STATUS: V1 STUB. Returns 0.0 for all planets. DO NOT re-investigate
without new source material — see investigation summary below.

WHY STUBBED:
A faithful port of PyJHora's __drik_bala_calc_1 kernel (the function
PyJHora's own shad_bala() actually calls) was implemented and validated
session 37. Results:
  - Surbhi chart: 7/7 planets matched AstroSage within ±5 Virupa.
  - Sulabh chart: 4/7 matched (Sun, Mars, Mercury, Jupiter).
    Moon and Venus diverged by +16.4 and +7.7 Virupa respectively,
    DESPITE JHora and AstroSage agreeing with each other almost exactly
    on those two values (Moon: JHora +5.84 vs AstroSage +5.83; Venus:
    JHora +1.46 vs AstroSage +1.46 — both oracles converge, our port
    does not). Saturn diverged from AstroSage (+18.14 vs +10.89) but
    matched JHora almost exactly (+18.14 vs +17.46) — likely genuine
    JHora-vs-AstroSage divergence, not a kernel bug.
  - Tried and rejected: Moon paksha-dependent benefic/malefic
    classification (made Sulabh results worse, 4/7 -> 1/7).
  - Root cause unresolved: the PyJHora kernel's [180°,300°) taper
    segment appears to overweight wide-orb aspects (e.g. Moon-Venus at
    186°, 6° past exact opposition, scored 56.95/60 — implausibly high
    for an aspect that wide). Neither AstroSage's nor JHora's actual
    source formula is available to verify against.

V1.1 PATH: requires either (a) AstroSage's published Drik Bala formula
(not currently public) or (b) the newer PyJHora __drik_bala_calc_1_pvr
kernel tested against the same two charts as a fresh hypothesis — NOT
yet tried, distinct from what was rejected above.

IMPACT OF STUB (V1):
  - Shadbala totals understated by |actual Drik Bala| per planet
    (AstroSage range observed: -20.44 to +22.15 Virupa).
  - Ratio (Shadbala/minimum requirement) may be inflated for planets
    with negative true Drik Bala — e.g. Sulabh Mercury: true ratio 0.77
    (below minimum), stub ratio would read ~0.83 (appears adequate).
    Flag this explicitly if/when ratio-based answers are built (P7).
  - Rank order: usually preserved (Drik Bala small relative to Sthana
    150-240 + Kala 90-290 in observed fixture range); could flip ranks
    for planets within ~20 Virupa of each other.
  - Yoga detection (P3): UNAFFECTED. Yogas use placement/dignity/sign-
    based aspects (agent.calculations.core.aspects), not Drik Bala.

ORACLE: N/A — stubbed pending V1.1.
"""


def compute_drik_bala(chart_data: dict) -> dict:
    """V1 STUB — returns 0.0 Drik Bala for all 7 classical planets.

    See module docstring for full investigation history and V1.1 path.
    Does not raise on malformed chart_data; always returns the same
    zero-filled structure so downstream Shadbala totals can sum safely.

    Args:
        chart_data: output of calculate_chart(). Unused in V1 — accepted
            for interface compatibility with other Shadbala components.

    Returns:
        Dict keyed by lowercase planet name, each value {"drik": 0.0}.
    """
    return {
        "sun":     {"drik": 0.0},
        "moon":    {"drik": 0.0},
        "mars":    {"drik": 0.0},
        "mercury": {"drik": 0.0},
        "jupiter": {"drik": 0.0},
        "venus":   {"drik": 0.0},
        "saturn":  {"drik": 0.0},
    }
