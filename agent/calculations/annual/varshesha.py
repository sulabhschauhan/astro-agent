"""Varshesha (Lord of the Year) selector -- Tajika consensus rule.

Pure function; PV bala comes from annual/panchavargeeya.py.

FIVE office-bearers (deduped, order kept):
  1 Dinaratri-pati: dispositor of the Moon's sign (night) / Sun's sign (day)
  2 Janma-Lagna lord   3 Muntha-sign lord   4 Varsha-Lagna lord
  5 Trirasi-pati: triplicity lord of the Varsha Lagna by day/night
    (Fire d=Sun/n=Jupiter, Earth d=Venus/n=Moon, Air d=Saturn/n=Mercury,
     Water d=Venus/n=Mars)
ASPECT on the Varsha Lagna by house from it: 3/5/9/11 benefic; 4/7/10 malefic;
1 (conjunction) = inimical, reported as 'malefic' with conjunct=True.
SELECTION: (a) strongest PV among benefic-aspecting; (b) else strongest among
any-aspecting; (c) else, or strongest < MIN_VB, or all candidates equal ->
Munthesh (Muntha lord). Every candidate is surfaced (surface-not-gate).

NO desktop oracle exists for the year-lord (JHora declares none): this pins the
consensus rule transcription, not JHora concurrence. PyJHora's max-over-all
deviation is documented, not adopted.
"""
from agent.calculations.annual.panchavargeeya import (
    _SIGN_LORD, _SWE_ID_TO_NAME, pancha_vargeeya_bala)

LAGNA_KEY = "Lagna"      # key of the Varsha Lagna longitude in the positions dict
MIN_VB = 5.0             # floor: below 'Ordinary' the aspecting lord is too weak to rule the year
_BENEFIC_HOUSES = frozenset({3, 5, 9, 11})
_MALEFIC_HOUSES = frozenset({1, 4, 7, 10})
_ID_BY_NAME = {n: i for i, n in _SWE_ID_TO_NAME.items()}
# sign % 4 (0 fire, 1 earth, 2 air, 3 water) -> (day lord, night lord)
_TRIRASI = {0: ("Sun", "Jupiter"), 1: ("Venus", "Moon"),
            2: ("Saturn", "Mercury"), 3: ("Venus", "Mars")}


def _sign(lon: float) -> int:
    return int(lon // 30) % 12


def _lord(sign: int) -> int:
    return _ID_BY_NAME[_SIGN_LORD[sign]]


def lord_of_the_year(annual_d1_positions: dict, natal_lagna_sign: int,
                     muntha_sign: int, is_night_pravesh: bool) -> dict:
    """annual_d1_positions: swisseph id -> sidereal lon for the 7 planets, plus
    LAGNA_KEY -> Varsha Lagna lon. Signs are 0..11 (Aries=0).

    Returns {candidates, winner (swisseph id), rule_path}.
    Raises ValueError on missing inputs or out-of-range signs.
    """
    if LAGNA_KEY not in annual_d1_positions:
        raise ValueError(f"lord_of_the_year: positions need key {LAGNA_KEY!r}")
    for nm, sg in (("natal_lagna_sign", natal_lagna_sign), ("muntha_sign", muntha_sign)):
        if not (isinstance(sg, int) and 0 <= sg <= 11):
            raise ValueError(f"lord_of_the_year: {nm} must be int 0..11, got {sg!r}")
    pv = pancha_vargeeya_bala(annual_d1_positions)  # ValueError if planets missing
    lagna_sign = _sign(annual_d1_positions[LAGNA_KEY])

    ref = _ID_BY_NAME["Moon"] if is_night_pravesh else _ID_BY_NAME["Sun"]
    tri = _TRIRASI[lagna_sign % 4][1 if is_night_pravesh else 0]
    offices = [
        ("dinaratri", _lord(_sign(annual_d1_positions[ref]))),
        ("janma_lagna", _lord(natal_lagna_sign)),
        ("muntha", _lord(muntha_sign)),
        ("varsha_lagna", _lord(lagna_sign)),
        ("trirasi", _ID_BY_NAME[tri]),
    ]
    seen, cands = set(), []
    for office, pid in offices:
        if pid in seen:
            continue
        seen.add(pid)
        house = (_sign(annual_d1_positions[pid]) - lagna_sign) % 12 + 1
        aspect = ("benefic" if house in _BENEFIC_HOUSES
                  else "malefic" if house in _MALEFIC_HOUSES else "none")
        cands.append({"office": office, "planet": pid, "house_from_lagna": house,
                      "aspect": aspect, "conjunct": house == 1, "pv_bala": pv[pid][0]})

    munthesh = _lord(muntha_sign)
    benefic = [c for c in cands if c["aspect"] == "benefic"]
    aspecting = [c for c in cands if c["aspect"] != "none"]
    if len({round(c["pv_bala"], 6) for c in cands}) == 1:
        return {"candidates": cands, "winner": munthesh,
                "rule_path": "all candidates equal -> Munthesh"}
    pool, label = (benefic, "benefic-aspecting") if benefic else (aspecting, "any-aspecting")
    if not pool:
        return {"candidates": cands, "winner": munthesh,
                "rule_path": "no candidate aspects Lagna -> Munthesh"}
    best = max(pool, key=lambda c: c["pv_bala"])
    if best["pv_bala"] < MIN_VB:
        return {"candidates": cands, "winner": munthesh,
                "rule_path": f"strongest {label} < {MIN_VB} VB -> Munthesh"}
    return {"candidates": cands, "winner": best["planet"],
            "rule_path": f"strongest {label} ({best['office']})"}
