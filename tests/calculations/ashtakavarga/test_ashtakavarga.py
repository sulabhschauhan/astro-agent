"""Tests for agent/calculations/ashtakavarga/ashtakavarga.py.

Oracle: tests/fixtures/jhora_david_ashtakavarga.md (JHora v8, David,
reference sign = natal lagna Virgo — the fixture's own CRITICAL
provenance note documents why the reference sign must equal the natal
lagna for these numbers to be reproducible).

Layer A: full-grid parity — all 96 cells (8 owners x 12 signs) against the
         fixture's BAV table, exactly (no tolerance band; this is a pure
         deterministic computation, not an ephemeris-derived Virupa). This
         is the first cell-by-cell parity run against this fixture — the
         module's own CITATION block (c) and the fixture's own D-1
         positions note both flagged this as "not yet performed" as of
         Session 54; this test closes that gap.

Layer B: SAV parity — all 12 signs against the fixture's SAV row, exact
         grand total 337, plus an explicit hand-summed-from-BAV check
         proving Lagna's BAV is excluded from the aggregate (compute_sav's
         own docstring: SAV would total 386, not 337, if Lagna were
         included).

Layer C: canonical row totals — each owner's BAV sums to its fixed,
         position-invariant total (these are the same totals compute_bav
         itself asserts internally; this layer re-derives them from the
         public return value rather than trusting the module's own
         internal assert).

Layer D: error paths — ValueError on missing contributor, unknown
         contributor key, and unknown sign name.

Layer E: convention sentinels — the 3 documented Parasara/Varahamihira
         conflict cells (module CITATION block (b)) land, for David's
         placements, on Moon's Aries cell and Venus's Leo cell. A mismatch
         here means the codebase has drifted to the Varahamihira variant,
         NOT that the implementation is broken — see the module's own
         CITATION block before "fixing" either number.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))  # project root

import pytest

from agent.calculations.ashtakavarga.ashtakavarga import compute_bav, compute_sav
from agent.chart_calculator import SIGNS

# David's D-1 sign placements — tests/fixtures/jhora_david_ashtakavarga.md's
# "D-1 positions" table (JHora v8 Basics tab, captured 2026-07-06, Session 54;
# Mercury independently confirmed there against a design-chat back-solve).
# Retrograde status is irrelevant to BAV (sign placement only).
_DAVID_PLACEMENTS: dict[str, str] = {
    "Sun": "Capricorn",
    "Moon": "Leo",
    "Mars": "Taurus",
    "Mercury": "Capricorn",
    "Jupiter": "Pisces",
    "Venus": "Scorpio",
    "Saturn": "Cancer",
    "Lagna": "Virgo",
}

# Fixture's BAV table, Aries..Pisces column order (tests/fixtures/
# jhora_david_ashtakavarga.md "BAV table"). Transcription checksum-verified
# there (21 checksums: 8 row totals + 12 column sums + grand total 337).
_FIXTURE_BAV: dict[str, list[int]] = {
    "Sun":     [3, 5, 4, 4, 5, 2, 5, 5, 3, 5, 4, 3],
    "Moon":    [3, 4, 5, 5, 4, 4, 5, 4, 2, 4, 4, 5],
    "Mars":    [2, 4, 6, 2, 2, 2, 4, 4, 2, 3, 4, 4],
    "Mercury": [2, 5, 6, 3, 3, 5, 4, 5, 5, 6, 5, 5],
    "Jupiter": [5, 4, 6, 3, 3, 7, 4, 4, 6, 4, 5, 5],
    "Venus":   [4, 3, 3, 5, 4, 5, 5, 7, 5, 4, 2, 5],
    "Saturn":  [3, 1, 3, 4, 3, 5, 5, 4, 3, 3, 4, 1],
    "Lagna":   [4, 3, 6, 6, 2, 2, 5, 5, 4, 4, 4, 4],
}

# Fixture's SAV row, Aries..Pisces order (7 planets only, Lagna excluded).
_FIXTURE_SAV: list[int] = [22, 26, 33, 26, 24, 30, 32, 33, 26, 29, 28, 28]
_FIXTURE_SAV_TOTAL = 337

_CANONICAL_ROW_TOTALS: dict[str, int] = {
    "Sun": 48, "Moon": 49, "Mars": 39, "Mercury": 54,
    "Jupiter": 56, "Venus": 52, "Saturn": 39, "Lagna": 49,
}


@pytest.fixture(scope="module")
def david_bav() -> dict[str, dict[str, int]]:
    return compute_bav(_DAVID_PLACEMENTS)


@pytest.fixture(scope="module")
def david_sav(david_bav: dict[str, dict[str, int]]) -> dict[str, int]:
    return compute_sav(david_bav)


# ── Layer A: full-grid parity (96 cells) ────────────────────────────────────

_ALL_CELLS = [
    (owner, sign) for owner in _FIXTURE_BAV for sign in SIGNS
]


@pytest.mark.parametrize("owner,sign", _ALL_CELLS, ids=[f"{o}-{s}" for o, s in _ALL_CELLS])
def test_full_grid_parity_against_jhora_fixture(david_bav, owner, sign):
    expected = _FIXTURE_BAV[owner][SIGNS.index(sign)]
    got = david_bav[owner][sign]
    assert got == expected, (
        f"BAV mismatch for owner={owner!r} sign={sign!r}: "
        f"got {got}, expected {expected} (tests/fixtures/jhora_david_ashtakavarga.md)"
    )


# ── Layer B: SAV parity + Lagna-exclusion proof ─────────────────────────────

@pytest.mark.parametrize("sign_index", range(12), ids=SIGNS)
def test_sav_parity_against_jhora_fixture(david_sav, sign_index):
    sign = SIGNS[sign_index]
    expected = _FIXTURE_SAV[sign_index]
    got = david_sav[sign]
    assert got == expected, (
        f"SAV mismatch for sign={sign!r}: got {got}, expected {expected} "
        f"(tests/fixtures/jhora_david_ashtakavarga.md)"
    )


def test_sav_grand_total_is_337(david_sav):
    assert sum(david_sav.values()) == _FIXTURE_SAV_TOTAL


def test_sav_excludes_lagna_bav(david_bav, david_sav):
    """Hand-sum the 7 planet BAVs for one sign column and confirm it equals
    SAV exactly -- proving compute_sav sums only the 7 planets, not all 8
    contributors. If Lagna's BAV were folded in, this hand sum would fall
    short of matching david_sav (Lagna contributes a nonzero bindu to every
    sign, so the two could never coincidentally agree on all 12 signs).
    """
    planets = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn")
    for sign in SIGNS:
        hand_summed = sum(david_bav[planet][sign] for planet in planets)
        assert hand_summed == david_sav[sign], (
            f"hand-summed 7-planet BAV for {sign!r} ({hand_summed}) != "
            f"compute_sav's value ({david_sav[sign]})"
        )
        with_lagna = hand_summed + david_bav["Lagna"][sign]
        assert with_lagna != david_sav[sign], (
            f"SAV for {sign!r} equals the 7-planet sum plus Lagna's BAV "
            f"({david_bav['Lagna'][sign]}) -- Lagna does not look excluded"
        )


# ── Layer C: canonical row totals ───────────────────────────────────────────

@pytest.mark.parametrize("owner,expected_total", sorted(_CANONICAL_ROW_TOTALS.items()))
def test_canonical_row_total(david_bav, owner, expected_total):
    assert sum(david_bav[owner].values()) == expected_total


# ── Layer D: error paths ─────────────────────────────────────────────────────

def test_compute_bav_missing_contributor_raises_value_error():
    incomplete = dict(_DAVID_PLACEMENTS)
    del incomplete["Saturn"]
    with pytest.raises(ValueError, match="missing required contributor"):
        compute_bav(incomplete)


def test_compute_bav_unknown_contributor_raises_value_error():
    bad = dict(_DAVID_PLACEMENTS)
    bad["Rahu"] = "Aries"
    with pytest.raises(ValueError, match="unknown contributor"):
        compute_bav(bad)


def test_compute_bav_unknown_sign_raises_value_error():
    bad = dict(_DAVID_PLACEMENTS)
    bad["Sun"] = "Ophiuchus"
    with pytest.raises(ValueError, match="unrecognized sign"):
        compute_bav(bad)


# ── Layer E: Parasara/Varahamihira convention sentinels ─────────────────────

def test_sentinel_moon_aries_parasara_convention(david_bav):
    """Moon's Aries cell receives BOTH documented Parasara-only conflict
    contributions for David's placements: 9th-from-Moon (Moon in Leo -> 9th
    is Aries) and 2nd-from-Jupiter (Jupiter in Pisces -> 2nd is Aries). A
    mismatch here most likely means AV_TABLES has been changed to the
    Varahamihira variant (which excludes one or both of these houses as
    benefic) -- see ashtakavarga.py's module CITATION block (b) before
    treating this as an implementation bug.
    """
    assert david_bav["Moon"]["Aries"] == 3


def test_sentinel_venus_leo_parasara_convention(david_bav):
    """Venus's Leo cell receives the documented Parasara-only 4th-from-Mars
    conflict contribution for David's placements (Mars in Taurus -> 4th is
    Leo). A mismatch here most likely means AV_TABLES has been changed to
    the Varahamihira variant (which excludes this house as benefic) -- see
    ashtakavarga.py's module CITATION block (b) before treating this as an
    implementation bug.
    """
    assert david_bav["Venus"]["Leo"] == 4
