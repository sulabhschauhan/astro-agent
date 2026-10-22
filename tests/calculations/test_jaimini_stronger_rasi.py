"""Tests for agent/calculations/jaimini/strength.py::stronger_rasi -- PVR
Ch.15 Section 15.5.2 (the Narayana-dasa seed selector).

Scope of THIS file (pure logic, no ephemeris):
  - input contract (unknown/equal signs, bad longitudes);
  - Rule 1 (occupancy) -- unambiguous, hand-verifiable;
  - result shape (frozen, hashable, diagnostics trail).

Rules 2-6 (aspect / exaltation / oddity / advancement) are NOT hand-traced
here -- a wrong hand-built oracle is worse than none (Working Style #27). They
are validated two ways, both external oracles:
  (a) PVR Exercise 26 (Chart 12, 6 pairs, answer key printed p.217) -- added
      once Chart 12's 9 placements are in hand (it is a diagram in the PDF, not
      extractable as text);
  (b) the JHora Narayana first-dasa (= stronger of 1st/7th) on the 4 reference
      charts, folded into the Narayana end-to-end oracle.
"""
from __future__ import annotations

import pytest

from agent.calculations.jaimini.strength import (
    stronger_rasi, StrongerRasiResult,
)

_SIGNS = ("Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra",
          "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces")
_P9 = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu")


def _lon(sign: str, deg: float = 5.0) -> float:
    return _SIGNS.index(sign) * 30.0 + deg


def _chart(placements: dict[str, str]) -> dict[str, float]:
    """9-planet longitude dict from a {planet: sign} map (5 deg into each)."""
    assert set(placements) == set(_P9), "must place all 9 planets"
    return {p: _lon(s) for p, s in placements.items()}


# ── input contract ──────────────────────────────────────────────────────────

def test_unknown_sign_raises():
    ch = _chart({p: "Aries" if p != "Ketu" else "Libra" for p in _P9})
    with pytest.raises(ValueError, match="canonical"):
        stronger_rasi("Xyz", "Libra", ch)


def test_equal_signs_raise():
    ch = _chart({p: "Aries" if p != "Ketu" else "Libra" for p in _P9})
    with pytest.raises(ValueError, match="must differ"):
        stronger_rasi("Aries", "Aries", ch)


def test_missing_planet_raises():
    ch = _chart({p: "Aries" if p != "Ketu" else "Libra" for p in _P9})
    del ch["Venus"]
    with pytest.raises(ValueError, match="Venus|9 keys"):
        stronger_rasi("Aries", "Libra", ch)


def test_out_of_range_longitude_raises():
    ch = _chart({p: "Aries" if p != "Ketu" else "Libra" for p in _P9})
    ch["Sun"] = 360.0
    with pytest.raises(ValueError, match="0, 360|out-of-range"):
        stronger_rasi("Aries", "Libra", ch)


# ── Rule 1: occupancy (unambiguous) ──────────────────────────────────────────

def test_rule_1_more_planets_wins():
    # Scorpio gets Mars + Jupiter (2), Taurus gets Venus (1); nothing else in
    # either sign -> Scorpio wins on rule 1.
    placements = {
        "Mars": "Scorpio", "Jupiter": "Scorpio", "Venus": "Taurus",
        "Sun": "Aries", "Moon": "Gemini", "Mercury": "Cancer",
        "Saturn": "Leo", "Rahu": "Virgo", "Ketu": "Pisces",
    }
    res = stronger_rasi("Scorpio", "Taurus", _chart(placements))
    assert res.winner == "Scorpio"
    assert res.deciding_rule == "rule_1"
    assert res.diagnostics[-1] == ("rule_1", (2, 1))


def test_rule_1_seed_style_empty_vs_occupied():
    # 1st house Aries empty, 7th house Libra holds 2 planets -> Libra is the
    # stronger (the Narayana dasa seed would be the 7th house).
    placements = {
        "Venus": "Libra", "Saturn": "Libra",
        "Sun": "Cancer", "Moon": "Leo", "Mars": "Scorpio", "Mercury": "Gemini",
        "Jupiter": "Pisces", "Rahu": "Taurus", "Ketu": "Scorpio",
    }
    res = stronger_rasi("Aries", "Libra", _chart(placements))
    assert res.winner == "Libra"
    assert res.deciding_rule == "rule_1"


# ── PVR Exercise 26 book oracle (Chart 12's D-10) ────────────────────────────
# Chart 12 (PVR p.155 / PDF p.166, "D-10 SAV Exercise") read directly from the
# diagram; cross-checked: all six Exercise-26 pairs' planet counts match these
# placements exactly. Degrees are distinct small offsets (signs are what rules
# 1-5 use; rule 6 is not reached on any of these pairs per PVR).
_CHART12_D10 = {
    "Sun": 241.0,     # Sagittarius
    "Moon": 272.0,    # Capricorn
    "Mars": 213.0,    # Scorpio
    "Mercury": 244.0,  # Sagittarius
    "Jupiter": 216.0,  # Scorpio
    "Venus": 37.0,    # Taurus
    "Saturn": 338.0,  # Pisces
    "Rahu": 189.0,    # Libra
    "Ketu": 9.0,      # Aries (opposite Rahu)
}

# PVR Exercise 26 answer key (printed p.206-207 / PDF p.216-217):
_EX26 = [
    ("Aries", "Libra", "Aries", "rule_2"),               # tie on count; Ar aspected by Jup+Mars
    ("Taurus", "Scorpio", "Scorpio", "rule_1"),          # Sc 2 vs Ta 1
    ("Gemini", "Sagittarius", "Sagittarius", "rule_1"),  # Sg 2 vs Ge 0
    ("Cancer", "Capricorn", "Capricorn", "rule_1"),      # Cp 1 vs Cn 0
    ("Leo", "Aquarius", "Aquarius", "rule_2"),           # both empty; Aq aspected by co-lord Rahu
    ("Virgo", "Pisces", "Pisces", "rule_1"),             # Pi 1 vs Vi 0
]


@pytest.mark.parametrize("a,b,winner,rule", _EX26)
def test_exercise_26_book_oracle(a, b, winner, rule):
    res = stronger_rasi(a, b, dict(_CHART12_D10))
    assert res.winner == winner, (
        f"{a} vs {b}: expected {winner}, got {res.winner} "
        f"(rule {res.deciding_rule}, {res.diagnostics})"
    )
    assert res.deciding_rule == rule, (
        f"{a} vs {b}: expected deciding {rule}, got {res.deciding_rule} "
        f"({res.diagnostics})"
    )


# ── result shape ─────────────────────────────────────────────────────────────

def test_result_is_frozen_and_hashable():
    placements = {
        "Mars": "Scorpio", "Jupiter": "Scorpio", "Venus": "Taurus",
        "Sun": "Aries", "Moon": "Gemini", "Mercury": "Cancer",
        "Saturn": "Leo", "Rahu": "Virgo", "Ketu": "Pisces",
    }
    res = stronger_rasi("Scorpio", "Taurus", _chart(placements))
    assert isinstance(res, StrongerRasiResult)
    hash(res)  # must not raise
    with pytest.raises(Exception):
        res.winner = "Taurus"  # frozen
