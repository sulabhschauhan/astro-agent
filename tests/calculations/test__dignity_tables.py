"""Structural invariant tests for agent/calculations/core/_dignity_tables.py.

Locked convention: every MT / Own / Exalt-range / Debil-range interval is
half-open [start, end) — 0.0 is inclusive at the lower bound, 30.0 is never
reached (the sign itself is [0, 30)). 20.0deg Virgo is Mercury Own, not MT.

Independent of chart_calculator.py and any other production module by
design — reaches into _dignity_tables only, plus stdlib + pytest.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))  # project root

import pytest

from agent.calculations.core._dignity_tables import (
    EXALTATION,
    DEBILITATION,
    MOOLATRIKONA,
    OWN_SIGNS,
)

CANONICAL_SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]
CANONICAL_PLANETS = [
    "Sun", "Moon", "Mars", "Mercury", "Jupiter",
    "Venus", "Saturn", "Rahu", "Ketu",
]
NODES = {"Rahu", "Ketu"}
NON_NODAL_PLANETS = [p for p in CANONICAL_PLANETS if p not in NODES]


def _all_signs(table) -> list[str]:
    signs = []
    for value in table.values():
        entries = value if isinstance(value, list) else [value]
        for entry in entries:
            signs.append(entry[0])
    return signs


def _all_ranges(table) -> list[tuple[str, str, float, float]]:
    ranges = []
    for planet, value in table.items():
        entries = value if isinstance(value, list) else [value]
        for sign, start, end in entries:
            ranges.append((planet, sign, start, end))
    return ranges


# ── 1. Completeness ───────────────────────────────────────────────────────

@pytest.mark.parametrize(
    "table,name",
    [
        (EXALTATION, "EXALTATION"),
        (DEBILITATION, "DEBILITATION"),
        (MOOLATRIKONA, "MOOLATRIKONA"),
        (OWN_SIGNS, "OWN_SIGNS"),
    ],
)
def test_table_has_exactly_nine_canonical_planets(table, name):
    assert set(table.keys()) == set(CANONICAL_PLANETS), (
        f"{name}: keys {sorted(table.keys())} != canonical planet set"
    )
    assert len(table) == 9, f"{name}: expected 9 entries, got {len(table)}"


# ── 2. Sign-name validity (typo guard) ──────────────────────────────────────

@pytest.mark.parametrize(
    "table,name",
    [
        (EXALTATION, "EXALTATION"),
        (DEBILITATION, "DEBILITATION"),
        (MOOLATRIKONA, "MOOLATRIKONA"),
        (OWN_SIGNS, "OWN_SIGNS"),
    ],
)
def test_all_sign_names_are_canonical(table, name):
    for sign in _all_signs(table):
        assert sign in CANONICAL_SIGNS, f"{name}: unrecognized sign name {sign!r}"


# ── 3. Deep-degree validity ─────────────────────────────────────────────────

@pytest.mark.parametrize(
    "table,name", [(EXALTATION, "EXALTATION"), (DEBILITATION, "DEBILITATION")]
)
@pytest.mark.parametrize("planet", CANONICAL_PLANETS)
def test_deep_degree_validity(table, name, planet):
    _, deep_degree = table[planet]
    if planet in NODES:
        assert deep_degree is None, (
            f"{name}[{planet}]: expected None deep degree for node, got {deep_degree}"
        )
    else:
        assert deep_degree is not None, (
            f"{name}[{planet}]: expected numeric deep degree, got None"
        )
        assert 0.0 <= deep_degree < 30.0, (
            f"{name}[{planet}]: deep degree {deep_degree} outside [0.0, 30.0)"
        )


# ── 4. Range validity ────────────────────────────────────────────────────────

@pytest.mark.parametrize(
    "table,name", [(MOOLATRIKONA, "MOOLATRIKONA"), (OWN_SIGNS, "OWN_SIGNS")]
)
def test_range_validity(table, name):
    for planet, sign, start, end in _all_ranges(table):
        assert 0.0 <= start < end <= 30.0, (
            f"{name}[{planet}] ({sign}): range [{start}, {end}) "
            f"violates 0.0 <= start < end <= 30.0"
        )


# ── 5. Exalt-Debil 180deg invariant ────────────────────────────────────────────

@pytest.mark.parametrize("planet", CANONICAL_PLANETS)
def test_exalt_debil_are_opposite_signs(planet):
    exalt_sign = EXALTATION[planet][0]
    debil_sign = DEBILITATION[planet][0]
    exalt_idx = CANONICAL_SIGNS.index(exalt_sign)
    debil_idx = CANONICAL_SIGNS.index(debil_sign)
    assert (debil_idx - exalt_idx) % 12 == 6, (
        f"{planet}: exalt={exalt_sign} (idx {exalt_idx}), "
        f"debil={debil_sign} (idx {debil_idx}) — not exactly 6 signs apart"
    )


# ── 6. Half-open disjointness within a shared sign ──────────────────────────

@pytest.mark.parametrize("planet", CANONICAL_PLANETS)
def test_mt_and_own_do_not_overlap_within_shared_sign(planet):
    mt_sign, mt_start, mt_end = MOOLATRIKONA[planet]
    for own_sign, own_start, own_end in OWN_SIGNS[planet]:
        if own_sign != mt_sign:
            continue
        overlaps = mt_start < own_end and own_start < mt_end
        assert not overlaps, (
            f"{planet} ({mt_sign}): MT [{mt_start}, {mt_end}) overlaps "
            f"Own [{own_start}, {own_end}) under half-open semantics"
        )


# ── 7. Half-open partition in the MT-shared sign ─────────────────────────────

@pytest.mark.parametrize("planet", NON_NODAL_PLANETS)
def test_half_open_partition_in_mt_shared_sign(planet):
    mt_sign, mt_start, mt_end = MOOLATRIKONA[planet]
    intervals = [(mt_start, mt_end)]

    exalt_sign, exalt_deep = EXALTATION[planet]
    if exalt_sign == mt_sign:
        intervals.append((0.0, exalt_deep))

    for own_sign, own_start, own_end in OWN_SIGNS[planet]:
        if own_sign == mt_sign:
            intervals.append((own_start, own_end))

    intervals.sort()

    assert intervals[0][0] == 0.0, (
        f"{planet} ({mt_sign}): partition does not start at 0.0 — {intervals}"
    )
    assert intervals[-1][1] == 30.0, (
        f"{planet} ({mt_sign}): partition does not end at 30.0 — {intervals}"
    )
    for (s1, e1), (s2, e2) in zip(intervals, intervals[1:]):
        assert e1 == s2, (
            f"{planet} ({mt_sign}): gap or overlap between {(s1, e1)} and "
            f"{(s2, e2)} — full partition {intervals}"
        )
