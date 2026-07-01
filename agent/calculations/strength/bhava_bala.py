"""Bhava Bala — all three sub-components + aggregate (BPHS 27.26-31).

Source: BPHS 27.26-31; B.V. Raman "Graha and Bhava Balas".

Sub-components:
  compute_bhavadhipati_bala  — real implementation; AstroSage-validated.
  compute_bhava_dig_bala     — V1 STUB (formula investigated, root cause unresolved).
  compute_bhava_drishti_bala — V1 STUB (shares Drik Bala's unresolved kernel).

Aggregate:
  compute_bhava_bala_totals  — combines all three; carries dig_is_stubbed and
                               drishti_is_stubbed flags on every house entry.

See CLAUDE.md Known Source Divergences for both stub rationales.
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


def compute_bhava_dig_bala(house_signs: dict[int, str]) -> dict[int, float]:
    """V1 STUB — always returns 0.0 for all 12 houses.

    See CLAUDE.md Known Source Divergences — 'Bhava Dig Bala' for why.
    DO NOT silently consume this downstream without checking the
    accompanying caveat; any aggregator combining this with
    Bhavadhipati Bala or Bhava Drishti Bala must carry a mandatory
    dig_is_stubbed: bool field, same pattern as shadbala_totals.py's
    drik_is_stubbed.
    """
    if set(house_signs.keys()) != set(range(1, 13)):
        raise ValueError(
            f"house_signs must have exactly keys 1-12, got {sorted(house_signs.keys())}"
        )
    return {h: 0.0 for h in range(1, 13)}


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
    "V1: bhava_dig and bhava_drishti are stubbed at 0.0 "
    "(see CLAUDE.md Known Source Divergences). "
    "total_virupa equals bhavadhipati only; rank may shift when stubs are resolved."
)


def compute_bhava_bala_totals(
    house_signs: dict[int, str],
    shadbala_totals: dict[str, float],
) -> dict[int, dict]:
    """Aggregate all 3 Bhava Bala sub-components per house.

    Returns dict keyed 1-12. Each value contains:
        bhavadhipati: float  — real computation
        bhava_dig: float     — always 0.0 V1 (stub)
        bhava_drishti: float — always 0.0 V1 (stub)
        total_virupa: float  — sum of the 3 components
        total_rupa: float    — total_virupa / 60, rounded to 2 dp
        rank: int            — 1 (strongest) to 12 (weakest), by total_virupa
                               descending; lower house number wins ties
        dig_is_stubbed: bool     — always True V1
        drishti_is_stubbed: bool — always True V1
        caveat: str          — fixed note on both stubs (mirrors shadbala_totals.py)

    shadbala_totals must use title-case keys ('Sun', 'Jupiter', ...) — see
    compute_bhavadhipati_bala docstring for the casing contract.
    """
    bhavadhipati = compute_bhavadhipati_bala(house_signs, shadbala_totals)
    dig = compute_bhava_dig_bala(house_signs)
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
            "dig_is_stubbed": True,
            "drishti_is_stubbed": True,
            "caveat": _BHAVA_BALA_V1_CAVEAT,
        }

    # rank 1 = strongest; tie-break: lower house number gets the better rank.
    for rank, house in enumerate(
        sorted(range(1, 13), key=lambda h: (-result[h]["total_virupa"], h)), 1
    ):
        result[house]["rank"] = rank

    return result
