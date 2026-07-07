"""Oracle tests for agent/calculations/jaimini/rasi_aspects.py -- P6
Jaimini rasi drishti (sign aspect) primitive.

Do not modify rasi_aspects.py to make these tests pass -- any
disagreement between the module's computed table and a transcribed PVR
oracle row is a genuine falsification of the module, not a test bug.

ORACLE PROVENANCE: all expected values below are transcribed verbatim
from rasi_aspects.py's own CITATION block (PVR Narasimha Rao, "Vedic
Astrology: An Integrated Approach", Ch.10 Section 10.3 worked examples
+ Exercise 15 answer key, printed pp.102/110, PDF pp.113/121) -- not
recomputed from the movable/fixed/dual rule inside this file.

Layer 1: 3 worked-row oracle tests (Section 10.3, hardcoded sets).
Layer 2: 9-row Exercise 15 oracle, parametrized (including Ketu --
         ordinary zodiacal counting; the anti-zodiacal rule is
         argala/virodhargala-scoped only, per CITATION).
Layer 3: exhaustive 144-pair symmetry sweep.
Layer 4: structural locks -- 3-member sets, class-pairing, no
         adjacent-sign aspect, no self-aspect.
Layer 5: return-type lock (frozenset).
Layer 6: error-path + case-sensitivity contract tests.
Layer 7: cross-system guard against accidental unification with graha
         drishti (aspects.py).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))  # project root

import pytest

from agent.calculations.core.aspects import signs_aspected_by
from agent.calculations.jaimini.rasi_aspects import (
    rasi_aspects_between,
    signs_rasi_aspected_by,
)

_SIGNS = (
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
)

_MOVABLE_SIGNS = frozenset({"Aries", "Cancer", "Libra", "Capricorn"})
_FIXED_SIGNS = frozenset({"Taurus", "Leo", "Scorpio", "Aquarius"})
_DUAL_SIGNS = frozenset({"Gemini", "Virgo", "Sagittarius", "Pisces"})


def _adjacent_signs(sign: str) -> frozenset[str]:
    index = _SIGNS.index(sign)
    return frozenset({_SIGNS[(index - 1) % 12], _SIGNS[(index + 1) % 12]})


# ── 1. Section 10.3 worked-row oracle tests ──────────────────────────────────
# Hardcoded from the CITATION block verbatim -- NOT recomputed from the
# movable/fixed/dual rule here, so a drift in the module's derivation
# gets caught rather than mirrored.

def test_aries_worked_row_pvr_section_10_3():
    assert signs_rasi_aspected_by("Aries") == frozenset(
        {"Leo", "Scorpio", "Aquarius"}
    )


def test_taurus_worked_row_pvr_section_10_3():
    assert signs_rasi_aspected_by("Taurus") == frozenset(
        {"Cancer", "Libra", "Capricorn"}
    )


def test_gemini_worked_row_pvr_section_10_3():
    assert signs_rasi_aspected_by("Gemini") == frozenset(
        {"Virgo", "Sagittarius", "Pisces"}
    )


# ── 2. Exercise 15 answer key oracle (9 rows, printed p.110 / PDF p.121) ────
# Each row's "occupied sign" is not given directly by PVR (only the
# aspected-rasis triplet is) -- it is uniquely determined because exactly
# one of the 12 signs produces that aspect set. Occupied signs below were
# derived by that reverse lookup, then the forward assertion (occupied ->
# expected aspected set) is what each parametrized case actually checks.

_EXERCISE_15_ROWS = [
    pytest.param("Taurus", frozenset({"Cancer", "Libra", "Capricorn"}), id="Sun_in_Taurus"),
    pytest.param("Aries", frozenset({"Leo", "Scorpio", "Aquarius"}), id="Moon_in_Aries"),
    pytest.param("Scorpio", frozenset({"Capricorn", "Aries", "Cancer"}), id="Mars_in_Scorpio"),
    pytest.param("Sagittarius", frozenset({"Pisces", "Gemini", "Virgo"}), id="Mercury_in_Sagittarius"),
    pytest.param("Virgo", frozenset({"Sagittarius", "Pisces", "Gemini"}), id="Jupiter_in_Virgo"),
    pytest.param("Capricorn", frozenset({"Taurus", "Leo", "Scorpio"}), id="Venus_in_Capricorn"),
    pytest.param("Scorpio", frozenset({"Capricorn", "Aries", "Cancer"}), id="Saturn_in_Scorpio"),
    pytest.param("Leo", frozenset({"Libra", "Capricorn", "Aries"}), id="Rahu_in_Leo"),
    # Ketu row: PVR's Exercise 15 answer key gives Ar/Cn/Li for Ketu,
    # occupying Aquarius (fixed). This is ORDINARY zodiacal movable/
    # fixed/dual counting -- PVR's anti-zodiacal note (Section 10.6) is
    # explicitly scoped to argala/virodhargala only, never to rasi
    # drishti; this row is the module CITATION's own proof of that scope.
    pytest.param("Aquarius", frozenset({"Aries", "Cancer", "Libra"}), id="Ketu_in_Aquarius"),
]


@pytest.mark.parametrize("occupied_sign, expected_aspected", _EXERCISE_15_ROWS)
def test_exercise_15_answer_key_row(occupied_sign, expected_aspected):
    assert signs_rasi_aspected_by(occupied_sign) == expected_aspected


# ── 3. Exhaustive symmetry sweep (144 ordered pairs) ─────────────────────────

def test_rasi_aspects_between_is_symmetric_for_all_144_ordered_pairs():
    # PVR states symmetry explicitly (Section 10.3): "sign Y will aspect
    # sign X if sign X aspects sign Y." Checked here over every ordered
    # pair, not just the 3 worked examples.
    for sign_a in _SIGNS:
        for sign_b in _SIGNS:
            assert rasi_aspects_between(sign_a, sign_b) == rasi_aspects_between(
                sign_b, sign_a
            ), f"symmetry broken for pair ({sign_a}, {sign_b})"


# ── 4. Structural locks, full 12-sign sweeps ─────────────────────────────────

@pytest.mark.parametrize("sign", _SIGNS)
def test_every_aspect_set_has_exactly_three_members(sign):
    assert len(signs_rasi_aspected_by(sign)) == 3


@pytest.mark.parametrize("sign", sorted(_MOVABLE_SIGNS))
def test_movable_signs_aspect_only_fixed_signs(sign):
    assert signs_rasi_aspected_by(sign) <= _FIXED_SIGNS


@pytest.mark.parametrize("sign", sorted(_FIXED_SIGNS))
def test_fixed_signs_aspect_only_movable_signs(sign):
    assert signs_rasi_aspected_by(sign) <= _MOVABLE_SIGNS


@pytest.mark.parametrize("sign", sorted(_DUAL_SIGNS))
def test_dual_signs_aspect_exactly_the_other_three_duals(sign):
    assert signs_rasi_aspected_by(sign) == _DUAL_SIGNS - {sign}


@pytest.mark.parametrize("sign", _SIGNS)
def test_no_sign_aspects_an_adjacent_sign(sign):
    assert signs_rasi_aspected_by(sign).isdisjoint(_adjacent_signs(sign)), (
        f"{sign} must never rasi-aspect either of its zodiacal neighbors "
        f"{sorted(_adjacent_signs(sign))}"
    )


@pytest.mark.parametrize("sign", _SIGNS)
def test_no_sign_aspects_itself(sign):
    # Contract lock: rasi_aspects_between(x, x) is False for all 12 signs
    # -- a sign never rasi-aspects itself under the movable/fixed/dual rule.
    assert rasi_aspects_between(sign, sign) is False


# ── 5. Return-type lock ──────────────────────────────────────────────────────

@pytest.mark.parametrize("sign", _SIGNS)
def test_signs_rasi_aspected_by_returns_frozenset(sign):
    assert isinstance(signs_rasi_aspected_by(sign), frozenset)


# ── 6. Error-path coverage ────────────────────────────────────────────────────

def test_signs_rasi_aspected_by_rejects_unrecognized_sign():
    with pytest.raises(ValueError, match="Atlantis"):
        signs_rasi_aspected_by("Atlantis")


def test_rasi_aspects_between_rejects_unrecognized_sign_a():
    with pytest.raises(ValueError, match="Atlantis"):
        rasi_aspects_between("Atlantis", "Aries")


def test_rasi_aspects_between_rejects_unrecognized_sign_b():
    with pytest.raises(ValueError, match="Atlantis"):
        rasi_aspects_between("Aries", "Atlantis")


def test_signs_rasi_aspected_by_is_case_sensitive_rejects_uppercase():
    # Consistent with aspects.py's existing contract: no case
    # normalization, "ARIES" is rejected the same as any other
    # unrecognized sign name.
    with pytest.raises(ValueError, match="ARIES"):
        signs_rasi_aspected_by("ARIES")


# ── 7. Cross-system guard against rasi/graha drishti unification ────────────

def test_rasi_drishti_and_graha_drishti_are_disjoint_for_sun_in_aries():
    # Tripwire: rasi drishti (this module) and graha drishti
    # (agent/calculations/core/aspects.py) are different classical
    # mechanisms and must never be accidentally unified. Sun in Aries
    # aspects only its 7th, Libra, under graha drishti -- disjoint from
    # Aries's rasi-drishti set {Leo, Scorpio, Aquarius}.
    graha_result = set(signs_aspected_by("Sun", "Aries"))
    rasi_result = signs_rasi_aspected_by("Aries")

    assert graha_result == {"Libra"}
    assert graha_result.isdisjoint(rasi_result), (
        f"graha drishti {graha_result} and rasi drishti {rasi_result} "
        f"for Aries must be disjoint -- if this fails, the two systems "
        f"have been accidentally unified somewhere"
    )
