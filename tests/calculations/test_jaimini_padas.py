"""Tests for agent/calculations/jaimini/padas.py -- P6 Jaimini bhava
padas orchestration kernel (PVR Ch.9 Section 9.2).

FIXTURE PROVENANCE:
  Layer A: PVR Ch.9 Example 29 (printed p.87 / PDF p.99), Chart 1 --
    same CHART1 fixture as test_jaimini_arudha.py, copied verbatim (see
    that file's own FIXTURE PROVENANCE for the pymupdf reconstruction
    detail, transcribed Session 57). lagna_sign="Virgo" (Asc: 10Vi58).
    Only label + arudha_sign are book-printed per house -- house_sign/
    lord/count/etc. are NOT asserted here (already covered by
    test_jaimini_arudha.py's own Layer A).
  Layer B: synthetic regression fixture isolating strength.py's D2
    fail-closed (both co-lords resident), propagated through the FULL
    12-house loop -- test_jaimini_arudha.py's own C3 only exercised
    compute_arudha_pada() directly, never compute_bhava_padas()'s own
    loop; this layer closes that gap.
  Layer C: input-contract error paths, confirming the validation split
    documented in padas.py's own docstring (lagna_sign checked before
    the loop; planet_longitudes delegated to compute_arudha_pada()).
  Layer D: result-shape locks (frozen, hashable) + label scheme.
"""

import sys
from dataclasses import FrozenInstanceError
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))  # project root

import pytest

from agent.calculations.jaimini.padas import BhavaPada, BhavaPadaSet, compute_bhava_padas

_SIGN_BASES = {
    "Ar": 0, "Ta": 30, "Ge": 60, "Cn": 90, "Le": 120, "Vi": 150,
    "Li": 180, "Sc": 210, "Sg": 240, "Cp": 270, "Aq": 300, "Pi": 330,
}


def _dms_to_abs(sign: str, d: float, m: float = 0, s: float = 0) -> float:
    return _SIGN_BASES[sign] + d + m / 60 + s / 3600


# ── Layer A fixture (PVR Example 29, Chart 1 -- copied verbatim from
# test_jaimini_arudha.py, see that file's own FIXTURE PROVENANCE) ──────────

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

# PVR's own book-printed (label, arudha_sign) per house, Example 29,
# items (1)-(12), printed p.87-88 / PDF p.99-100. Keyed by house_num.
_EXAMPLE_29_LABELED_PADAS = {
    1: ("AL", "Gemini"), 2: ("A2", "Leo"), 3: ("A3", "Virgo"),
    4: ("A4", "Leo"), 5: ("A5", "Aries"), 6: ("A6", "Gemini"),
    7: ("A7", "Taurus"), 8: ("A8", "Capricorn"), 9: ("A9", "Capricorn"),
    10: ("A10", "Virgo"), 11: ("A11", "Taurus"), 12: ("UL", "Libra"),
}


class TestExample29BookOracle:
    # Only label + arudha_sign are book-printed per house -- everything
    # else on BhavaPada.result (house_sign/lord/count/etc.) is already
    # covered by test_jaimini_arudha.py's own Layer A and not
    # re-asserted here.
    def test_all_12_houses_match_book(self):
        bps = compute_bhava_padas("Virgo", CHART1)
        assert len(bps.padas) == 12
        assert tuple(p.house_num for p in bps.padas) == tuple(range(1, 13))
        for pada in bps.padas:
            expected_label, expected_arudha = _EXAMPLE_29_LABELED_PADAS[pada.house_num]
            assert pada.label == expected_label
            assert pada.result.arudha_sign == expected_arudha


# ── Layer B: fail-closed D2 propagation through the full loop ──────────────

# Both Mars AND Ketu resident in Scorpio simultaneously -- isolates
# strength.py's design lock D2 (Basic Rule both-resident gap), fail
# closed. lagna_sign="Scorpio" makes house 1 itself Scorpio, so the
# very first loop iteration hits the failure -- this is the whole-loop
# propagation path test_jaimini_arudha.py's own C3 never exercised
# (that test called compute_arudha_pada() directly, not
# compute_bhava_padas()'s loop). Remaining 7 planets filled in-range,
# distinct, irrelevant.
D2_BOTH_RESIDENT_SCORPIO = {
    "Sun": 12.0, "Moon": 42.0, "Mercury": 102.0, "Jupiter": 132.0,
    "Venus": 162.0, "Saturn": 192.0,
    "Mars": 210.0, "Ketu": 220.0, "Rahu": 40.0,
}


class TestFailClosedPropagation:
    def test_d2_both_resident_propagates_through_loop(self):
        with pytest.raises(ValueError, match="D2|both"):
            compute_bhava_padas("Scorpio", D2_BOTH_RESIDENT_SCORPIO)


# ── Layer C: input contract ──────────────────────────────────────────────

class TestInputContract:
    def test_unrecognized_lagna_sign_raises_before_loop(self):
        with pytest.raises(ValueError, match="Xyz"):
            compute_bhava_padas("Xyz", CHART1)

    def test_missing_key_raises_delegated_to_arudha(self):
        # Confirms the validation split: padas.py checks lagna_sign
        # itself but delegates planet_longitudes' key-set/range
        # validation entirely to compute_arudha_pada() -- not
        # duplicated here.
        bad = dict(CHART1)
        del bad["Ketu"]
        with pytest.raises(ValueError, match="Ketu"):
            compute_bhava_padas("Virgo", bad)


# ── Layer D: result-shape locks ─────────────────────────────────────────

class TestResultShape:
    def test_bhava_pada_set_is_frozen(self):
        bps = compute_bhava_padas("Virgo", CHART1)
        with pytest.raises(FrozenInstanceError):
            bps.lagna_sign = "Aries"

    def test_bhava_pada_set_is_hashable(self):
        bps = compute_bhava_padas("Virgo", CHART1)
        hash(bps)  # must not raise

    def test_bhava_pada_is_frozen(self):
        bps = compute_bhava_padas("Virgo", CHART1)
        with pytest.raises(FrozenInstanceError):
            bps.padas[0].label = "Xyz"

    def test_result_types(self):
        bps = compute_bhava_padas("Virgo", CHART1)
        assert isinstance(bps, BhavaPadaSet)
        assert all(isinstance(p, BhavaPada) for p in bps.padas)

    def test_labels_scheme(self):
        bps = compute_bhava_padas("Virgo", CHART1)
        by_house = {p.house_num: p.label for p in bps.padas}
        assert by_house[1] == "AL"
        assert by_house[12] == "UL"
        for house_num in range(2, 12):
            assert by_house[house_num] == f"A{house_num}"
