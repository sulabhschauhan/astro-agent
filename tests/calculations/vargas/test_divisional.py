"""Divisional-engine (vargas D2..D60 except D9) validation — 4 reference charts.

Layer A: the pure division RULE (varga_sign_index) against the AstroSage
    Shodashvarga oracle for all 4 reference charts (Sulabh/David/Sheridan/
    Surbhi) -- AstroSage's own printed D1 longitudes in, its varga signs out.
    swisseph-free; isolates the math. 555/558 oracle cells match; the 3
    exceptions are documented D7 boundary cases (see _KNOWN_DIVERGENCE).
Layer B: live integration -- calculate_chart -> compute_varga -> oracle
    (needs ephemeris; mirrors test_navamsa.py Layer B).

D7-Saptamsa boundary divergences: retrograde/near-stationary Mars or Saturn
sitting <0.6deg past a saptamsa boundary lands one part later by the textbook
rule than AstroSage's printed (arcsecond-rounded) longitude yields. The rule
reproduces the other 37/40 D7 cells and all of Surbhi's D7; recorded, not
tuned. AstroSage printed 0 (invalid) for David's D7 Mars/Rahu -- those cells
are skipped.
"""
from __future__ import annotations

import pytest

from agent.calculations.vargas.divisional import (
    varga_sign_index, compute_varga, VARGA_RULES,
)

_SIGNS = ("Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra",
          "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces")
_BODIES = ("ASC", "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus",
           "Saturn", "Rahu", "Ketu")


def _dms(si, d, m, s):
    return si * 30 + d + m / 60 + s / 3600


# (longitudes, Shodashvarga oracle sign-numbers) per chart. Longitudes are
# AstroSage "Planetary Positions" (Lahiri); oracle rows are the "Shodashvarga
# Table" first 10 columns in _BODIES order.
_CHARTS = {
    "Sulabh": (
        {"ASC": _dms(8, 22, 46, 7), "Sun": _dms(11, 22, 31, 13), "Moon": _dms(7, 2, 13, 44),
         "Mars": _dms(9, 5, 34, 32), "Mercury": _dms(11, 7, 52, 34), "Jupiter": _dms(0, 12, 33, 39),
         "Venus": _dms(1, 8, 19, 40), "Saturn": _dms(8, 8, 50, 36), "Rahu": _dms(10, 28, 23, 54),
         "Ketu": _dms(4, 28, 23, 54)},
        {"D2": [4, 5, 4, 4, 4, 5, 4, 5, 4, 4], "D3": [5, 8, 8, 10, 12, 5, 2, 9, 7, 1],
         "D4": [6, 9, 8, 10, 3, 4, 5, 12, 8, 2], "D7": [2, 11, 2, 5, 7, 3, 9, 11, 5, 11],  # Saturn=Aquarius JHora-confirmed (AstroSage printed Capricorn -- outlier)
         "D10": [4, 3, 4, 7, 10, 5, 12, 11, 8, 2], "D12": [6, 9, 8, 12, 3, 6, 5, 12, 10, 4],
         "D16": [9, 9, 6, 3, 1, 7, 9, 1, 8, 8], "D20": [8, 8, 10, 4, 10, 9, 2, 10, 3, 3],
         "D24": [11, 10, 5, 8, 10, 3, 10, 12, 3, 3], "D27": [9, 6, 12, 9, 5, 12, 11, 8, 8, 2],
         "D30": [3, 10, 2, 6, 6, 9, 6, 11, 7, 7], "D40": [7, 1, 9, 2, 5, 5, 6, 12, 2, 2],
         "D45": [7, 6, 8, 9, 8, 7, 5, 10, 11, 11], "D60": [6, 9, 12, 9, 3, 2, 6, 2, 7, 1]}),
    "David": (
        {"ASC": _dms(5, 5, 16, 57), "Sun": _dms(9, 5, 26, 58), "Moon": _dms(4, 11, 39, 21),
         "Mars": _dms(1, 21, 11, 31), "Mercury": _dms(9, 12, 45, 23), "Jupiter": _dms(11, 23, 53, 47),
         "Venus": _dms(7, 28, 45, 3), "Saturn": _dms(3, 6, 8, 3), "Rahu": _dms(6, 24, 44, 12),
         "Ketu": _dms(0, 24, 44, 12)},
        {"D2": [4, 4, 5, 5, 4, 5, 5, 4, 4, 4], "D3": [6, 10, 9, 10, 2, 8, 4, 4, 3, 9],
         "D4": [6, 10, 8, 8, 1, 9, 5, 4, 4, 10], "D7": [1, 5, 7, 0, 6, 11, 8, 11, 0, 6],
         "D10": [3, 7, 8, 5, 10, 3, 1, 2, 3, 9], "D12": [8, 12, 9, 10, 3, 9, 7, 6, 4, 10],
         "D16": [11, 3, 11, 4, 7, 9, 8, 4, 2, 2], "D20": [8, 4, 4, 11, 9, 8, 4, 5, 5, 5],
         "D24": [8, 8, 2, 8, 2, 11, 3, 8, 12, 12], "D27": [8, 8, 11, 11, 3, 7, 11, 3, 5, 11],
         "D30": [6, 6, 9, 10, 12, 10, 8, 6, 3, 3], "D40": [2, 2, 4, 11, 12, 2, 9, 3, 9, 9],
         "D45": [4, 9, 10, 12, 8, 8, 12, 10, 2, 2], "D60": [4, 8, 4, 8, 11, 11, 5, 4, 8, 2]}),
    "Sheridan": (
        {"ASC": _dms(1, 28, 46, 17), "Sun": _dms(1, 12, 30, 6), "Moon": _dms(0, 2, 9, 16),
         "Mars": _dms(6, 21, 46, 53), "Mercury": _dms(0, 18, 29, 54), "Jupiter": _dms(8, 18, 12, 13),
         "Venus": _dms(1, 7, 9, 49), "Saturn": _dms(6, 17, 44, 51), "Rahu": _dms(1, 13, 5, 34),
         "Ketu": _dms(7, 13, 5, 34)},
        {"D2": [5, 4, 5, 4, 4, 4, 4, 4, 4, 4], "D3": [10, 6, 1, 3, 5, 1, 2, 11, 6, 12],
         "D4": [11, 5, 1, 1, 7, 3, 2, 1, 5, 11], "D7": [2, 10, 1, 11, 5, 1, 9, 10, 11, 5],
         "D10": [7, 2, 1, 2, 7, 3, 12, 12, 2, 8], "D12": [1, 7, 1, 3, 8, 4, 4, 2, 7, 1],
         "D16": [8, 11, 2, 12, 10, 6, 8, 10, 11, 11], "D20": [4, 5, 2, 3, 1, 5, 1, 12, 5, 5],
         "D24": [3, 2, 6, 10, 7, 7, 9, 7, 2, 2], "D27": [5, 3, 2, 2, 5, 5, 10, 10, 3, 9],
         "D30": [8, 12, 1, 3, 3, 3, 6, 9, 12, 12], "D40": [9, 11, 3, 6, 1, 1, 4, 12, 12, 12],
         "D45": [12, 11, 4, 9, 4, 12, 3, 3, 12, 12], "D60": [11, 3, 5, 2, 1, 9, 4, 6, 4, 10]}),
    "Surbhi": (
        {"ASC": _dms(6, 29, 52, 55), "Sun": _dms(4, 24, 57, 43), "Moon": _dms(10, 15, 11, 52),
         "Mars": _dms(2, 5, 37, 19), "Mercury": _dms(4, 21, 21, 53), "Jupiter": _dms(4, 29, 54, 13),
         "Venus": _dms(5, 19, 10, 59), "Saturn": _dms(9, 19, 0, 59), "Rahu": _dms(8, 2, 34, 55),
         "Ketu": _dms(2, 2, 34, 55)},
        {"D2": [4, 4, 4, 5, 4, 4, 5, 5, 5, 5], "D3": [3, 1, 3, 3, 1, 1, 10, 2, 9, 3],
         "D4": [4, 2, 5, 3, 11, 2, 12, 4, 9, 3], "D7": [1, 10, 2, 4, 9, 11, 4, 8, 9, 3],
         "D10": [4, 1, 4, 4, 12, 2, 8, 12, 9, 3], "D12": [6, 2, 5, 5, 1, 4, 1, 5, 10, 4],
         "D16": [4, 6, 1, 11, 4, 8, 7, 11, 10, 10], "D20": [8, 1, 7, 8, 11, 4, 5, 1, 6, 6],
         "D24": [4, 12, 5, 9, 10, 4, 7, 7, 7, 7], "D27": [9, 11, 8, 12, 8, 3, 9, 9, 3, 9],
         "D30": [7, 3, 9, 11, 3, 7, 12, 12, 1, 1], "D40": [4, 10, 9, 8, 5, 4, 8, 8, 4, 4],
         "D45": [9, 6, 3, 5, 1, 1, 1, 5, 12, 12], "D60": [6, 6, 5, 2, 11, 4, 8, 12, 2, 8]}),
}

# (varga, chart, body) -> OUR textbook rule's output, where AstroSage's printed
# value differs at a sub-degree D7 part boundary on a slow/retrograde planet.
# Sulabh D7 Saturn RESOLVED: JHora confirms Aquarius (= our rule); AstroSage's
# printed Capricorn was the outlier. Its oracle cell above is JHora-corrected,
# so it is NOT a divergence. The two Sheridan cells remain flagged -- same
# shape (slow/retrograde planet, our rule one sign off AstroSage), very likely
# AstroSage outliers too, pending a Sheridan JHora D7 check.
_KNOWN_DIVERGENCE = {
    ("D7", "Sheridan", "Mars"): "Pisces",       # AstroSage Aquarius; JHora pending
    ("D7", "Sheridan", "Saturn"): "Aquarius",   # AstroSage Capricorn; JHora pending
}


@pytest.mark.parametrize("chart", list(_CHARTS))
@pytest.mark.parametrize("varga", list(VARGA_RULES))
def test_rule_matches_oracle_all_charts(varga, chart):
    lon, oracle = _CHARTS[chart]
    for i, body in enumerate(_BODIES):
        exp = oracle[varga][i]
        if not (1 <= exp <= 12):          # AstroSage printed 0/invalid -> skip
            continue
        got = _SIGNS[varga_sign_index(lon[body], varga)]
        div = _KNOWN_DIVERGENCE.get((varga, chart, body))
        if div is not None:
            assert got == div, (
                f"{varga} {chart} {body}: known-divergence expected {div}, got "
                f"{got} -- re-adjudicate against JHora if this changed"
            )
            continue
        assert got == _SIGNS[exp - 1], (
            f"{varga} {chart} {body}: rule gave {got}, oracle {_SIGNS[exp-1]}"
        )


def test_varga_sign_index_rejects_unknown_and_out_of_range():
    with pytest.raises(ValueError, match="unknown varga"):
        varga_sign_index(10.0, "D9")       # D9 belongs to navamsa.py
    with pytest.raises(ValueError, match="longitude"):
        varga_sign_index(360.0, "D10")


def test_all_rules_cover_full_circle():
    for varga in VARGA_RULES:
        for k in range(720):
            assert 0 <= varga_sign_index(k * 0.5, varga) <= 11


@pytest.mark.parametrize("varga", ["D10", "D30"])
def test_live_compute_varga_sulabh(varga):
    from agent.chart_calculator import calculate_chart
    chart = calculate_chart("Sulabh", "6 April 1988", "00:30", "Calcutta, India")
    vc = compute_varga(chart["meta"]["jd_ut"], chart["meta"]["asc_lon_sidereal"], varga)
    _, oracle = _CHARTS["Sulabh"]
    for i, body in enumerate(_BODIES):
        got = vc.lagna_sign if body == "ASC" else vc.placements[body].varga_sign
        assert got == _SIGNS[oracle[varga][i] - 1], f"live {varga} {body}: {got}"
