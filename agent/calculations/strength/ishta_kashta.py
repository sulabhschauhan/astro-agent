"""Ishta Phala and Kashta Phala — benefic/malefic score extension of Shadbala.

Formula (BPHS Ch. 27, verified against JHora v8 Strengths tab, all 4 reference
charts — Sulabh, Surbhi, Sheridan, David):

    Ishta Phala  = sqrt(Uchcha_Bala * Chesta_Bala)
    Kashta Phala = sqrt((60 - Uchcha_Bala) * (60 - Chesta_Bala))

Output range ≈ [0, 60], matching JHora v8 directly. The /60-normalized scale
described in some secondary sources does NOT match JHora output.

Validation tier: JHora v8 Strengths tab, all 4 reference charts. Representative
spot-checks against oracle:
  Sulabh Sun:     Ishta 43.79 (JHora 43.66, Δ 0.13), Kashta 11.97 (JHora 12.02, Δ 0.05)
  Sulabh Mercury: Ishta  2.83 (JHora  2.75, Δ 0.08)
Deltas are within normal cross-oracle rounding seen elsewhere in this codebase.

Uchcha Bala is the "ochcha" sub-component of compute_sthana_bala() — same value,
different transliteration across sources. Chesta Bala is compute_chesta_bala()
output; Sun and Moon are NOT special-cased despite some popular sources assuming
Chesta ≈ 0 for non-retrograding bodies — chesta_bala.py supplies real values for
all 7 planets and those values are what JHora uses here.
"""

import math

from agent.calculations.strength.chesta_bala import compute_chesta_bala
from agent.calculations.strength.kala_bala import compute_kala_bala
from agent.calculations.strength.sthana_bala import compute_sthana_bala

_PLANETS = ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn"]


def compute_ishta_kashta(chart_data: dict) -> dict:
    """Compute Ishta/Kashta Phala for all 7 classical planets.

    Args:
        chart_data: output of calculate_chart(). Internally calls
            compute_sthana_bala() and compute_chesta_bala() -- caller
            does not need to pre-compute either.

    Returns:
        Dict keyed by lowercase planet name. Each value:
            ishta_phala:  float, approx range [0, 60], rounded 2 dp
            kashta_phala: float, approx range [0, 60], rounded 2 dp
            net:          float -- ishta_phala - kashta_phala, rounded 2 dp
            uchcha_bala:  float -- ochcha sub-component used, for traceability
            chesta_bala:  float -- chesta value used, for traceability

    Raises:
        ValueError/RuntimeError: propagated from compute_sthana_bala or
            compute_chesta_bala on malformed chart_data or ephemeris failure.
    """
    sthana = compute_sthana_bala(chart_data)

    # compute_chesta_bala needs paksha and ayana extracted from kala_bala.
    # Only those two sub-keys are consumed; kala_total is not used here, so
    # calling without sthana_result/dig_result (for Yuddha) is correct.
    kala = compute_kala_bala(chart_data)
    paksha_result = {p: kala[p]["paksha"] for p in _PLANETS}
    ayana_result  = {p.capitalize(): kala[p]["ayana"] for p in _PLANETS}

    chesta = compute_chesta_bala(chart_data, paksha_result, ayana_result)

    result: dict = {}
    for p in _PLANETS:
        uchcha = sthana[p]["ochcha"]
        ch     = chesta[p]["chesta"]

        # max(0, ...) guards against sub-zero floating-point noise at boundary.
        ishta_sq  = max(0.0, uchcha * ch)
        kashta_sq = max(0.0, (60.0 - uchcha) * (60.0 - ch))

        ishta  = round(math.sqrt(ishta_sq),  2)
        kashta = round(math.sqrt(kashta_sq), 2)

        result[p] = {
            "ishta_phala":  ishta,
            "kashta_phala": kashta,
            "net":          round(ishta - kashta, 2),
            "uchcha_bala":  round(uchcha, 4),
            "chesta_bala":  round(ch, 4),
        }

    return result
