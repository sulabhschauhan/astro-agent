"""Tests for agent/calculations/jaimini/strength.py -- P6 Jaimini
stronger co-lord cascade (PVR Ch.15 Section 15.5.1).

FIXTURE PROVENANCE:
  Layer A: JHora v8, Lahiri ayanamsa, Mean Node, real-chart longitudes
    for Sulabh and Sheridan -- same source table as
    tests/calculations/test_jaimini_karakas.py's DAVID/SULABH/SHERIDAN
    fixtures (verbatim, transcribed Session 57). Ketu = Rahu + 180 deg,
    confirmed against tests/fixtures/jhora_sulabh.md's own raw Ketu row
    (28 Le 25' 02.40" = 28 Aq 25' 02.40" + 180 deg exactly).
  Layer B: PVR Ch.15 Section 15.5.1 worked examples and Exercise 25,
    verbatim per strength.py's own CITATION block. Exercise 25 and the
    Step-2 Saturn-count=2 example give only PARTIAL chart data in the
    book (a few planets' signs, not a full 9-planet longitude set) --
    this module's docstring CITATION carries the verbatim text; the
    fixtures below are hand-constructed full charts engineered to
    reproduce PVR's stated intermediate counts and final winner
    exactly (every intermediate value below was cross-checked against
    the book's own narrated arithmetic before being locked in). The
    5(b) fixture uses PVR's own two longitudes verbatim (Mars 23Li17,
    Ketu 5Cn54) with the remaining 7 planets placed to guarantee steps
    (1)-(4) tie exactly as the book's "suppose we have a tie" framing
    requires -- do NOT recompute or "correct" the placements without
    re-verifying steps (1)-(4) still tie.
  Layer C: synthetic regression fixtures for design locks D2/D3/D4/D6,
    each hand-constructed to isolate exactly the mechanism under test.
  Layer D: input-contract error paths (sign, purpose, key set, range).
  Layer E: result-shape locks (hashability, diagnostics tuple shape).
"""

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))  # project root

import pytest

from agent.calculations.jaimini.strength import (
    StrongerCoLordResult,
    stronger_co_lord,
)

_SIGN_BASES = {
    "Ar": 0, "Ta": 30, "Ge": 60, "Cn": 90, "Le": 120, "Vi": 150,
    "Li": 180, "Sc": 210, "Sg": 240, "Cp": 270, "Aq": 300, "Pi": 330,
}


def _dms_to_abs(sign: str, d: float, m: float = 0, s: float = 0) -> float:
    return _SIGN_BASES[sign] + d + m / 60 + s / 3600


# ── Layer A fixtures (JHora v8 verbatim -- see FIXTURE PROVENANCE) ─────────

SULABH = {
    "Sun": _dms_to_abs("Pi", 22, 31, 52.53),
    "Moon": _dms_to_abs("Sc", 2, 14, 52.28),
    "Mars": _dms_to_abs("Cp", 5, 34, 38.75),
    "Mercury": _dms_to_abs("Pi", 7, 53, 19.62),
    "Jupiter": _dms_to_abs("Ar", 12, 34, 25.28),
    "Venus": _dms_to_abs("Ta", 8, 20, 35.31),
    "Saturn": _dms_to_abs("Sg", 8, 51, 10.60),
    "Rahu": _dms_to_abs("Aq", 28, 25, 2.40),
    "Ketu": _dms_to_abs("Le", 28, 25, 2.40),  # Rahu + 180 (jhora_sulabh.md verbatim)
}

SHERIDAN = {
    "Sun": _dms_to_abs("Ta", 12, 30, 48.88),
    "Moon": _dms_to_abs("Ar", 2, 10, 33.00),
    "Mars": _dms_to_abs("Li", 21, 46, 6.71),
    "Mercury": _dms_to_abs("Ar", 18, 30, 40.55),
    "Jupiter": _dms_to_abs("Sg", 18, 11, 23.34),
    "Venus": _dms_to_abs("Ta", 7, 10, 42.19),
    "Saturn": _dms_to_abs("Li", 17, 44, 27.51),
    "Rahu": _dms_to_abs("Ta", 13, 6, 42.33),
    "Ketu": _dms_to_abs("Sc", 13, 6, 42.33),  # Rahu + 180
}


class TestRealChartOracle:
    def test_sulabh_aquarius_basic_rule_saturn(self):
        # Rahu (28 Aq 25') is resident in Aquarius -> basic rule gives
        # the OTHER co-lord, Saturn.
        result = stronger_co_lord("Aquarius", SULABH)
        assert result.winner == "Saturn"
        assert result.loser == "Rahu"
        assert result.deciding_step == "basic_rule"

    def test_sheridan_scorpio_basic_rule_mars(self):
        # Ketu (13 Sc 6') is resident in Scorpio -> basic rule gives
        # the OTHER co-lord, Mars.
        result = stronger_co_lord("Scorpio", SHERIDAN)
        assert result.winner == "Mars"
        assert result.loser == "Ketu"
        assert result.deciding_step == "basic_rule"

    def test_sulabh_scorpio_cascade_ketu_at_step_2(self):
        # Neither Mars (Cp) nor Ketu (Le) resides in Scorpio -> full
        # cascade. Step 1 ties 0-0 (both alone). Step 2: Ketu's sign
        # (Leo) is rasi-aspected by Jupiter's sign (Aries, a movable
        # rasi aspecting the non-adjacent fixed rasi Leo) -> Ketu
        # count 1, Mars count 0.
        result = stronger_co_lord("Scorpio", SULABH)
        assert result.winner == "Ketu"
        assert result.loser == "Mars"
        assert result.deciding_step == "step_2"
        diag = dict(result.diagnostics)
        assert diag["step_1_joiners"] == (0, 0)
        assert diag["step_2_counts"] == (0, 1)

    def test_sheridan_aquarius_cascade_rahu_at_step_1(self):
        # Neither Saturn (Li) nor Rahu (Ta) resides in Aquarius ->
        # cascade. Step 1: Mars joins Saturn in Libra (1 joiner);
        # Sun and Venus join Rahu in Taurus (2 joiners) -> Rahu wins.
        result = stronger_co_lord("Aquarius", SHERIDAN)
        assert result.winner == "Rahu"
        assert result.loser == "Saturn"
        assert result.deciding_step == "step_1"
        assert dict(result.diagnostics)["step_1_joiners"] == (1, 2)


# ── Layer B: PVR book-verbatim worked examples ──────────────────────────────

# Step-2 example (printed p.202 / PDF p.213): "Saturn is in Ge with
# Mercury, Rahu is in Ar, Mars is in Le, Jupiter is in Ta." An extra
# joiner (Venus) is added alongside Rahu in Aries so Step 1 ties 0
# joiners flat -> 1-1 (PVR's own text implies "we have a tie after
# rule (1)" is the precondition for reaching this step in isolation;
# the book's illustration is self-contained per-step, not one
# continuous chart flowing through every step). This does not alter
# PVR's own Step-2 count claim: Saturn is conjoined by Mercury AND by
# his own dispositor (Mercury again, Gemini's classical lord) for a
# count of 2; Rahu is conjoined/aspected only by his dispositor (Mars
# in Leo aspecting Aries) for a count of 1.
STEP_2_WORKED_EXAMPLE = {
    "Saturn": _dms_to_abs("Ge", 15),
    "Mercury": _dms_to_abs("Ge", 20),
    "Rahu": _dms_to_abs("Ar", 10),
    "Venus": _dms_to_abs("Ar", 20),
    "Mars": _dms_to_abs("Le", 10),
    "Jupiter": _dms_to_abs("Ta", 10),
    "Ketu": _dms_to_abs("Li", 10),
    "Sun": _dms_to_abs("Cp", 10),
    "Moon": _dms_to_abs("Vi", 10),
}

# Exercise 25 (printed p.203, answer key pp.205-206 / PDF p.214,
# 216-217): PVR states Saturn/Rahu signs only implicitly, via the
# narrated counts ("Saturn is aspected by Mercury and not
# aspected/conjoined by Jupiter and his dispositor (Jupiter again)"
# -> Saturn occupies a Jupiter-ruled dual rasi, Sagittarius; "Rahu is
# aspected by Venus (his dispositor)" -> Rahu occupies a Venus-ruled
# rasi, and Step 4 states it is movable -> Libra) and the Step-4
# verdict ("Saturn is in a dual rasi and Rahu is in a movable rasi").
# Mercury is placed in Virgo (aspects dual Sagittarius, not movable
# Libra) and Venus in Taurus (aspects movable Libra, not dual
# Sagittarius) to reproduce exactly the book's per-role True/False
# pattern. Scorpio half per the book verbatim: "Mars is in Sc and
# Ketu is elsewhere (in Ar)."
EXERCISE_25 = {
    "Sun": _dms_to_abs("Cn", 15),
    "Moon": _dms_to_abs("Aq", 15),
    "Mars": _dms_to_abs("Sc", 10),
    "Mercury": _dms_to_abs("Vi", 10),
    "Jupiter": _dms_to_abs("Cp", 10),
    "Venus": _dms_to_abs("Ta", 10),
    "Saturn": _dms_to_abs("Sg", 10),
    "Rahu": _dms_to_abs("Li", 10),
    "Ketu": _dms_to_abs("Ar", 10),
}

# Step 5(b) example (printed p.203 / PDF p.214), PVR's own longitudes
# verbatim: "Mars is at 23Li17 and Ketu is at 5Cn54." The other 7
# planets are placed to guarantee steps (1)-(4) tie (0 joiners each,
# 0 role-hits each, neither exalted, both movable rasis) so the
# function actually reaches Step 5(b) on these exact two longitudes,
# reproducing PVR's own advancement arithmetic (23deg17' vs
# 30deg-5deg54'=24deg6').
STEP_5B_WORKED_EXAMPLE = {
    "Sun": _dms_to_abs("Ta", 10),
    "Moon": _dms_to_abs("Sg", 10),
    "Mars": _dms_to_abs("Li", 23, 17),
    "Mercury": _dms_to_abs("Ge", 10),
    "Jupiter": _dms_to_abs("Ar", 10),
    "Venus": _dms_to_abs("Vi", 10),
    "Saturn": _dms_to_abs("Cp", 10),
    "Rahu": _dms_to_abs("Pi", 10),
    "Ketu": _dms_to_abs("Cn", 5, 54),
}


class TestPvrWorkedExamples:
    def test_step_2_saturn_count_of_2(self):
        result = stronger_co_lord("Aquarius", STEP_2_WORKED_EXAMPLE)
        assert result.winner == "Saturn"
        assert result.loser == "Rahu"
        assert result.deciding_step == "step_2"
        diag = dict(result.diagnostics)
        assert diag["step_1_joiners"] == (1, 1)
        assert diag["step_2_counts"] == (2, 1)

    def test_exercise_25_aquarius_saturn_via_step_4(self):
        result = stronger_co_lord("Aquarius", EXERCISE_25)
        assert result.winner == "Saturn"
        assert result.loser == "Rahu"
        assert result.deciding_step == "step_4"
        diag = dict(result.diagnostics)
        assert diag["step_1_joiners"] == (0, 0)
        assert diag["step_2_counts"] == (1, 1)
        assert diag["step_3_exalted"] == (False, False)
        assert diag["step_4_modality_rank"] == (3, 1)  # Saturn dual, Rahu movable

    def test_exercise_25_scorpio_ketu_via_basic_rule(self):
        result = stronger_co_lord("Scorpio", EXERCISE_25)
        assert result.winner == "Ketu"
        assert result.loser == "Mars"
        assert result.deciding_step == "basic_rule"

    def test_step_5b_ketu_more_advanced_than_mars(self):
        # PVR's own numbers: Mars advancement 23deg17', Ketu
        # advancement 30deg-5deg54'=24deg6' -> Ketu wins.
        result = stronger_co_lord("Scorpio", STEP_5B_WORKED_EXAMPLE)
        assert result.winner == "Ketu"
        assert result.loser == "Mars"
        assert result.deciding_step == "step_5b"
        diag = dict(result.diagnostics)
        assert diag["step_1_joiners"] == (0, 0)
        assert diag["step_2_counts"] == (0, 0)
        assert diag["step_3_exalted"] == (False, False)
        assert diag["step_4_modality_rank"] == (1, 1)
        mars_adv, ketu_adv = diag["step_5b_advancement"]
        assert mars_adv == pytest.approx(23 + 17 / 60)
        assert ketu_adv == pytest.approx(30 - (5 + 54 / 60))


# ── Layer C: design-lock regression fixtures ────────────────────────────────

# D2: both co-lords resident in the contested sign simultaneously
# (the 2022-23 Saturn+Rahu-in-Aquarius trigger named in the module's
# own D2 writeup) -> fail closed.
D2_BOTH_RESIDENT = {
    "Sun": _dms_to_abs("Ar", 10), "Moon": _dms_to_abs("Ta", 10),
    "Mars": _dms_to_abs("Ge", 10), "Mercury": _dms_to_abs("Cn", 10),
    "Jupiter": _dms_to_abs("Le", 10), "Venus": _dms_to_abs("Vi", 10),
    "Saturn": _dms_to_abs("Aq", 10), "Rahu": _dms_to_abs("Aq", 20),
    "Ketu": _dms_to_abs("Le", 20),
}

# D3: Mars in Aries contesting Scorpio -- Aries' classical lord is
# Mars himself, so the Step-2 dispositor role is self-referential and
# conjoins trivially (+1, mechanical no-exclusion reading). Ketu (in
# Cancer) is placed with 0 role-hits so the self-dispositor point is
# the sole, isolable source of Mars's win.
D3_SELF_DISPOSITOR = {
    "Sun": _dms_to_abs("Cp", 10), "Moon": _dms_to_abs("Pi", 10),
    "Mars": _dms_to_abs("Ar", 10), "Mercury": _dms_to_abs("Vi", 10),
    "Jupiter": _dms_to_abs("Ge", 10), "Venus": _dms_to_abs("Le", 10),
    "Saturn": _dms_to_abs("Li", 10), "Rahu": _dms_to_abs("Sg", 10),
    "Ketu": _dms_to_abs("Cn", 10),
}

# D4: Ketu occupies Capricorn -- Mars's own classical exaltation sign
# -- to prove a node sitting in ANOTHER planet's exaltation sign gains
# nothing at Step 3 (Rahu/Ketu are never in _EXALTATION_SIGN). Mars
# (in Gemini, a dual rasi) then wins at Step 4 on modality alone,
# confirming Step 3 was a genuine no-op rather than a lucky bypass.
D4_NODE_IN_ANOTHER_PLANETS_EXALTATION_SIGN = {
    "Sun": _dms_to_abs("Aq", 10), "Moon": _dms_to_abs("Li", 10),
    "Mars": _dms_to_abs("Ge", 10), "Mercury": _dms_to_abs("Ar", 10),
    "Jupiter": _dms_to_abs("Cn", 10), "Venus": _dms_to_abs("Cn", 10),
    "Saturn": _dms_to_abs("Li", 10), "Rahu": _dms_to_abs("Ar", 10),
    "Ketu": _dms_to_abs("Cp", 10),
}

# D6: Saturn (Ge 15, advancement 15.0) and Rahu (Vi 15, advancement
# 30-15=15.0) tie exactly at Step 5(b) after steps (1)-(4) also tie
# (both dual rasis, both dispositor-of-sign = Mercury, 0 role-hits
# each) -> fail closed.
D6_EXACT_TIE = {
    "Sun": _dms_to_abs("Cp", 10), "Moon": _dms_to_abs("Cn", 10),
    "Mars": _dms_to_abs("Le", 10), "Mercury": _dms_to_abs("Ar", 10),
    "Jupiter": _dms_to_abs("Ta", 10), "Venus": _dms_to_abs("Li", 10),
    "Saturn": _dms_to_abs("Ge", 15), "Rahu": _dms_to_abs("Vi", 15),
    "Ketu": _dms_to_abs("Sg", 10),
}


class TestDesignLockRegressions:
    def test_d2_both_resident_fails_closed(self):
        with pytest.raises(ValueError, match="BOTH in Aquarius"):
            stronger_co_lord("Aquarius", D2_BOTH_RESIDENT)

    def test_d3_self_dispositor_conjoins_trivially(self):
        result = stronger_co_lord("Scorpio", D3_SELF_DISPOSITOR)
        assert result.winner == "Mars"
        assert result.deciding_step == "step_2"
        assert dict(result.diagnostics)["step_2_counts"] == (1, 0)

    def test_d4_node_never_exalted_even_in_another_planets_sign(self):
        result = stronger_co_lord(
            "Scorpio", D4_NODE_IN_ANOTHER_PLANETS_EXALTATION_SIGN
        )
        diag = dict(result.diagnostics)
        assert diag["step_3_exalted"] == (False, False)
        assert result.deciding_step == "step_4"
        assert result.winner == "Mars"

    def test_d6_exact_advancement_tie_fails_closed(self):
        with pytest.raises(ValueError, match="exact advancement tie"):
            stronger_co_lord("Aquarius", D6_EXACT_TIE)


# ── Layer D: input contract ──────────────────────────────────────────────

class TestInputContract:
    def test_unrecognized_sign_raises(self):
        with pytest.raises(ValueError, match="Scorpio.*Aquarius"):
            stronger_co_lord("Leo", {})

    def test_purpose_dasa_duration_cites_footnote_53(self):
        with pytest.raises(ValueError, match="footnote 53"):
            stronger_co_lord("Aquarius", {}, purpose="dasa_duration")

    def test_purpose_unrecognized_lists_two_literals(self):
        with pytest.raises(ValueError, match="'arudha'.*'dasa_duration'"):
            stronger_co_lord("Aquarius", {}, purpose="natal_strength")

    def test_missing_key_named(self):
        bad = dict(SULABH)
        del bad["Ketu"]
        with pytest.raises(ValueError, match="Ketu"):
            stronger_co_lord("Scorpio", bad)

    def test_extra_key_named(self):
        bad = dict(SULABH)
        bad["Pluto"] = 15.0
        with pytest.raises(ValueError, match="Pluto"):
            stronger_co_lord("Scorpio", bad)

    def test_out_of_range_longitude_named(self):
        bad = dict(SULABH)
        bad["Mars"] = 360.0
        with pytest.raises(ValueError, match="Mars"):
            stronger_co_lord("Scorpio", bad)

    def test_negative_longitude_named(self):
        bad = dict(SULABH)
        bad["Rahu"] = -1.0
        with pytest.raises(ValueError, match="Rahu"):
            stronger_co_lord("Aquarius", bad)

    def test_nan_longitude_fails_closed(self):
        # `not (0 <= lon < 360)`: NaN compares False against every
        # relation, so this form catches it without a separate
        # isnan() check (see strength.py's own comment at the guard).
        bad = dict(SULABH)
        bad["Saturn"] = math.nan
        with pytest.raises(ValueError, match="Saturn"):
            stronger_co_lord("Aquarius", bad)


# ── Layer E: result-shape locks ─────────────────────────────────────────

class TestResultShape:
    def test_result_is_hashable(self):
        result = stronger_co_lord("Aquarius", SULABH)
        hash(result)  # must not raise

    def test_diagnostics_is_tuple_of_pairs(self):
        result = stronger_co_lord("Aquarius", SHERIDAN)
        assert isinstance(result.diagnostics, tuple)
        for entry in result.diagnostics:
            assert isinstance(entry, tuple)
            assert len(entry) == 2

    def test_basic_rule_short_circuit_has_no_diagnostics(self):
        result = stronger_co_lord("Aquarius", SULABH)
        assert result.deciding_step == "basic_rule"
        assert result.diagnostics == ()

    def test_result_type(self):
        result = stronger_co_lord("Aquarius", SULABH)
        assert isinstance(result, StrongerCoLordResult)
