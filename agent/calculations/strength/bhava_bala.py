"""Bhava Bala — all three sub-components + aggregate (BPHS 27.26-31).

Source: BPHS 27.26-31; B.V. Raman "Graha and Bhava Balas".

Sub-components:
  compute_bhavadhipati_bala  — real implementation; AstroSage-validated.
  compute_bhava_dig_bala     — real implementation, ported from PyJHora's
                               rasi-animal-group taper formula (Porphyry
                               cusps required — see function docstring).
  compute_bhava_drishti_bala — V1 STUB (shares Drik Bala's unresolved kernel).

Aggregate:
  compute_bhava_bala_totals  — combines all three; carries dig_is_stubbed and
                               drishti_is_stubbed flags on every house entry.

See CLAUDE.md Known Source Divergences for the drishti stub rationale (and
the now-superseded dig rationale, pending a SESSION_LOG/CLAUDE.md update).
"""

from __future__ import annotations

from agent.chart_calculator import SIGN_LORDS

_EXPECTED_HOUSES = frozenset(range(1, 13))


def compute_bhavadhipati_bala(
    house_signs: dict[int, str],
    shadbala_totals: dict[str, float],
) -> dict[int, float]:
    """Return Bhavadhipati Bala (Virupa) for each of the 12 houses.

    For each house, looks up its sign's ruling planet via SIGN_LORDS and
    returns that planet's Shadbala virupa total.

    Args:
        house_signs: {1: "Sagittarius", 2: "Capricorn", ...} — exactly 12
            entries with integer keys 1-12, whole-sign house assignment.
        shadbala_totals: planet name → virupa total. Keys must be
            title-case planet names ('Sun', 'Jupiter', ...) matching the
            SIGN_LORDS convention — NOT the lowercase keys ('sun',
            'jupiter') that compute_shadbala_totals() returns natively.
            Callers must capitalize before passing (e.g.
            ``{p.capitalize(): v for p, v in raw.items()}``). See
            test_bhava_bala.py::test_e_live_compute_wiring_smoke for the
            required bridge. This casing mismatch between
            shadbala_totals.py (lowercase) and the rest of the codebase
            (title-case: SIGN_LORDS, dignity.py, pancha_mahapurusha.py)
            is a known inconsistency flagged for a future cleanup pass.
            Must include the lord of every sign present in house_signs.

    Returns:
        {1: 405.2, 2: 423.16, ...} — house number → Bhavadhipati Bala.

    Raises:
        ValueError: if house_signs does not have exactly 12 entries with keys
            1-12, contains an unrecognised sign, or shadbala_totals is missing
            the lord for any house's sign.
    """
    if set(house_signs.keys()) != _EXPECTED_HOUSES:
        missing = _EXPECTED_HOUSES - set(house_signs.keys())
        extra = set(house_signs.keys()) - _EXPECTED_HOUSES
        raise ValueError(
            f"house_signs must have exactly keys 1-12; "
            f"missing={sorted(missing)}, extra={sorted(extra)}"
        )

    result: dict[int, float] = {}
    for house, sign in house_signs.items():
        if sign not in SIGN_LORDS:
            raise ValueError(
                f"House {house}: sign {sign!r} not recognised — "
                f"expected one of {sorted(SIGN_LORDS)}"
            )
        lord = SIGN_LORDS[sign]
        if lord not in shadbala_totals:
            raise ValueError(
                f"House {house}: sign {sign!r} is ruled by {lord!r}, "
                f"but {lord!r} is missing from shadbala_totals "
                f"(keys present: {sorted(shadbala_totals)})"
            )
        result[house] = shadbala_totals[lord]

    return result


# Verbatim from PyJHora const.py — nara_rasi_longitudes, jalachara_rasi_longitudes,
# chatushpada_rasis, keeta_rasis. Absolute sidereal longitude (0-360), NOT
# per-sign 0-30 offsets. Keyed by the house-offset anchor PyJHora's own
# strength.py._bhava_dig_bala uses (brl dict: {0:nara, 3:jalachara, 9:chatushpada,
# 6:keeta}) — house-index-0 = Lagna/1st, 3 = 4th/IC, 6 = 7th/Desc, 9 = 10th/MC.
# See this session's PyJHora investigation report for the source extraction.
_RASI_GROUP_RANGES: dict[int, list[tuple[float, float]]] = {
    0: [(60, 90), (150, 180), (180, 210), (240, 255), (300, 330)],  # Nara (human)
    3: [(90, 120), (285, 300), (330, 360)],                         # Jalachara (aquatic)
    9: [(0, 30), (30, 60), (120, 150), (255, 270), (270, 285)],     # Chatushpada (quadruped)
    6: [(210, 240)],                                                # Keeta (insect)
}


def compute_bhava_dig_bala(
    house_signs: dict[int, str],
    house_cusps: dict[int, float],
) -> dict[str, object]:
    """Bhava Dig Bala — real implementation, ported from PyJHora's
    strength.py _bhava_dig_bala (BPHS-derived rasi-animal-group taper).

    This is a DIFFERENT formula family from the originally-attempted
    continuous "angular distance from weak cusp / 3" formula (see CLAUDE.md
    Known Source Divergences — 'Bhava Dig Bala (Session 41 investigation...)'
    for that earlier, rejected hypothesis) — not a refinement of it. Instead
    of a continuous arc, each house's OWN cusp longitude is classified into
    one of four classical rasi-animal groups (Nara/human, Jalachara/aquatic,
    Chatushpada/quadruped, Keeta/insect — see _RASI_GROUP_RANGES), and the
    house receives a value tapering by its offset from that group's anchor
    house (Lagna, 4th/IC, 7th/Desc, or 10th/MC respectively): 60 Virupa at
    the anchor itself, decreasing by 10 per house step away.

    Cusp system: house_cusps MUST be Porphyry ('Sripati' in JHora) cusps,
    NOT the equal-house/whole-sign scheme used elsewhere in this codebase
    for sign/house placement — see agent.chart_calculator.
    compute_porphyry_house_cusps(). PyJHora's own _bhava_dig_bala reads
    bhava_method=2 ('Sripati method'), which is mathematically equivalent to
    pyswisseph's hsys=b'O' (both trisect the arc between the house-system-
    invariant angular cusps).

    Upstream quirk (replicated, not silently hidden): PyJHora's own loop
    spans 14 house-offsets (h in range(-7,7)) over a 12-house cycle, so per
    rasi-group anchor, exactly 2 houses get visited by two different h
    values (the wraparound pairs h=-7/h=+5 and h=-6/h=+6). PyJHora's
    dict-comprehension aggregation keeps whichever value was written last,
    which depends on Python set/dict iteration order and is not a
    principled max/sum. In practice this does not affect the VALUE: the
    taper formula abs(60 - abs(h)*10) is symmetric, so both wraparound
    pairs always produce identical values for a given house (|-7| and |5|
    are equidistant from 60 in the taper, likewise |-6| and |6|) — verified
    algebraically this session. We replicate "last write wins" using a
    fixed, deterministic iteration order (unlike PyJHora's hash-order
    dependent one) and surface any house that received >1 candidate via
    multi_match_houses, so a genuine divergence (e.g. a cusp landing exactly
    on a rasi-group boundary, matching two DIFFERENT groups) is visible
    rather than silently resolved.

    Args:
        house_signs: {1: "Sagittarius", ...} — exactly 12 entries, keys 1-12.
            Used only for input-shape validation (kept for API symmetry with
            the other Bhava Bala sub-components); the formula itself reads
            house_cusps, not house_signs.
        house_cusps: {1: cusp1_lon, ..., 12: cusp12_lon} — Porphyry/Sripati
            absolute sidereal longitude (0-360) per house. See
            agent.chart_calculator.compute_porphyry_house_cusps().

    Returns:
        {
            "values": {1: 60.0, ..., 12: float},  # Virupa, range [0, 60]
            "multi_match_houses": [],             # house numbers with >1
                                                    # candidate match (see quirk above)
        }

    Raises:
        ValueError: house_signs or house_cusps missing keys 1-12.
        RuntimeError: a house's cusp longitude matched none of the 4
            rasi-animal-group ranges — should not happen (the 4 groups
            partition the full 360 with no gaps) but is not assumed silently.
    """
    if set(house_signs.keys()) != set(range(1, 13)):
        raise ValueError(
            f"house_signs must have exactly keys 1-12, got {sorted(house_signs.keys())}"
        )
    if set(house_cusps.keys()) != set(range(1, 13)):
        raise ValueError(
            f"house_cusps must have exactly keys 1-12, got {sorted(house_cusps.keys())}"
        )

    # 0-indexed house cusps (bm[i] = house (i+1)'s cusp), matching PyJHora's
    # own bm array indexing in strength.py._bhava_dig_bala.
    bm = {i: house_cusps[i + 1] % 360.0 for i in range(12)}

    candidates: dict[int, list[float]] = {i: [] for i in range(12)}
    for k, ranges in _RASI_GROUP_RANGES.items():
        group_matches: dict[int, float] = {}
        for h in range(-7, 7):
            target = (k + h) % 12
            cusp_lon = bm[target]
            if any(l1 <= cusp_lon <= l2 for l1, l2 in ranges):
                group_matches[target] = abs(60 - abs(h) * 10)
        for target, value in group_matches.items():
            candidates[target].append(value)

    multi_match_houses: list[int] = []
    values: dict[int, float] = {}
    for i in range(12):
        house = i + 1
        matches = candidates[i]
        if not matches:
            raise RuntimeError(
                f"compute_bhava_dig_bala: house {house} (cusp={bm[i]:.4f}) "
                f"matched none of the 4 rasi-animal-group longitude ranges "
                f"(Nara/Jalachara/Chatushpada/Keeta) — expected full 360deg "
                f"coverage with no gaps; see PyJHora strength.py "
                f"_bhava_dig_bala and const.py's *_rasi_longitudes constants"
            )
        if len(matches) > 1:
            multi_match_houses.append(house)
        values[house] = matches[-1]

    return {"values": values, "multi_match_houses": multi_match_houses}


def compute_bhava_drishti_bala(house_signs: dict[int, str]) -> dict[int, float]:
    """V1 STUB — always returns 0.0 for all 12 houses.

    Shares its root cause with drik_bala.py's stub: both depend on the
    same Drishti Kendra aspect-strength kernel, which has an unresolved
    divergence from AstroSage (see CLAUDE.md Known Source Divergences —
    'Bhava Drishti Bala' and 'Drik Bala'). DO NOT re-derive this kernel
    independently of resolving Drik Bala first — they are the same
    underlying formula gap, not two separate problems.
    """
    if set(house_signs.keys()) != set(range(1, 13)):
        raise ValueError(
            f"house_signs must have exactly keys 1-12, got {sorted(house_signs.keys())}"
        )
    return {h: 0.0 for h in range(1, 13)}


_BHAVA_BALA_V1_CAVEAT = (
    "V1: bhava_drishti is stubbed at 0.0 "
    "(see CLAUDE.md Known Source Divergences). bhava_dig is real (PyJHora "
    "rasi-animal-group formula, Porphyry cusps). total_virupa omits the "
    "drishti contribution; rank may shift when that stub is resolved."
)


def compute_bhava_bala_totals(
    house_signs: dict[int, str],
    shadbala_totals: dict[str, float],
    house_cusps: dict[int, float],
) -> dict[int, dict]:
    """Aggregate all 3 Bhava Bala sub-components per house.

    Returns dict keyed 1-12. Each value contains:
        bhavadhipati: float  — real computation
        bhava_dig: float     — real computation (PyJHora rasi-animal-group
                               formula; see compute_bhava_dig_bala)
        bhava_drishti: float — always 0.0 V1 (stub)
        total_virupa: float  — sum of the 3 components
        total_rupa: float    — total_virupa / 60, rounded to 2 dp
        rank: int            — 1 (strongest) to 12 (weakest), by total_virupa
                               descending; lower house number wins ties
        dig_is_stubbed: bool     — always False (Dig Bala is real, this session)
        drishti_is_stubbed: bool — always True V1
        caveat: str          — fixed note on the remaining stub (mirrors
                               shadbala_totals.py)

    shadbala_totals must use title-case keys ('Sun', 'Jupiter', ...) — see
    compute_bhavadhipati_bala docstring for the casing contract.

    house_cusps must be Porphyry/Sripati cusps (see compute_bhava_dig_bala
    and agent.chart_calculator.compute_porphyry_house_cusps) — NOT the same
    cusps as house_signs, which is whole-sign.
    """
    bhavadhipati = compute_bhavadhipati_bala(house_signs, shadbala_totals)
    dig = compute_bhava_dig_bala(house_signs, house_cusps)["values"]
    drishti = compute_bhava_drishti_bala(house_signs)

    result: dict[int, dict] = {}
    for h in range(1, 13):
        total_v = bhavadhipati[h] + dig[h] + drishti[h]
        result[h] = {
            "bhavadhipati": bhavadhipati[h],
            "bhava_dig": dig[h],
            "bhava_drishti": drishti[h],
            "total_virupa": total_v,
            "total_rupa": round(total_v / 60, 2),
            "rank": 0,  # filled in the ranking pass below
            "dig_is_stubbed": False,
            "drishti_is_stubbed": True,
            "caveat": _BHAVA_BALA_V1_CAVEAT,
        }

    # rank 1 = strongest; tie-break: lower house number gets the better rank.
    for rank, house in enumerate(
        sorted(range(1, 13), key=lambda h: (-result[h]["total_virupa"], h)), 1
    ):
        result[house]["rank"] = rank

    return result
