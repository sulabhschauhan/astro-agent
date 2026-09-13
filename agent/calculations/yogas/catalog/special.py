"""Special and miscellaneous yoga definitions.

Fills the Phase-0 stub of the same name. Same contract as `raja_yogas`:
PURE over the fact block, and every rule reports a NOT-FIRED reason.

TWO RULE FAMILIES HERE
----------------------
1. VIPAREETA RAJA YOGA -- Harsha / Sarala / Vimala. A dusthana lord (6, 8, 12)
   placed in ANOTHER dusthana. The definition is CONTESTED and the split is
   real, not an OCR artifact: Uttara Kalamrita requires the lord in one of the
   OTHER TWO dusthanas, while several later compilations also count the lord in
   its OWN dusthana. This module takes the Uttara Kalamrita reading and marks
   each rule `contested=True` with the divergence named, so the answer can say
   which definition it used rather than quietly picking one. Do NOT "fix" this
   by widening the condition -- that is the tiebreaker decision, and it is
   Sulabh's, not this module's.
2. GAJAKESARI -- Moon and Jupiter in mutual kendra. Widely mis-reported by
   consumer chart apps, so an explicit NOT-FIRED verdict has direct value.

Python 3.11.
"""
from __future__ import annotations

DUSTHANAS = (6, 8, 12)
KENDRA_FROM = (1, 4, 7, 10)

_VRY_SOURCE = "Uttara Kalamrita (Vipareeta Raja Yoga); cf. BPHS ch.48"
_VRY_CONTEST = ("Uttara Kalamrita requires the lord in one of the OTHER two "
                "dusthanas; some later compilations also count the lord in its "
                "own dusthana. This uses the Uttara Kalamrita reading.")
_GK_SOURCE = "BPHS ch.36 Many Other Yogas"

# name -> (owning house, the houses its lord must occupy)
_VIPAREETA = {
    "Harsha Yoga": (6, (8, 12)),
    "Sarala Yoga": (8, (6, 12)),
    "Vimala Yoga": (12, (6, 8)),
}


def _house_lords(facts: dict) -> dict[int, dict]:
    raw = facts.get("house_lords") or {}
    out: dict[int, dict] = {}
    for k, v in raw.items():
        try:
            out[int(k)] = v
        except (TypeError, ValueError):
            continue
    return out


def _ordinal(n: int) -> str:
    if 10 <= n % 100 <= 20:
        return f"{n}th"
    return f"{n}{ {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th') }"


def detect(facts: dict) -> list[dict]:
    out = _vipareeta(facts)
    gk = _gajakesari(facts)
    if gk:
        out.append(gk)
    return out


def _vipareeta(facts: dict) -> list[dict]:
    lords = _house_lords(facts)
    out: list[dict] = []
    for name, (owner, targets) in _VIPAREETA.items():
        row = lords.get(owner)
        rid = name.split()[0].lower() + "_yoga"
        if not row:
            out.append({"id": rid, "name": name, "fired": False,
                        "reason": f"the {_ordinal(owner)} lord is not known",
                        "evidence": [], "source": _VRY_SOURCE,
                        "contested": True, "contested_note": _VRY_CONTEST})
            continue
        where = row.get("in_house")
        fired = where in targets
        target_txt = " or the ".join(_ordinal(t) for t in targets)
        if fired:
            why = (f"the {_ordinal(owner)} lord ({row['lord']}) is in the "
                   f"{_ordinal(int(where))}, one of the difficult houses this "
                   f"yoga requires")
        elif where == owner:
            why = (f"the {_ordinal(owner)} lord ({row['lord']}) is in the "
                   f"{_ordinal(owner)} itself; this definition requires the "
                   f"{target_txt}, so it does not qualify")
        else:
            why = (f"the {_ordinal(owner)} lord ({row['lord']}) is in the "
                   f"{_ordinal(int(where))}, not the {target_txt}")
        out.append({
            "id": rid, "name": name, "fired": bool(fired), "reason": why,
            "evidence": [f"house_lords.{owner}.lord={row.get('lord')}",
                         f"house_lords.{owner}.in_house={where}"],
            "source": _VRY_SOURCE,
            "contested": True, "contested_note": _VRY_CONTEST,
        })
    return out


def _gajakesari(facts: dict):
    """Moon and Jupiter in mutual kendra (1, 4, 7 or 10 houses apart)."""
    pos = facts.get("planet_positions") or {}
    moon, jup = pos.get("Moon"), pos.get("Jupiter")
    if not (isinstance(moon, dict) and isinstance(jup, dict)):
        return None
    try:
        mh, jh = int(moon["house"]), int(jup["house"])
    except (KeyError, TypeError, ValueError):
        return None

    # Houses counted inclusively from one to the other, the classical way.
    sep = ((jh - mh) % 12) + 1
    fired = sep in KENDRA_FROM
    if fired:
        why = (f"Jupiter stands {_ordinal(sep)} from the Moon, one of the "
               f"supporting angles this yoga requires")
    else:
        why = (f"Jupiter stands {_ordinal(sep)} from the Moon (Moon in the "
               f"{_ordinal(mh)}, Jupiter in the {_ordinal(jh)}); the yoga needs "
               f"them 1, 4, 7 or 10 houses apart")
    return {
        "id": "gajakesari_yoga", "name": "Gajakesari Yoga",
        "fired": bool(fired), "reason": why,
        "evidence": [f"planet_positions.Moon.house={mh}",
                     f"planet_positions.Jupiter.house={jh}"],
        "source": _GK_SOURCE,
    }
