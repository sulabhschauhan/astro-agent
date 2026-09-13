"""Raja yoga definitions -- kendra-trikona lord links.

Fills the Phase-0 stub of the same name. PURE: every function takes the
already-computed fact block and returns verdicts. No ephemeris, no
`chart_calculator` import, no calculation of a chart fact -- the S124 lock
and the S20 "don't touch chart_calculator" lock both hold by construction.

WHY VERDICTS AND NOT A LIST OF HITS
-----------------------------------
Every rule reports whether it FIRED **and, when it did not, why not**. The
not-fired reason is the product feature: "you do not have Gajakesari, because
your Moon and Jupiter are six houses apart" is the half of a good answer this
pipeline has never been able to produce. A detector that returns only hits
throws that away.

DOCTRINE: BPHS Ch.34 (Yoga Karakas) and Ch.36 (Many Other Yogas). A kendra
lord (1/4/7/10) linked to a trikona lord (1/5/9) by conjunction or mutual
aspect is the Raja Yoga condition. The 9th-10th case (Dharma-Karmadhipati) is
reported separately because it is the strongest named member and readers ask
for it by name.

Python 3.11.
"""
from __future__ import annotations

KENDRA_HOUSES = (1, 4, 7, 10)
TRIKONA_HOUSES = (1, 5, 9)

_SOURCE = "BPHS ch.34 Yoga Karakas"


def _house_lords(facts: dict) -> dict[int, dict]:
    """`house_lords` with integer keys. Tolerates the JSON string keys the
    capture round-trip produces."""
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


def _aspects_between(facts: dict, a: str, b: str) -> bool:
    """True when `a` and `b` aspect each other, per the restated
    `aspected_by` map. One-way and mutual are NOT distinguished here; the
    caller reports whichever direction it found."""
    ab = (facts.get("aspects") or {}).get("aspected_by") or {}
    return b in (ab.get(a) or []) or a in (ab.get(b) or [])


def detect(facts: dict) -> list[dict]:
    """Every Raja-yoga rule in this module, fired or not."""
    lords = _house_lords(facts)
    if not lords:
        return []

    out: list[dict] = []
    out.append(_dharma_karmadhipati(lords))
    out.extend(_kendra_trikona_links(facts, lords))
    return out


def _dharma_karmadhipati(lords: dict[int, dict]) -> dict:
    """9th lord and 10th lord occupying one house."""
    n, t = lords.get(9), lords.get(10)
    if not (n and t):
        return {"id": "dharma_karmadhipati", "name": "Dharma-Karmadhipati Yoga",
                "fired": False, "reason": "the 9th or 10th lord is not known",
                "evidence": [], "source": _SOURCE}
    same = n.get("in_house") == t.get("in_house")
    if same:
        reason = (f"the 9th lord ({n['lord']}) and the 10th lord ({t['lord']}) "
                  f"both occupy the {_ordinal(int(n['in_house']))} house")
    else:
        reason = (f"the 9th lord ({n['lord']}) is in the "
                  f"{_ordinal(int(n['in_house']))} and the 10th lord "
                  f"({t['lord']}) is in the {_ordinal(int(t['in_house']))}; "
                  f"they do not occupy one house")
    return {
        "id": "dharma_karmadhipati",
        "name": "Dharma-Karmadhipati Yoga",
        "fired": bool(same),
        "reason": reason,
        "evidence": [f"house_lords.9.lord={n['lord']}",
                     f"house_lords.9.in_house={n.get('in_house')}",
                     f"house_lords.10.lord={t['lord']}",
                     f"house_lords.10.in_house={t.get('in_house')}"],
        "source": _SOURCE,
    }


def _kendra_trikona_links(facts: dict, lords: dict[int, dict]) -> list[dict]:
    """Kendra lord linked to trikona lord, by conjunction or by aspect.

    One rule instance per (kendra house, trikona house) pair, so a chart with
    several links reports several -- and a chart with none reports the pairs
    it checked, which is what makes an honest "no Raja Yoga here" possible.

    A planet ruling both a kendra and a trikona is reported as its own kind:
    classically that single planet is a yogakaraka, not a two-planet link.
    """
    out: list[dict] = []
    for k in KENDRA_HOUSES:
        for t in TRIKONA_HOUSES:
            # The 1st house is BOTH a kendra and a trikona. Pairing it with
            # itself would make every lagna lord a yogakaraka, which is noise,
            # not doctrine -- so the degenerate pair is skipped.
            if k == t:
                continue
            kl, tl = lords.get(k), lords.get(t)
            if not (kl and tl):
                continue
            kp, tp = kl.get("lord"), tl.get("lord")
            rid = f"kendra_trikona_{k}_{t}"
            if kp == tp:
                out.append({
                    "id": rid, "name": f"Yogakaraka ({kp})", "fired": True,
                    "reason": (f"{kp} rules both the {_ordinal(k)} (a supporting "
                               f"angle) and the {_ordinal(t)} (a fortune house), "
                               f"so one planet carries both"),
                    "evidence": [f"house_lords.{k}.lord={kp}",
                                 f"house_lords.{t}.lord={tp}"],
                    "source": _SOURCE})
                continue

            conjunct = kl.get("in_house") == tl.get("in_house")
            aspected = _aspects_between(facts, kp, tp)
            fired = bool(conjunct or aspected)
            if conjunct:
                why = (f"the {_ordinal(k)} lord ({kp}) and the {_ordinal(t)} "
                       f"lord ({tp}) share the "
                       f"{_ordinal(int(kl['in_house']))} house")
            elif aspected:
                why = (f"the {_ordinal(k)} lord ({kp}) and the {_ordinal(t)} "
                       f"lord ({tp}) aspect each other")
            else:
                why = (f"the {_ordinal(k)} lord ({kp}, in the "
                       f"{_ordinal(int(kl['in_house']))}) and the "
                       f"{_ordinal(t)} lord ({tp}, in the "
                       f"{_ordinal(int(tl['in_house']))}) neither share a "
                       f"house nor aspect each other")
            out.append({
                "id": rid,
                "name": f"Raja Yoga ({_ordinal(k)}-{_ordinal(t)} lord link)",
                "fired": fired, "reason": why,
                "evidence": [f"house_lords.{k}.lord={kp}",
                             f"house_lords.{k}.in_house={kl.get('in_house')}",
                             f"house_lords.{t}.lord={tp}",
                             f"house_lords.{t}.in_house={tl.get('in_house')}"],
                "source": _SOURCE})
    return out
