"""Regression pin for the Varshesha (year-lord) selector, C2.

NO desktop oracle exists for the year-lord (JHora declares none). This pins the
CONSENSUS rule transcription (benefic-aspect strongest-PV, Munthesh default) on
the three oracle annual charts. PyJHora's max-over-all rule would give Moon (2025)
/ Mars (2026) -- documented, NOT adopted.
"""
import os
import re

import pytest
import swisseph as swe

from agent.calculations.annual.varshesha import LAGNA_KEY, lord_of_the_year

_ORACLE = os.path.join(os.path.dirname(__file__), "..", "..", "..",
                       "data", "default_user", "jhora_sulabh_varshaphal.md")
_SIGNS = ["Ar", "Ta", "Ge", "Cn", "Le", "Vi", "Li", "Sc", "Sg", "Cp", "Aq", "Pi"]
_IDS = {"Sun": swe.SUN, "Moon": swe.MOON, "Mars": swe.MARS, "Mercury": swe.MERCURY,
        "Jupiter": swe.JUPITER, "Venus": swe.VENUS, "Saturn": swe.SATURN}
NATAL_LAGNA_SIGN = _SIGNS.index("Sg")
# year -> (muntha sign, night pravesh per oracle panchanga, expected winner)
CASES = {2025: ("Cp", False, "Venus"), 2026: ("Aq", True, "Jupiter"),
         2027: ("Pi", True, "Jupiter")}
# year -> {planet: (house_from_lagna, aspect)} for candidates
EXPECTED_ASPECT = {
    2025: {"Moon": (1, "malefic"), "Venus": (9, "benefic"),
           "Jupiter": (11, "benefic"), "Saturn": (9, "benefic")},
    2026: {"Jupiter": (9, "benefic"), "Mercury": (5, "benefic"),
           "Venus": (7, "malefic"), "Mars": (6, "none"), "Saturn": (6, "none")},
    2027: {"Jupiter": (8, "none")},
}


def _positions(year):
    if not os.path.exists(_ORACLE):
        pytest.skip("JHora varshaphal oracle file absent")
    md = open(_ORACLE, encoding="utf-8").read()
    a = md.index(f"### {year} (Lagna")
    block = md[a:md.index("```", md.index("```", a) + 3)]
    out = {}
    for m in re.finditer(
            r"^(Lagna|Sun|Moon|Mars|Mercury|Jupiter|Venus|Saturn)\b.*?\s(\d+) (\w\w) (\d+)' (\d+\.\d+)\"",
            block, re.M):
        key = LAGNA_KEY if m.group(1) == "Lagna" else _IDS[m.group(1)]
        out[key] = (_SIGNS.index(m.group(3)) * 30 + int(m.group(2))
                    + int(m.group(4)) / 60 + float(m.group(5)) / 3600)
    assert len(out) == 8
    return out


def _run(year):
    muntha, night, _ = CASES[year]
    return lord_of_the_year(_positions(year), NATAL_LAGNA_SIGN, _SIGNS.index(muntha), night)


@pytest.mark.parametrize("year", sorted(CASES))
def test_winner(year):
    assert _run(year)["winner"] == _IDS[CASES[year][2]]


@pytest.mark.parametrize("year", sorted(EXPECTED_ASPECT))
def test_candidate_aspects(year):
    by_planet = {c["planet"]: c for c in _run(year)["candidates"]}
    for name, (house, aspect) in EXPECTED_ASPECT[year].items():
        c = by_planet[_IDS[name]]
        assert (c["house_from_lagna"], c["aspect"]) == (house, aspect), (year, name)


def test_2025_moon_conjunct_inimical_not_chosen():
    r = _run(2025)
    moon = next(c for c in r["candidates"] if c["planet"] == swe.MOON)
    assert moon["conjunct"] and moon["pv_bala"] > 14   # strongest PV but inimical
    assert r["winner"] != swe.MOON


def test_2027_falls_to_munthesh():
    r = _run(2027)
    assert len(r["candidates"]) == 1 and "Munthesh" in r["rule_path"]
