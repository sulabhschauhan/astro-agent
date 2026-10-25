"""Regression pin for Pancha-vargeeya bala (Raman Model A, C1).

Annual D1 longitudes are parsed from the JHora oracle file; expected values are
the engine's own frozen output. Any friendship/varga change trips this test and
forces a conscious decision.

Frozen (computed) vs JHora oracle:
  EXACT (17): all Sun (11.70 x3), Mars, Jupiter, Venus, Saturn x3, Mercury 2025/2027.
  DOCUMENTED RESIDUAL (4) -- Moon's NEUTRAL relationships score higher in JHora
  than "inimical" (3-tier Raman folds neutral into enemy); compound/4-tier/positional
  models were tested and are worse:
    Moon 2025 14.79 (oracle 15.41)   Moon 2026 4.95 (6.51)
    Moon 2027  7.56 (10.99)          Mercury 2026 5.25 (7.12)
  Year-lord ranking is unaffected by the residual (Moon still wins 2025).
"""
import os
import re

import pytest
import swisseph as swe

from agent.calculations.annual.panchavargeeya import pancha_vargeeya_bala

_ORACLE = os.path.join(os.path.dirname(__file__), "..", "..", "..",
                       "data", "default_user", "jhora_sulabh_varshaphal.md")
_SIGNS = ["Ar", "Ta", "Ge", "Cn", "Le", "Vi", "Li", "Sc", "Sg", "Cp", "Aq", "Pi"]
_IDS = {"Sun": swe.SUN, "Moon": swe.MOON, "Mars": swe.MARS, "Mercury": swe.MERCURY,
        "Jupiter": swe.JUPITER, "Venus": swe.VENUS, "Saturn": swe.SATURN}

EXPECTED = {
    2025: {"Sun": 11.70, "Moon": 14.79, "Mars": 10.12, "Mercury": 5.03,
           "Jupiter": 7.89, "Venus": 10.85, "Saturn": 6.05},
    2026: {"Sun": 11.70, "Moon": 4.95, "Mars": 10.58, "Mercury": 5.25,
           "Jupiter": 9.64, "Venus": 9.21, "Saturn": 5.12},
    2027: {"Sun": 11.70, "Moon": 7.56, "Mars": 6.59, "Mercury": 5.04,
           "Jupiter": 14.82, "Venus": 10.21, "Saturn": 5.43},
}


def _annual_longitudes(year):
    if not os.path.exists(_ORACLE):
        pytest.skip("JHora varshaphal oracle file absent")
    md = open(_ORACLE, encoding="utf-8").read()
    a = md.index(f"### {year} (Lagna")
    block = md[a:md.index("```", md.index("```", a) + 3)]
    out = {}
    for m in re.finditer(
            r"^(Sun|Moon|Mars|Mercury|Jupiter|Venus|Saturn)\b.*?\s(\d+) (\w\w) (\d+)' (\d+\.\d+)\"",
            block, re.M):
        out[_IDS[m.group(1)]] = (_SIGNS.index(m.group(3)) * 30 + int(m.group(2))
                                 + int(m.group(4)) / 60 + float(m.group(5)) / 3600)
    assert len(out) == 7, f"parsed {len(out)} planets for {year}"
    return out


@pytest.fixture(scope="module")
def results():
    return {y: pancha_vargeeya_bala(_annual_longitudes(y)) for y in EXPECTED}


@pytest.mark.parametrize("year", sorted(EXPECTED))
@pytest.mark.parametrize("planet", list(_IDS))
def test_frozen_value(results, year, planet):
    got = results[year][_IDS[planet]][0]
    assert got == pytest.approx(EXPECTED[year][planet], abs=0.01)


def test_band_thresholds(results):
    assert results[2025][swe.MOON][1] == "Powerful"       # 14.79
    assert results[2027][swe.JUPITER][1] == "Powerful"    # 14.82
    assert results[2026][swe.MOON][1] == "Weak"           # 4.95


def test_year_lord_ranking_invariant(results):
    # 2025: Varsha-Lagna lord Moon beats Venus
    assert results[2025][swe.MOON][0] > results[2025][swe.VENUS][0]
    # 2026: Jupiter tops the aspect-eligible office-bearers (Janma-Lagna lord
    # Jupiter, Varsha-Lagna lord Venus, Muntha lord Saturn). Mars (10.58) is
    # stronger but fails the Tajika aspect filter, so it is excluded.
    eligible = [swe.JUPITER, swe.VENUS, swe.SATURN]
    top = max(eligible, key=lambda p: results[2026][p][0])
    assert top == swe.JUPITER
    # 2027: Jupiter is the top of all seven
    assert max(results[2027], key=lambda p: results[2027][p][0]) == swe.JUPITER
