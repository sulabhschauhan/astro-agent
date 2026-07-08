"""Tests for agent/calculations/jaimini/arudha.py -- P6 Jaimini bhava
arudha kernel (PVR Ch.9 Section 9.2).

FIXTURE PROVENANCE:
  Layer A: PVR Ch.9 Example 29 (printed p.87 / PDF p.99), Chart 1 --
    "Rasi Arudha example", April 9, 2000, 5:55pm (4:00 West), 71W12
    42N30. All 9 planet longitudes plus Asc are printed verbatim under
    the chart diagram (Asc: 10Vi58, Sun: 26Pi29, Merc: 1Pi36,
    Jup: 17Ar21, Moon: 4Ge45, Ven: 10Pi01, Mars: 19Ar09, Sat: 22Ar41,
    Rahu: 5Cn55, Ketu: 5Cp55 -- Ketu = Rahu+180 confirmed exactly).
    Reconstructed via pymupdf render of PDF page 99 (0-idx 98), read
    directly off the printed table, transcribed Session 57. All 12
    houses' book-narrated intermediate counts ((1) count=7 ... (12)
    count=8) were cross-checked against compute_arudha_pada()'s own
    count field before this file was written, confirming the
    reconstruction is faithful -- only arudha_sign is asserted here
    per this task's scope (see Layer A class docstring).
  Layer B: synthetic step-5-exception fixtures, expected values derived
    in design chat (Session 57) and independently re-derived by hand
    against arudha.py's own COUNTING FORMULA docstring before this file
    was written. B3 doubles as PVR's own inline worked example (Ch.9
    Section 9.2 step (3)/(4): "if the house we are interested in is in
    Gemini and its lord Mercury is in Aquarius... 9... Libra").
  Layer C: co-lord dependency + propagation. C1/C2 reuse the SHERIDAN/
    SULABH JHora v8 fixtures verbatim from test_jaimini_strength.py
    (same provenance: Lahiri ayanamsa, Mean Node, transcribed Session
    57) as routing checks only -- arudha_sign is NOT asserted as oracle
    for these two (self-derived, no book/JHora arudha parity source).
    C3 is a synthetic regression fixture isolating strength.py's D2
    fail-closed propagation.
  Layer D: input-contract error paths (house_sign, key set, range),
    mirroring test_jaimini_strength.py's Layer D discipline.
  Layer E: result-shape locks (frozen, hashable).
"""

import math
import sys
from dataclasses import FrozenInstanceError
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))  # project root

import pytest

from agent.calculations.jaimini.arudha import ArudhaPadaResult, compute_arudha_pada

_SIGN_BASES = {
    "Ar": 0, "Ta": 30, "Ge": 60, "Cn": 90, "Le": 120, "Vi": 150,
    "Li": 180, "Sc": 210, "Sg": 240, "Cp": 270, "Aq": 300, "Pi": 330,
}


def _dms_to_abs(sign: str, d: float, m: float = 0, s: float = 0) -> float:
    return _SIGN_BASES[sign] + d + m / 60 + s / 3600


# ── Layer A fixture (PVR Example 29, Chart 1 -- see FIXTURE PROVENANCE) ─────

CHART1 = {
    "Sun": _dms_to_abs("Pi", 26, 29),
    "Moon": _dms_to_abs("Ge", 4, 45),
    "Mars": _dms_to_abs("Ar", 19, 9),
    "Mercury": _dms_to_abs("Pi", 1, 36),
    "Jupiter": _dms_to_abs("Ar", 17, 21),
    "Venus": _dms_to_abs("Pi", 10, 1),
    "Saturn": _dms_to_abs("Ar", 22, 41),
    "Rahu": _dms_to_abs("Cn", 5, 55),
    "Ketu": _dms_to_abs("Cp", 5, 55),  # Rahu + 180 (5Cn55 + 180 = 5Cp55, verbatim)
}

# PVR's own book-printed arudha_sign per house (Example 29, items (1)-(12),
# printed p.87-88 / PDF p.99-100).
_EXAMPLE_29_ARUDHA_SIGNS = {
    "Virgo": "Gemini", "Libra": "Leo", "Scorpio": "Virgo", "Sagittarius": "Leo",
    "Capricorn": "Aries", "Aquarius": "Gemini", "Pisces": "Taurus",
    "Aries": "Capricorn", "Taurus": "Capricorn", "Gemini": "Virgo",
    "Cancer": "Taurus", "Leo": "Libra",
}


class TestExample29BookOracle:
    # Inputs (CHART1) are RECONSTRUCTED from the printed longitude table,
    # not book-narrated arithmetic themselves -- only the final
    # arudha_sign is book-printed per house. count/raw_ending_sign/
    # co_lord_deciding_step are NOT asserted in this layer.
    @pytest.mark.parametrize("house_sign,expected_arudha", sorted(_EXAMPLE_29_ARUDHA_SIGNS.items()))
    def test_book_arudha_sign(self, house_sign, expected_arudha):
        result = compute_arudha_pada(house_sign, CHART1)
        assert result.arudha_sign == expected_arudha


# ── Layer B: step-5 exception (synthetic) ───────────────────────────────────

# Fillers for the 8 planet keys not under test in each Layer B case --
# in-range, distinct, and irrelevant since these house_signs are not
# co-lorded (only the named planet's longitude is ever consulted).
_B_FILLERS = {
    "Sun": 12.0, "Moon": 42.0, "Mars": 72.0, "Mercury": 102.0, "Jupiter": 132.0,
    "Venus": 162.0, "Saturn": 192.0, "Rahu": 232.0, "Ketu": 232.0 + 180 - 360,
}


def _b_chart(**overrides):
    chart = dict(_B_FILLERS)
    chart.update(overrides)
    return chart


class TestStep5Exception:
    def test_b1_first_house_trigger(self):
        # 1st-house trigger, distance 0: Mars at 10.0deg (Aries), house
        # sign itself Aries.
        result = compute_arudha_pada("Aries", _b_chart(Mars=10.0))
        assert result.count == 1
        assert result.raw_ending_sign == "Aries"
        assert result.exception_applied is True
        assert result.arudha_sign == "Capricorn"
        assert result.lord == "Mars"

    def test_b2_seventh_house_trigger(self):
        # 7th-house trigger, distance 6: Mercury at 165.0deg (Virgo),
        # house sign Gemini.
        result = compute_arudha_pada("Gemini", _b_chart(Mercury=165.0))
        assert result.count == 4
        assert result.raw_ending_sign == "Sagittarius"
        assert result.exception_applied is True
        assert result.arudha_sign == "Virgo"
        assert result.lord == "Mercury"

    def test_b3_no_exception_pvr_inline_example(self):
        # PVR's own inline worked example (Ch.9 Section 9.2, steps
        # (3)-(4)): Gemini's lord Mercury in Aquarius -> count 9 ->
        # Libra. No 1st/7th trigger.
        result = compute_arudha_pada("Gemini", _b_chart(Mercury=315.0))
        assert result.count == 9
        assert result.raw_ending_sign == "Libra"
        assert result.exception_applied is False
        assert result.arudha_sign == "Libra"


# ── Layer C: co-lord dependency + propagation ───────────────────────────────

# SHERIDAN/SULABH -- JHora v8 verbatim, copied from test_jaimini_strength.py
# (same provenance; see that file's own FIXTURE PROVENANCE header).
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

SULABH = {
    "Sun": _dms_to_abs("Pi", 22, 31, 52.53),
    "Moon": _dms_to_abs("Sc", 2, 14, 52.28),
    "Mars": _dms_to_abs("Cp", 5, 34, 38.75),
    "Mercury": _dms_to_abs("Pi", 7, 53, 19.62),
    "Jupiter": _dms_to_abs("Ar", 12, 34, 25.28),
    "Venus": _dms_to_abs("Ta", 8, 20, 35.31),
    "Saturn": _dms_to_abs("Sg", 8, 51, 10.60),
    "Rahu": _dms_to_abs("Aq", 28, 25, 2.40),
    "Ketu": _dms_to_abs("Le", 28, 25, 2.40),  # Rahu + 180
}

# C3: both Mars AND Ketu resident in Scorpio simultaneously -- isolates
# strength.py's design lock D2 (Basic Rule both-resident gap), fail
# closed. Remaining 7 planets filled in-range, distinct, irrelevant.
D2_BOTH_RESIDENT_SCORPIO = {
    "Sun": 12.0, "Moon": 42.0, "Mercury": 102.0, "Jupiter": 132.0,
    "Venus": 162.0, "Saturn": 192.0,
    "Mars": 210.0, "Ketu": 220.0, "Rahu": 40.0,
}


class TestCoLordDependency:
    def test_c1_sheridan_scorpio_basic_rule_mars(self):
        # Ketu (13 Sc 6') is resident in Scorpio -> basic rule picks
        # Mars. Routing check only -- arudha_sign is self-derived, not
        # asserted as oracle here.
        result = compute_arudha_pada("Scorpio", SHERIDAN)
        assert result.lord == "Mars"
        assert result.co_lord_deciding_step == "basic_rule"

    def test_c2_sulabh_aquarius_basic_rule_saturn(self):
        # Rahu (28 Aq 25') is resident in Aquarius -> basic rule picks
        # Saturn. Routing check only.
        result = compute_arudha_pada("Aquarius", SULABH)
        assert result.lord == "Saturn"
        assert result.co_lord_deciding_step == "basic_rule"

    def test_c3_d2_both_resident_propagates_unmodified(self):
        # strength.py's D2 fail-closed (both co-lords resident in the
        # contested sign) must propagate out of arudha.py unmodified --
        # this module does not catch or reinterpret it.
        with pytest.raises(ValueError, match="D2|both"):
            compute_arudha_pada("Scorpio", D2_BOTH_RESIDENT_SCORPIO)


# ── Layer D: input contract ──────────────────────────────────────────────

class TestInputContract:
    def test_unrecognized_house_sign_raises(self):
        with pytest.raises(ValueError, match="Xyz"):
            compute_arudha_pada("Xyz", CHART1)

    def test_missing_key_raises(self):
        bad = dict(CHART1)
        del bad["Ketu"]
        with pytest.raises(ValueError, match="Ketu"):
            compute_arudha_pada("Virgo", bad)

    def test_extra_key_raises(self):
        bad = dict(CHART1)
        bad["Pluto"] = 15.0
        with pytest.raises(ValueError, match="Pluto"):
            compute_arudha_pada("Virgo", bad)

    def test_out_of_range_high_longitude_raises(self):
        bad = dict(CHART1)
        bad["Mars"] = 360.0
        with pytest.raises(ValueError, match="Mars"):
            compute_arudha_pada("Virgo", bad)

    def test_negative_longitude_raises(self):
        bad = dict(CHART1)
        bad["Rahu"] = -1.0
        with pytest.raises(ValueError, match="Rahu"):
            compute_arudha_pada("Virgo", bad)

    def test_nan_longitude_fails_closed(self):
        bad = dict(CHART1)
        bad["Saturn"] = math.nan
        with pytest.raises(ValueError, match="Saturn"):
            compute_arudha_pada("Virgo", bad)


# ── Layer E: result-shape locks ─────────────────────────────────────────

class TestResultShape:
    def test_result_is_frozen(self):
        result = compute_arudha_pada("Virgo", CHART1)
        with pytest.raises(FrozenInstanceError):
            result.arudha_sign = "Aries"

    def test_result_is_hashable(self):
        result = compute_arudha_pada("Virgo", CHART1)
        hash(result)  # must not raise

    def test_result_type(self):
        result = compute_arudha_pada("Virgo", CHART1)
        assert isinstance(result, ArudhaPadaResult)
