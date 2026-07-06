"""Bhinna Ashtakavarga (BAV) and Sarvashtakavarga (SAV) — Session 54.

Deterministic bindu-scoring from D-1 sign placements only: no ephemeris
calls, no house/cusp input, pure functions of {contributor: sign}.

CITATION:
  (a) Benefic-house tables: PVR Narasimha Rao, "Vedic Astrology: An
      Integrated Approach", Tables 19-26, Parasara convention. Verified
      against canonical position-invariant totals (see _CANONICAL_BAV_TOTAL)
      and against the JHora v8 David fixture by hand in design review,
      2026-07-06.
  (b) Known Parasara/Varahamihira conflict cells, kept as Parasara per (a)
      — do NOT silently "fix" these against a Varahamihira-convention
      source without a tiebreaker review (see CLAUDE.md Locked Decisions,
      tiebreaker principle):
        - Moon's AV: 9th-from-Moon is benefic (Parasara); some
          Varahamihira-lineage tables exclude it.
        - Moon's AV: 2nd-from-Jupiter is benefic (Parasara); ditto.
        - Venus's AV: 4th-from-Mars is benefic (Parasara); ditto.
  (c) Validation oracle: JHora v8, reference sign = natal lagna (Virgo) —
      see tests/fixtures/jhora_david_ashtakavarga.md. Per-cell parity
      validated Session 54: 96/96 BAV cells + 12/12 SAV cells vs
      tests/fixtures/jhora_david_ashtakavarga.md (David, hardest case),
      incl. both Parasara/Varahamihira sentinel cells (Moon-Ar=3,
      Venus-Le=4) — Parasara convention confirmed end-to-end. See
      tests/calculations/ashtakavarga/test_ashtakavarga.py.
  (d) Algorithm and Aries-absolute (no lagna-rotation) indexing convention
      matches PyJHora's raw computation kernel — see
      diagnostics/pyjhora_ashtakavarga_indexing_20260706.md.
  (e) Contributor-set consumer spec: PVR Narasimha Rao, "Vedic Astrology:
      An Integrated Approach", ch. 25.5.2 / Table 60 — Prastaara
      Ashtakavarga kakshya scoring needs, per (owner, sign) cell, WHICH
      contributors donate a bindu (not just the bindu count), since a
      kakshya's rekha depends on whether the transiting planet is benefic
      w.r.t. that kakshya's lord. See compute_bav_contributors().

OUT OF SCOPE (not implemented here): trikona sodhana, ekadhipatya sodhana,
sodhya pindas, kakshya divisions, transit/gochara Ashtakavarga scoring.
Raw BAV + SAV only.
"""

from __future__ import annotations

from agent.chart_calculator import SIGNS

_CONTRIBUTORS: tuple[str, ...] = (
    "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Lagna",
)
_PLANETS: tuple[str, ...] = _CONTRIBUTORS[:-1]  # excludes Lagna, for SAV

_CANONICAL_BAV_TOTAL: dict[str, int] = {
    "Sun": 48, "Moon": 49, "Mars": 39, "Mercury": 54,
    "Jupiter": 56, "Venus": 52, "Saturn": 39, "Lagna": 49,
}
_CANONICAL_SAV_TOTAL = 337

# AV_TABLES[owner][reference] = benefic houses (1-12) counted from the
# reference's own occupied sign (reference's sign = house 1). PVR Tables
# 19-26, Parasara convention -- see module CITATION.
AV_TABLES: dict[str, dict[str, tuple[int, ...]]] = {
    "Sun": {
        "Sun": (1, 2, 4, 7, 8, 9, 10, 11),
        "Moon": (3, 6, 10, 11),
        "Mars": (1, 2, 4, 7, 8, 9, 10, 11),
        "Mercury": (3, 5, 6, 9, 10, 11, 12),
        "Jupiter": (5, 6, 9, 11),
        "Venus": (6, 7, 12),
        "Saturn": (1, 2, 4, 7, 8, 9, 10, 11),
        "Lagna": (3, 4, 6, 10, 11, 12),
    },
    "Moon": {
        "Sun": (3, 6, 7, 8, 10, 11),
        "Moon": (1, 3, 6, 7, 9, 10, 11),
        "Mars": (2, 3, 5, 6, 10, 11),
        "Mercury": (1, 3, 4, 5, 7, 8, 10, 11),
        "Jupiter": (1, 2, 4, 7, 8, 10, 11),
        "Venus": (3, 4, 5, 7, 9, 10, 11),
        "Saturn": (3, 5, 6, 11),
        "Lagna": (3, 6, 10, 11),
    },
    "Mars": {
        "Sun": (3, 5, 6, 10, 11),
        "Moon": (3, 6, 11),
        "Mars": (1, 2, 4, 7, 8, 10, 11),
        "Mercury": (3, 5, 6, 11),
        "Jupiter": (6, 10, 11, 12),
        "Venus": (6, 8, 11, 12),
        "Saturn": (1, 4, 7, 8, 9, 10, 11),
        "Lagna": (1, 3, 6, 10, 11),
    },
    "Mercury": {
        "Sun": (5, 6, 9, 11, 12),
        "Moon": (2, 4, 6, 8, 10, 11),
        "Mars": (1, 2, 4, 7, 8, 9, 10, 11),
        "Mercury": (1, 3, 5, 6, 9, 10, 11, 12),
        "Jupiter": (6, 8, 11, 12),
        "Venus": (1, 2, 3, 4, 5, 8, 9, 11),
        "Saturn": (1, 2, 4, 7, 8, 9, 10, 11),
        "Lagna": (1, 2, 4, 6, 8, 10, 11),
    },
    "Jupiter": {
        "Sun": (1, 2, 3, 4, 7, 8, 9, 10, 11),
        "Moon": (2, 5, 7, 9, 11),
        "Mars": (1, 2, 4, 7, 8, 10, 11),
        "Mercury": (1, 2, 4, 5, 6, 9, 10, 11),
        "Jupiter": (1, 2, 3, 4, 7, 8, 10, 11),
        "Venus": (2, 5, 6, 9, 10, 11),
        "Saturn": (3, 5, 6, 12),
        "Lagna": (1, 2, 4, 5, 6, 7, 9, 10, 11),
    },
    "Venus": {
        "Sun": (8, 11, 12),
        "Moon": (1, 2, 3, 4, 5, 8, 9, 11, 12),
        "Mars": (3, 4, 6, 9, 11, 12),
        "Mercury": (3, 5, 6, 9, 11),
        "Jupiter": (5, 8, 9, 10, 11),
        "Venus": (1, 2, 3, 4, 5, 8, 9, 10, 11),
        "Saturn": (3, 4, 5, 8, 9, 10, 11),
        "Lagna": (1, 2, 3, 4, 5, 8, 9, 11),
    },
    "Saturn": {
        "Sun": (1, 2, 4, 7, 8, 10, 11),
        "Moon": (3, 6, 11),
        "Mars": (3, 5, 6, 10, 11, 12),
        "Mercury": (6, 8, 9, 10, 11, 12),
        "Jupiter": (5, 6, 11, 12),
        "Venus": (6, 11, 12),
        "Saturn": (3, 5, 6, 11),
        "Lagna": (1, 3, 4, 6, 10, 11),
    },
    "Lagna": {
        "Sun": (3, 4, 6, 10, 11, 12),
        "Moon": (3, 6, 10, 11, 12),
        "Mars": (1, 3, 6, 10, 11),
        "Mercury": (1, 2, 4, 6, 8, 10, 11),
        "Jupiter": (1, 2, 4, 5, 6, 7, 9, 10, 11),
        "Venus": (1, 2, 3, 4, 5, 8, 9),
        "Saturn": (1, 3, 4, 6, 10, 11),
        "Lagna": (3, 6, 10, 11),
    },
}


def compute_bav(placements: dict[str, str]) -> dict[str, dict[str, int]]:
    """Bhinna Ashtakavarga for the 7 planets + Lagna.

    Args:
        placements: {"Sun": sign, "Moon": sign, ..., "Saturn": sign,
            "Lagna": sign} — exactly these 8 contributor keys (title-case,
            matching agent.chart_calculator's planet-name convention), each
            mapped to one of the 12 title-case sign names in
            agent.chart_calculator.SIGNS.

    Returns:
        {contributor: {sign: bindus}} for all 8 contributors, each sign
        dict covering all 12 signs (Aries..Pisces) with int bindus 0-8.

    Raises:
        ValueError: placements missing/has unknown contributor keys, or
            any placement value is not a recognized sign name.
    """
    missing = set(_CONTRIBUTORS) - set(placements.keys())
    if missing:
        raise ValueError(
            f"placements missing required contributor(s): {sorted(missing)} "
            f"(got keys {sorted(placements.keys())})"
        )
    extra = set(placements.keys()) - set(_CONTRIBUTORS)
    if extra:
        raise ValueError(
            f"placements has unknown contributor key(s): {sorted(extra)}; "
            f"expected exactly {sorted(_CONTRIBUTORS)}"
        )
    for contributor, sign in placements.items():
        if sign not in SIGNS:
            raise ValueError(
                f"placements[{contributor!r}] has unrecognized sign {sign!r}; "
                f"expected one of {SIGNS}"
            )

    sign_index = {contributor: SIGNS.index(sign) for contributor, sign in placements.items()}

    bav: dict[str, dict[str, int]] = {}
    for owner in _CONTRIBUTORS:
        bindus = [0] * 12
        owner_table = AV_TABLES[owner]
        for reference in _CONTRIBUTORS:
            s = sign_index[reference]
            for house in owner_table[reference]:
                idx = (s + house - 1) % 12
                bindus[idx] += 1
        total = sum(bindus)
        assert total == _CANONICAL_BAV_TOTAL[owner], (
            f"{owner} BAV total {total} != canonical {_CANONICAL_BAV_TOTAL[owner]} "
            f"(position-invariant check failed — AV_TABLES[{owner!r}] is corrupt)"
        )
        bav[owner] = {SIGNS[i]: bindus[i] for i in range(12)}

    return bav


def compute_sav(bav: dict[str, dict[str, int]]) -> dict[str, int]:
    """Sarvashtakavarga — sums the 7 PLANET BAVs only (Lagna excluded, JHora
    convention: SAV grand total is 337, not the 386 a Lagna-inclusive sum
    would give).

    Args:
        bav: compute_bav()'s return value (or any dict with the same
            shape) — must contain all 7 planet keys, each mapped to a
            dict covering all 12 signs.

    Returns:
        {sign: bindus} for all 12 signs, summed across the 7 planets.

    Raises:
        ValueError: bav missing any of the 7 planet keys, or any present
            planet's sign dict is missing one of the 12 signs.
    """
    missing_planets = set(_PLANETS) - set(bav.keys())
    if missing_planets:
        raise ValueError(
            f"bav missing required planet(s): {sorted(missing_planets)} "
            f"(got keys {sorted(bav.keys())})"
        )
    for planet in _PLANETS:
        missing_signs = set(SIGNS) - set(bav[planet].keys())
        if missing_signs:
            raise ValueError(
                f"bav[{planet!r}] missing sign(s): {sorted(missing_signs)}"
            )

    sav = {sign: sum(bav[planet][sign] for planet in _PLANETS) for sign in SIGNS}

    total = sum(sav.values())
    assert total == _CANONICAL_SAV_TOTAL, (
        f"SAV total {total} != canonical {_CANONICAL_SAV_TOTAL} "
        f"(one or more planet BAVs passed in are corrupt)"
    )

    return sav


def compute_bav_contributors(
    placements: dict[str, str],
) -> dict[str, dict[str, frozenset[str]]]:
    """Per-cell BAV contributor sets, for Prastaara Ashtakavarga kakshya
    scoring (see module CITATION (e)): a kakshya has a rekha iff the
    transiting planet is benefic in the rasi w.r.t. that kakshya's lord
    (PVR ch. 25.5.2, Table 60), which requires knowing WHICH contributors
    donate a bindu to a cell, not just the bindu count. Kakshya lord order
    (Saturn, Jupiter, Mars, Sun, Venus, Mercury, Moon, Lagna; 3d45' divisions)
    and the transit scoring itself belong to a future transit-scorer module,
    NOT here.

    Args:
        placements: same contract as compute_bav().

    Returns:
        {owner: {sign: frozenset of contributor names}} for all 8
        contributors x 12 signs — contributor names are drawn from the same
        8-name set as placements' keys ('Sun'..'Saturn', 'Lagna').

    Raises:
        ValueError: same conditions as compute_bav() (delegated to it).
    """
    bav = compute_bav(placements)

    sign_index = {contributor: SIGNS.index(sign) for contributor, sign in placements.items()}

    contributors: dict[str, dict[str, frozenset[str]]] = {}
    for owner in _CONTRIBUTORS:
        owner_table = AV_TABLES[owner]
        donors: list[set[str]] = [set() for _ in range(12)]
        for reference in _CONTRIBUTORS:
            s = sign_index[reference]
            for house in owner_table[reference]:
                idx = (s + house - 1) % 12
                donors[idx].add(reference)

        contributors[owner] = {}
        for i in range(12):
            sign = SIGNS[i]
            contributor_set = frozenset(donors[i])
            expected = bav[owner][sign]
            assert len(contributor_set) == expected, (
                f"contributor-set size for owner={owner!r} sign={sign!r} "
                f"is {len(contributor_set)} != compute_bav()'s bindu count "
                f"{expected} (contributor-counting logic has diverged from "
                f"compute_bav's bindu-counting logic)"
            )
            contributors[owner][sign] = contributor_set

    return contributors
