"""Tests for agent/calculations/dashas/narayana.py -- PVR Ch.18 Narayana dasa.

Book oracles used (no ephemeris -- pure logic):
  - Table 40 structure (every row a permutation of 12 signs starting with the
    seed) + the 5 worked progression sequences (Ex.63 Sc, Ex.64 Pi, Ex.65 Cp,
    Ex.66 Le, Ex.68 Ge), PVR pp.232-240.
  - The §18.2.2 length formula vs Example 66's 12 worked cells (PVR p.236-237),
    including the exalted-Moon +1.
  - The Aq/Sc co-lord path via the Basic Rule (one co-lord in the sign -> take
    the other).

End-to-end (seed selection + per-chart lengths) is oracle-checked against JHora
Narayana on the 4 reference charts separately.
"""
from __future__ import annotations

import pytest

from agent.calculations.dashas.narayana import (
    DASA_PROGRESSION, compute_narayana_antardasha, compute_narayana_dasa,
    _count_to_lord, _length_for_lord, _lord_and_length,
)

_SIGNS = ("Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra",
          "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces")
_P9 = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu")


def _lon(sign: str, deg: float = 5.0) -> float:
    return _SIGNS.index(sign) * 30.0 + deg


# ── Table 40 structure ───────────────────────────────────────────────────────

def test_table40_has_12_seeds_x_3_cases():
    assert set(DASA_PROGRESSION) == set(_SIGNS)
    for seed, cases in DASA_PROGRESSION.items():
        assert set(cases) == {"normal", "saturn", "ketu"}


@pytest.mark.parametrize("seed", _SIGNS)
@pytest.mark.parametrize("case", ["normal", "saturn", "ketu"])
def test_table40_rows_are_permutations_starting_with_seed(seed, case):
    row = DASA_PROGRESSION[seed][case]
    assert row[0] == seed, f"{seed}/{case} must start with the seed"
    assert set(row) == set(_SIGNS), f"{seed}/{case} must be all 12 signs once"
    assert len(row) == 12


# ── Worked progression sequences (PVR examples) ──────────────────────────────

@pytest.mark.parametrize("seed,expected", [
    ("Scorpio",     "Sc Ge Cp Le Pi Li Ta Sg Cn Aq Vi Ar"),   # Ex.63
    ("Pisces",      "Pi Cn Sc Sg Ar Le Vi Cp Ta Ge Li Aq"),   # Ex.64
    ("Capricorn",   "Cp Sg Sc Li Vi Le Cn Ge Ta Ar Pi Aq"),   # Ex.65
    ("Leo",         "Le Cp Ge Sc Ar Vi Aq Cn Sg Ta Li Pi"),   # Ex.66
    ("Gemini",      "Ge Aq Li Vi Ta Cp Sg Le Ar Pi Sc Cn"),   # Ex.68 (Bill Gates)
])
def test_worked_sequences_match_book(seed, expected):
    abbr = {"Ar": "Aries", "Ta": "Taurus", "Ge": "Gemini", "Cn": "Cancer",
            "Le": "Leo", "Vi": "Virgo", "Li": "Libra", "Sc": "Scorpio",
            "Sg": "Sagittarius", "Cp": "Capricorn", "Aq": "Aquarius", "Pi": "Pisces"}
    want = tuple(abbr[t] for t in expected.split())
    assert DASA_PROGRESSION[seed]["normal"] == want


# ── Cross-validation: the COMPUTED progression vs PVR's printed Table 40 ──────
# All 36 rows (12 seeds x 3 cases) transcribed VERBATIM from PVR Table 40
# (printed p.234-235 / PDF p.245-246). The engine computes the progression from
# the movement rules; this independent transcription is the oracle. Both agreeing
# on every row is what makes the progression a derived calculation rather than a
# lookup, and closes the gap on the rows no worked example exercises.
_ABBR = {"Ar": "Aries", "Ta": "Taurus", "Ge": "Gemini", "Cn": "Cancer",
         "Le": "Leo", "Vi": "Virgo", "Li": "Libra", "Sc": "Scorpio",
         "Sg": "Sagittarius", "Cp": "Capricorn", "Aq": "Aquarius", "Pi": "Pisces"}
_TABLE40 = {
    "Aries": {"normal": "Ar Ta Ge Cn Le Vi Li Sc Sg Cp Aq Pi",
              "saturn": "Ar Ta Ge Cn Le Vi Li Sc Sg Cp Aq Pi",
              "ketu":   "Ar Pi Aq Cp Sg Sc Li Vi Le Cn Ge Ta"},
    "Taurus": {"normal": "Ta Sg Cn Aq Vi Ar Sc Ge Cp Le Pi Li",
               "saturn": "Ta Ge Cn Le Vi Li Sc Sg Cp Aq Pi Ar",
               "ketu":   "Ta Li Pi Le Cp Ge Sc Ar Vi Aq Cn Sg"},
    "Gemini": {"normal": "Ge Aq Li Vi Ta Cp Sg Le Ar Pi Sc Cn",
               "saturn": "Ge Cn Le Vi Li Sc Sg Cp Aq Pi Ar Ta",
               "ketu":   "Ge Li Aq Pi Cn Sc Sg Ar Le Vi Cp Ta"},
    "Cancer": {"normal": "Cn Ge Ta Ar Pi Aq Cp Sg Sc Li Vi Le",
               "saturn": "Cn Le Vi Li Sc Sg Cp Aq Pi Ar Ta Ge",
               "ketu":   "Cn Le Vi Li Sc Sg Cp Aq Pi Ar Ta Ge"},
    "Leo": {"normal": "Le Cp Ge Sc Ar Vi Aq Cn Sg Ta Li Pi",
            "saturn": "Le Vi Li Sc Sg Cp Aq Pi Ar Ta Ge Cn",
            "ketu":   "Le Pi Li Ta Sg Cn Aq Vi Ar Sc Ge Cp"},
    "Virgo": {"normal": "Vi Cp Ta Ge Li Aq Pi Cn Sc Sg Ar Le",
              "saturn": "Vi Li Sc Sg Cp Aq Pi Ar Ta Ge Cn Le",
              "ketu":   "Vi Ta Cp Sg Le Ar Pi Sc Cn Ge Aq Li"},
    "Libra": {"normal": "Li Sc Sg Cp Aq Pi Ar Ta Ge Cn Le Vi",
              "saturn": "Li Sc Sg Cp Aq Pi Ar Ta Ge Cn Le Vi",
              "ketu":   "Li Vi Le Cn Ge Ta Ar Pi Aq Cp Sg Sc"},
    "Scorpio": {"normal": "Sc Ge Cp Le Pi Li Ta Sg Cn Aq Vi Ar",
                "saturn": "Sc Sg Cp Aq Pi Ar Ta Ge Cn Le Vi Li",
                "ketu":   "Sc Ar Vi Aq Cn Sg Ta Li Pi Le Cp Ge"},
    "Sagittarius": {"normal": "Sg Le Ar Pi Sc Cn Ge Aq Li Vi Ta Cp",
                    "saturn": "Sg Cp Aq Pi Ar Ta Ge Cn Le Vi Li Sc",
                    "ketu":   "Sg Ar Le Vi Cp Ta Ge Li Aq Pi Cn Sc"},
    "Capricorn": {"normal": "Cp Sg Sc Li Vi Le Cn Ge Ta Ar Pi Aq",
                  "saturn": "Cp Aq Pi Ar Ta Ge Cn Le Vi Li Sc Sg",
                  "ketu":   "Cp Aq Pi Ar Ta Ge Cn Le Vi Li Sc Sg"},
    "Aquarius": {"normal": "Aq Cn Sg Ta Li Pi Le Cp Ge Sc Ar Vi",
                 "saturn": "Aq Pi Ar Ta Ge Cn Le Vi Li Sc Sg Cp",
                 "ketu":   "Aq Vi Ar Sc Ge Cp Le Pi Li Ta Sg Cn"},
    "Pisces": {"normal": "Pi Cn Sc Sg Ar Le Vi Cp Ta Ge Li Aq",
               "saturn": "Pi Ar Ta Ge Cn Le Vi Li Sc Sg Cp Aq",
               "ketu":   "Pi Sc Cn Ge Aq Li Vi Ta Cp Sg Le Ar"},
}


@pytest.mark.parametrize("seed", list(_TABLE40))
@pytest.mark.parametrize("case", ["normal", "saturn", "ketu"])
def test_computed_progression_matches_pvr_table40(seed, case):
    want = tuple(_ABBR[t] for t in _TABLE40[seed][case].split())
    assert DASA_PROGRESSION[seed][case] == want, (
        f"{seed}/{case}: computed {DASA_PROGRESSION[seed][case]} != Table 40 {want}"
    )


# ── §18.2.2 length formula vs Example 66's 12 cells ──────────────────────────

@pytest.mark.parametrize("rasi,lord,lord_sign,expected", [
    ("Leo",         "Sun",     "Cancer",   1),
    ("Capricorn",   "Saturn",  "Taurus",   8),
    ("Gemini",      "Mercury", "Leo",      2),
    ("Scorpio",     "Mars",    "Leo",      9),
    ("Aries",       "Mars",    "Leo",      4),
    ("Virgo",       "Mercury", "Leo",      1),
    ("Aquarius",    "Saturn",  "Taurus",   9),
    ("Cancer",      "Moon",    "Taurus",   3),   # Moon exalted in Taurus -> +1
    ("Sagittarius", "Jupiter", "Scorpio", 11),
    ("Taurus",      "Venus",   "Leo",      3),
    ("Libra",       "Venus",   "Leo",     10),
    ("Pisces",      "Jupiter", "Scorpio",  4),
])
def test_length_formula_example_66(rasi, lord, lord_sign, expected):
    assert _length_for_lord(rasi, lord, lord_sign) == expected


def test_count_direction_odd_vs_even_footed():
    # odd-footed counts forward, even-footed backward (from Example 66).
    assert _count_to_lord("Scorpio", "Leo") == 10     # odd-footed forward
    assert _count_to_lord("Leo", "Cancer") == 2        # even-footed backward


def test_lord_in_own_sign_is_twelve_years():
    assert _length_for_lord("Aries", "Mars", "Aries") == 12    # count==1


# ── Aq/Sc co-lord path: Basic Rule (one co-lord in the sign -> the other) ─────

def test_aquarius_colord_basic_rule_takes_the_other():
    # Saturn in Aquarius -> lord is Rahu (the other co-lord). Rahu in Gemini:
    # Aq (even-footed) back to Ge = (10-2)%12+1 = 9 -> length 8.
    occ = {
        "Sun": "Aries", "Moon": "Taurus", "Mars": "Cancer", "Mercury": "Leo",
        "Jupiter": "Virgo", "Venus": "Libra", "Saturn": "Aquarius",
        "Rahu": "Gemini", "Ketu": "Sagittarius",
    }
    lons = {p: _lon(s) for p, s in occ.items()}
    lord, years = _lord_and_length("Aquarius", occ, lons)
    assert lord == "Rahu"
    assert years == 8


# ── full compute smoke (structure + two-cycle consistency) ───────────────────

def test_compute_narayana_structure_and_two_cycles():
    occ = {
        "Sun": "Cancer", "Moon": "Taurus", "Mars": "Leo", "Mercury": "Leo",
        "Jupiter": "Scorpio", "Venus": "Leo", "Saturn": "Taurus",
        "Rahu": "Gemini", "Ketu": "Sagittarius",
    }
    lons = {p: _lon(s) for p, s in occ.items()}
    nd = compute_narayana_dasa("Aquarius", lons)
    assert nd.seed in ("Aquarius", "Leo")          # the stronger of 1st/7th
    assert len(nd.periods) == 24                     # two cycles x 12
    assert nd.periods[0].rasi == nd.seed             # first dasa is the seed
    # cycle 2 length = 12 - cycle 1 length, per rasi.
    first = {p.rasi: p.years for p in nd.periods if p.cycle == 1}
    for p in nd.periods:
        if p.cycle == 2:
            assert p.years == 12 - first[p.rasi]


# ── End-to-end oracle: Sulabh's D1 vs JHora v8 Narayana (first cycle) ─────────
# Longitudes from the AstroSage D1 (same source + values as
# tests/calculations/vargas/test_divisional.py's _CHARTS["Sulabh"]); asc
# Sagittarius. Expected first-cycle (rasi, years) transcribed from the JHora v8
# "Narayana Dasa of D-1 chart" Maha Dasa table. This exercises the full chain:
# seed selection (stronger_rasi), the Saturn-in-seed progression case, and every
# length edge -- exalted (+1), debilitated (-1), own-sign (12), and the Aq/Sc
# co-lord path (Aq via Basic Rule -> Saturn; Sc via the D5 co-lord resolution).
_SULABH = {
    "Sun": 352.520, "Moon": 212.229, "Mars": 275.576, "Mercury": 337.876,
    "Jupiter": 12.561, "Venus": 38.328, "Saturn": 248.843, "Rahu": 328.398,
    "Ketu": 148.398,
}
_SULABH_NARAYANA_C1 = [
    ("Sagittarius", 4), ("Capricorn", 1), ("Aquarius", 2), ("Pisces", 11),
    ("Aries", 10), ("Taurus", 12), ("Gemini", 8), ("Cancer", 7),
    ("Leo", 5), ("Virgo", 5), ("Libra", 7), ("Scorpio", 9),
]


def test_sulabh_narayana_end_to_end_vs_jhora():
    nd = compute_narayana_dasa("Sagittarius", dict(_SULABH))
    assert nd.seed == "Sagittarius"          # stronger of 1st (Sg) / 7th (Ge)
    assert nd.progression_case == "saturn"   # Saturn occupies the Sg seed
    cycle1 = [(p.rasi, p.years) for p in nd.periods if p.cycle == 1]
    assert cycle1 == _SULABH_NARAYANA_C1
    # second cycle mirrors (12 - first), incl. Taurus -> 0 in cycle 2.
    second = {p.rasi: p.years for p in nd.periods if p.cycle == 2}
    assert second["Taurus"] == 0 and second["Sagittarius"] == 8


# ── Antardasa (PVR S18.3) vs frozen JHora v8 oracle (Sulabh, 2026-10-23) ─────
_SULABH_NARAYANA_AD = {
    "Sagittarius": "Ar Ta Ge Cn Le Vi Li Sc Sg Cp Aq Pi",
    "Capricorn":   "Sg Cp Aq Pi Ar Ta Ge Cn Le Vi Li Sc",
    "Aquarius":    "Sg Cp Aq Pi Ar Ta Ge Cn Le Vi Li Sc",
    "Pisces":      "Ar Ta Ge Cn Le Vi Li Sc Sg Cp Aq Pi",
    "Aries":       "Cp Sg Sc Li Vi Le Cn Ge Ta Ar Pi Aq",
    "Taurus":      "Le Vi Li Sc Sg Cp Aq Pi Ar Ta Ge Cn",
    "Gemini":      "Ar Ta Ge Cn Le Vi Li Sc Sg Cp Aq Pi",
    "Cancer":      "Sg Cp Aq Pi Ar Ta Ge Cn Le Vi Li Sc",
    "Leo":         "Sg Cp Aq Pi Ar Ta Ge Cn Le Vi Li Sc",
    "Virgo":       "Ar Ta Ge Cn Le Vi Li Sc Sg Cp Aq Pi",
    "Libra":       "Cp Sg Sc Li Vi Le Cn Ge Ta Ar Pi Aq",
    "Scorpio":     "Le Vi Li Sc Sg Cp Aq Pi Ar Ta Ge Cn",
}


@pytest.mark.parametrize("dasa_rasi", list(_SULABH_NARAYANA_AD))
def test_sulabh_antardasha_matches_jhora(dasa_rasi):
    want = tuple(_ABBR[t] for t in _SULABH_NARAYANA_AD[dasa_rasi].split())
    assert compute_narayana_antardasha(dasa_rasi, dict(_SULABH)) == want


def test_antardasha_unknown_rasi_raises():
    with pytest.raises(ValueError):
        compute_narayana_antardasha("Nope", dict(_SULABH))


# Branches inert on Sulabh's chart. MD Aries -> seed = stronger(Aries, Libra).
# Put every planet in Taurus except the one under test, so the seed is decided
# by the library; we read the seed back from the library to place the planet.
def _synthetic(**placements):
    # distinct degrees so stronger_rasi never ends in an exact float tie
    lons = {p: _lon("Taurus", 2.0 + 3 * i) for i, p in enumerate(_P9)}
    lons.update({p: _lon(s, 2.0 + 3 * _P9.index(p)) for p, s in placements.items()})
    return lons


def _seed_of(dasa_rasi, lons):
    from agent.calculations.jaimini.strength import stronger_rasi
    sev = _SIGNS[(_SIGNS.index(dasa_rasi) + 6) % 12]
    return stronger_rasi(dasa_rasi, sev, lons).winner


def test_antardasha_saturn_in_seed_forces_forward():
    # Seed Gemini (Mercury lord) with Mercury in an EVEN sign (Cancer -> would
    # run backward); Saturn in the seed overrides to forward.
    base = _synthetic(Mercury="Cancer", Saturn="Gemini")
    assert _seed_of("Gemini", base) == "Gemini"
    got = compute_narayana_antardasha("Gemini", base)
    assert got[0] == "Cancer" and got[1] == "Leo"


def test_antardasha_ketu_in_seed_flips_direction():
    # Mercury in Cancer (even) -> backward; Ketu in the seed flips to forward.
    base = _synthetic(Mercury="Cancer", Ketu="Gemini")
    assert _seed_of("Gemini", base) == "Gemini"
    got = compute_narayana_antardasha("Gemini", base)
    assert got[0] == "Cancer" and got[1] == "Leo"

