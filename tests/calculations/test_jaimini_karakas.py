"""Tests for agent/calculations/jaimini/karakas.py -- P6 Jaimini chara
karakas kernel.

FIXTURE PROVENANCE: JHora v8, Lahiri ayanamsa, Whole Sign, Mean Node,
karaka-scheme preference = 8. Captured Session 57 from JHora Body tables,
transcribed and ratified in design chat. Fixture values below are
verbatim JHora output -- do NOT recompute or "correct" them.

Layer A: four-chart full-tuple oracle asserts (JHora), hardest case
         (David -- 3 planets within 48 arcmin of each other) first.
Layer B: PVR Ch.8 p.81 Table 14 (Example 28) numeric oracle -- karaka
         assignment AND advancement values, arc-minute tolerance.
Layer C: Rahu-reversal structural/convention-lock test (regression guard
         against a sign flip in the Rahu branch, not an oracle claim).
Layer D: error-path contract tests (Ketu, missing/extra key, exact tie,
         Rahu-involved tie, range guard).
Layer E: result-shape locks (hashability, tuple length/order,
         permutation-of-inputs).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))  # project root

import pytest

from agent.calculations.jaimini.karakas import (
    CharaKarakasResult,
    compute_chara_karakas,
)

_SIGN_BASES = {
    "Ar": 0, "Ta": 30, "Ge": 60, "Cn": 90, "Le": 120, "Vi": 150,
    "Li": 180, "Sc": 210, "Sg": 240, "Cp": 270, "Aq": 300, "Pi": 330,
}


def _dms_to_abs(sign: str, d: float, m: float, s: float) -> float:
    return _SIGN_BASES[sign] + d + m / 60 + s / 3600


# ── Fixtures (JHora v8 verbatim -- see FIXTURE PROVENANCE above) ────────────

DAVID = {
    "Sun": _dms_to_abs("Cp", 5, 27, 33.96),
    "Moon": _dms_to_abs("Le", 11, 40, 24.23),
    "Mars": _dms_to_abs("Ta", 21, 13, 33.95),
    "Mercury": _dms_to_abs("Cp", 12, 45, 29.37),
    "Jupiter": _dms_to_abs("Pi", 23, 55, 32.12),
    "Venus": _dms_to_abs("Sc", 28, 45, 43.93),
    "Saturn": _dms_to_abs("Cn", 6, 2, 42.90),
    "Rahu": _dms_to_abs("Li", 24, 45, 18.05),
}
DAVID_EXPECTED = (
    ("AK", "Venus"), ("AmK", "Jupiter"), ("BK", "Mars"), ("MK", "Mercury"),
    ("PiK", "Moon"), ("PK", "Saturn"), ("GK", "Sun"), ("DK", "Rahu"),
)

SURBHI = {
    "Sun": _dms_to_abs("Le", 24, 58, 21.89),
    "Moon": _dms_to_abs("Aq", 15, 13, 3.07),
    "Mars": _dms_to_abs("Ge", 5, 39, 41.10),
    "Mercury": _dms_to_abs("Le", 21, 22, 48.83),
    "Jupiter": _dms_to_abs("Le", 29, 56, 56.35),
    "Venus": _dms_to_abs("Vi", 19, 11, 44.29),
    "Saturn": _dms_to_abs("Cp", 19, 2, 43.46),
    "Rahu": _dms_to_abs("Sg", 2, 36, 4.41),
}
SURBHI_EXPECTED = (
    ("AK", "Jupiter"), ("AmK", "Rahu"), ("BK", "Sun"), ("MK", "Mercury"),
    ("PiK", "Venus"), ("PK", "Saturn"), ("GK", "Moon"), ("DK", "Mars"),
)

SHERIDAN = {
    "Sun": _dms_to_abs("Ta", 12, 30, 48.88),
    "Moon": _dms_to_abs("Ar", 2, 10, 33.00),
    "Mars": _dms_to_abs("Li", 21, 46, 6.71),
    "Mercury": _dms_to_abs("Ar", 18, 30, 40.55),
    "Jupiter": _dms_to_abs("Sg", 18, 11, 23.34),
    "Venus": _dms_to_abs("Ta", 7, 10, 42.19),
    "Saturn": _dms_to_abs("Li", 17, 44, 27.51),
    "Rahu": _dms_to_abs("Ta", 13, 6, 42.33),
}
SHERIDAN_EXPECTED = (
    ("AK", "Mars"), ("AmK", "Mercury"), ("BK", "Jupiter"), ("MK", "Saturn"),
    ("PiK", "Rahu"), ("PK", "Sun"), ("GK", "Venus"), ("DK", "Moon"),
)

SULABH = {
    "Sun": _dms_to_abs("Pi", 22, 31, 52.53),
    "Moon": _dms_to_abs("Sc", 2, 14, 52.28),
    "Mars": _dms_to_abs("Cp", 5, 34, 38.75),
    "Mercury": _dms_to_abs("Pi", 7, 53, 19.62),
    "Jupiter": _dms_to_abs("Ar", 12, 34, 25.28),
    "Venus": _dms_to_abs("Ta", 8, 20, 35.31),
    "Saturn": _dms_to_abs("Sg", 8, 51, 10.60),
    "Rahu": _dms_to_abs("Aq", 28, 25, 2.40),
}
SULABH_EXPECTED = (
    ("AK", "Sun"), ("AmK", "Jupiter"), ("BK", "Saturn"), ("MK", "Venus"),
    ("PiK", "Mercury"), ("PK", "Mars"), ("GK", "Moon"), ("DK", "Rahu"),
)


# ── Layer A: four-chart full-tuple oracle (JHora v8) ─────────────────────────
# Hardest case first: David's Saturn/Sun/Rahu cluster spans only 48 arcmin
# of advancement (Rahu 5.245 deg .. Saturn 6.0452 deg, PK/GK/DK ranks) --
# the tightest margin of the 4 charts, so a ranking-comparison bug is most
# likely to surface here.

class TestFourChartOracle:
    def test_david_hardest_case(self):
        result = compute_chara_karakas(DAVID)
        assert result.karakas == DAVID_EXPECTED

    def test_surbhi_minute_level_tie_proximity(self):
        result = compute_chara_karakas(SURBHI)
        assert result.karakas == SURBHI_EXPECTED

    def test_sheridan_rahu_mid_rank(self):
        result = compute_chara_karakas(SHERIDAN)
        assert result.karakas == SHERIDAN_EXPECTED

    def test_sulabh_canonical(self):
        result = compute_chara_karakas(SULABH)
        assert result.karakas == SULABH_EXPECTED


# ── Layer B: PVR Ch.8 p.81 Table 14 (Example 28) numeric oracle ─────────────

PVR_EXAMPLE_28 = {
    "Sun": _dms_to_abs("Ge", 12, 47, 0),
    "Moon": _dms_to_abs("Ar", 20, 28, 0),
    "Mars": _dms_to_abs("Ge", 13, 51, 0),
    "Mercury": _dms_to_abs("Ge", 25, 18, 0),
    "Jupiter": _dms_to_abs("Ta", 5, 40, 0),
    "Venus": _dms_to_abs("Ge", 17, 21, 0),
    "Saturn": _dms_to_abs("Ta", 2, 28, 0),
    "Rahu": _dms_to_abs("Cn", 1, 43, 0),
}
PVR_EXAMPLE_28_EXPECTED = (
    ("AK", "Rahu"), ("AmK", "Mercury"), ("BK", "Moon"), ("MK", "Venus"),
    ("PiK", "Mars"), ("PK", "Sun"), ("GK", "Jupiter"), ("DK", "Saturn"),
)
PVR_EXAMPLE_28_ADVANCEMENT = {
    "Rahu": 28 + 17 / 60,
    "Mercury": 25 + 18 / 60,
    "Moon": 20 + 28 / 60,
    "Venus": 17 + 21 / 60,
    "Mars": 13 + 51 / 60,
    "Sun": 12 + 47 / 60,
    "Jupiter": 5 + 40 / 60,
    "Saturn": 2 + 28 / 60,
}


class TestPvrExample28:
    def test_karaka_assignment(self):
        result = compute_chara_karakas(PVR_EXAMPLE_28)
        assert result.karakas == PVR_EXAMPLE_28_EXPECTED

    def test_advancement_values(self):
        # Tolerance justification: PVR prints Table 14 at arc-minute
        # precision (e.g. "28°17'"), so 1 arc-minute (1/60 deg) is the
        # SOURCE's own resolution floor -- asserting tighter would claim
        # precision the printed example does not carry.
        # Scope guard: this tolerance applies ONLY to this Example 28
        # numeric check, never to the Layer A four-chart fixture asserts
        # (those are JHora-sourced to full arcsecond precision and are
        # asserted via exact tuple equality on karaka ASSIGNMENT, not on
        # advancement value, so no tolerance is smuggled into them).
        # Tuning note: tighten only if a higher-precision printing of
        # Example 28 (e.g. a seconds-level edition) is sourced.
        result = compute_chara_karakas(PVR_EXAMPLE_28)
        actual = dict(result.advancement)
        for planet, expected in PVR_EXAMPLE_28_ADVANCEMENT.items():
            assert actual[planet] == pytest.approx(expected, abs=1 / 60), planet


# ── Layer C: Rahu-reversal convention lock ───────────────────────────────────

class TestRahuReversalConventionLock:
    @pytest.mark.parametrize(
        "name,fixture",
        [
            ("david", DAVID),
            ("surbhi", SURBHI),
            ("sheridan", SHERIDAN),
            ("sulabh", SULABH),
        ],
    )
    def test_rahu_advancement_matches_own_formula(self, name, fixture):
        # This is a regression guard on the module's OWN Rahu formula
        # (30 - longitude % 30) reproducing itself on real fixture
        # longitudes -- a convention lock against an accidental sign
        # flip or off-by-one in the Rahu branch, NOT an external-oracle
        # claim. The actual oracle checks are Layer A's full-tuple
        # karaka-assignment asserts above.
        result = compute_chara_karakas(fixture)
        actual = dict(result.advancement)
        expected = 30.0 - (fixture["Rahu"] % 30.0)
        assert actual["Rahu"] == pytest.approx(expected)


# ── Layer D: error-path contract ─────────────────────────────────────────────

# Base longitudes with no accidental advancement collisions (verified: 5.0,
# 17.0, 23.0, 18.5, 22.0, 25.5, 28.0, 20.0 -- all distinct), used as a clean
# slate for the tie-error tests below so only the deliberately-overridden
# planets collide.
_NO_TIE_BASE = {
    "Sun": 5.0,       # Ar 5, advancement 5.0
    "Moon": 47.0,     # Ta 17, advancement 17.0
    "Mars": 83.0,     # Ge 23, advancement 23.0
    "Mercury": 138.5, # Le 18.5, advancement 18.5
    "Jupiter": 172.0, # Vi 22, advancement 22.0
    "Venus": 205.5,   # Li 25.5, advancement 25.5
    "Saturn": 268.0,  # Sg 28, advancement 28.0
    "Rahu": 100.0,    # Cn 10, advancement 30-10=20.0
}


class TestErrorPaths:
    def test_ketu_present_gives_design_reason_not_generic_message(self):
        bad = dict(SULABH)
        bad["Ketu"] = 15.0
        with pytest.raises(ValueError, match="moksha"):
            compute_chara_karakas(bad)

    def test_missing_key_names_saturn(self):
        bad = dict(SULABH)
        del bad["Saturn"]
        with pytest.raises(ValueError, match="Saturn"):
            compute_chara_karakas(bad)

    def test_extra_key_names_pluto(self):
        bad = dict(SULABH)
        bad["Pluto"] = 15.0
        with pytest.raises(ValueError, match="Pluto"):
            compute_chara_karakas(bad)

    def test_exact_tie_names_both_planets_and_mentions_sthira(self):
        longs = dict(_NO_TIE_BASE)
        longs["Sun"] = 10.0   # Ar 10, advancement 10.0
        longs["Moon"] = 40.0  # Ta 10, advancement 10.0 -- ties with Sun
        with pytest.raises(ValueError, match="sthira") as exc_info:
            compute_chara_karakas(longs)
        message = str(exc_info.value)
        assert "Sun" in message
        assert "Moon" in message

    def test_rahu_involved_tie(self):
        longs = dict(_NO_TIE_BASE)
        longs["Sun"] = 10.0    # Ar 10, advancement 10.0
        longs["Rahu"] = 320.0  # Aq 20, advancement 30-20=10.0 -- ties with Sun
        with pytest.raises(ValueError, match="sthira") as exc_info:
            compute_chara_karakas(longs)
        message = str(exc_info.value)
        assert "Sun" in message
        assert "Rahu" in message

    def test_range_guard_negative_names_sun(self):
        bad = dict(SULABH)
        bad["Sun"] = -0.1
        with pytest.raises(ValueError, match="Sun"):
            compute_chara_karakas(bad)

    def test_range_guard_upper_boundary_names_sun(self):
        bad = dict(SULABH)
        bad["Sun"] = 360.0
        with pytest.raises(ValueError, match="Sun"):
            compute_chara_karakas(bad)

    def test_range_guard_nan_names_sun(self):
        bad = dict(SULABH)
        bad["Sun"] = float("nan")
        with pytest.raises(ValueError, match="Sun"):
            compute_chara_karakas(bad)

    def test_range_guard_two_planets_both_named(self):
        bad = dict(SULABH)
        bad["Sun"] = -1.0
        bad["Moon"] = 400.0
        with pytest.raises(ValueError) as exc_info:
            compute_chara_karakas(bad)
        message = str(exc_info.value)
        assert "Sun" in message
        assert "Moon" in message


# ── Layer E: result-shape locks ──────────────────────────────────────────────

class TestResultShape:
    def test_returns_chara_karakas_result(self):
        result = compute_chara_karakas(SULABH)
        assert isinstance(result, CharaKarakasResult)

    def test_hashable(self):
        result = compute_chara_karakas(SULABH)
        assert isinstance(hash(result), int)

    def test_karakas_tuple_length_eight(self):
        result = compute_chara_karakas(SULABH)
        assert len(result.karakas) == 8

    def test_karaka_labels_in_table_13_order(self):
        result = compute_chara_karakas(SULABH)
        labels = tuple(label for label, _ in result.karakas)
        assert labels == ("AK", "AmK", "BK", "MK", "PiK", "PK", "GK", "DK")

    def test_assigned_planets_are_permutation_of_inputs(self):
        result = compute_chara_karakas(SULABH)
        assigned = sorted(planet for _, planet in result.karakas)
        assert assigned == sorted(SULABH.keys())
