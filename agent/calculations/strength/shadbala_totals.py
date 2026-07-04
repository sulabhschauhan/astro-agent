"""Shadbala Totals — final aggregation of all 6 Shadbala components.

Sums Sthana, Dig, Kala, Chesta, Naisargika, and Drik Bala into per-planet
Virupa totals, converts to Rupas, computes ratio against BPHS minimum
requirements, and ranks all 7 planets.

Drik Bala is a real implementation validated 28/28 (4 charts × 7 planets,
±0.5 Virupa) against JHora v8 — see drik_bala.py docstring for formula
provenance.
"""

from agent.calculations.strength.chesta_bala import compute_chesta_bala
from agent.calculations.strength.dig_bala import compute_dig_bala
from agent.calculations.strength.drik_bala import compute_drik_bala
from agent.calculations.strength.kala_bala import compute_kala_bala
from agent.calculations.strength.sthana_bala import compute_sthana_bala

# Fixed natural strengths (BPHS 60/7 series), confirmed against JHora.
NAISARGIKA_BALA: dict[str, float] = {
    "sun":     60.0,
    "moon":    51.43,
    "mars":    17.14,
    "mercury": 25.71,
    "jupiter": 34.29,
    "venus":   42.86,
    "saturn":   8.57,
}

_MIN_REQUIRED: dict[str, float] = {
    "sun":     5.0,
    "moon":    6.0,
    "mars":    5.0,
    "mercury": 7.0,
    "jupiter": 6.5,
    "venus":   5.5,
    "saturn":  5.0,
}

# Iteration order matters: stable-sort tie-break gives lower-index planet the better rank.
_PLANETS: list[str] = ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn"]

_CAVEAT: str = (
    "Shadbala totals carry a residual +/-6 Virupa envelope from the "
    "documented Ayana Bala Moon/Venus divergence (see CLAUDE.md 'Known "
    "Source Divergences (V1)' -> Ayana Bala). Drik Bala is real "
    "(JHora-validated); it no longer contributes stub uncertainty."
)


def compute_shadbala_totals(chart_data: dict) -> dict:
    """Aggregate all 6 Shadbala components into per-planet totals, ratios, ranks.

    Calls all 5 real component functions internally (sthana, dig, kala, chesta,
    drik) plus the local NAISARGIKA_BALA constant. Caller does not need to
    pre-compute any component.

    Args:
        chart_data: output of calculate_chart().

    Returns:
        Dict keyed by lowercase planet name. Each value:
            sthan_total, dig, kala_total, chesta, naisargika, drik: float (Virupa)
            shadbala_virupa: float — sum of the 6 components above
            shadbala_rupa: float — shadbala_virupa / 60, rounded 2dp
            min_required: float — BPHS fixed threshold (see table below)
            ratio: float — shadbala_rupa / min_required, rounded 2dp
            rank: int — 1 (strongest) to 7 (weakest), by shadbala_virupa descending
            drik_is_stubbed: bool — always False (real since Session 46)
            caveat: str — fixed string present on every planet

    Minimum requirements (BPHS, confirmed against AstroSage fixture rows):
        Sun=5.0, Moon=6.0, Mars=5.0, Mercury=7.0, Jupiter=6.5, Venus=5.5, Saturn=5.0

    Raises:
        ValueError: propagated from any component if chart_data is malformed.
        RuntimeError: propagated from any component on ephemeris failure.
    """
    sthana_result = compute_sthana_bala(chart_data)
    dig_result    = compute_dig_bala(chart_data)
    kala_result   = compute_kala_bala(chart_data, sthana_result, dig_result)

    paksha_result = {p: kala_result[p]["paksha"] for p in kala_result}
    ayana_result  = {p.capitalize(): kala_result[p]["ayana"] for p in kala_result}

    chesta_result = compute_chesta_bala(chart_data, paksha_result, ayana_result)
    drik_result   = compute_drik_bala(chart_data)

    virupa_map: dict[str, float] = {}
    for p in _PLANETS:
        virupa_map[p] = round(
            sthana_result[p]["sthan_total"]
            + dig_result[p]["dig"]
            + kala_result[p]["kala_total"]
            + chesta_result[p]["chesta"]
            + NAISARGIKA_BALA[p]
            + drik_result[p]["drik"],
            2,
        )

    # Stable sort: _PLANETS iteration order is the tie-break (lower index wins).
    ranked = sorted(_PLANETS, key=lambda p: virupa_map[p], reverse=True)
    ranks  = {p: i + 1 for i, p in enumerate(ranked)}

    result: dict[str, dict] = {}
    for p in _PLANETS:
        virupa = virupa_map[p]
        rupa   = round(virupa / 60.0, 2)
        min_r  = _MIN_REQUIRED[p]
        result[p] = {
            "sthan_total":     sthana_result[p]["sthan_total"],
            "dig":             dig_result[p]["dig"],
            "kala_total":      kala_result[p]["kala_total"],
            "chesta":          chesta_result[p]["chesta"],
            "naisargika":      NAISARGIKA_BALA[p],
            "drik":            drik_result[p]["drik"],
            "shadbala_virupa": virupa,
            "shadbala_rupa":   rupa,
            "min_required":    min_r,
            "ratio":           round(rupa / min_r, 2),
            "rank":            ranks[p],
            "drik_is_stubbed": False,
            "caveat":          _CAVEAT,
        }
    return result
