"""Astro Agent -- DIVISIONAL FACTS composer (Path B).

Surfaces the domain-relevant varga charts (from the oracle-validated divisional
engine) into a compact fact-block entry, like navamsa/shadbala/jaimini: the
CALLER attaches chart_facts["divisional"] after calculate_chart();
pipeline._fact_block renders it.

Surfaced set (7), each the varga classically consulted for that life area:
  D10 Dasamsa -> career; D7 Saptamsa -> children; D2 Hora -> wealth;
  D30 Trimsamsa -> health; D12 Dwadasamsa -> parents; D3 Drekkana -> siblings;
  D24 Chaturvimsamsa -> education.
The finer vargas (D16/D20/D27/D40/D45/D60) are computed by the engine but NOT
surfaced (payload economy -- add here if a question ever needs one). D9 is
surfaced separately via the navamsa composer.

RESTATE, NEVER RECOMPUTE: calls compute_varga (validated on 4 reference charts).

Varga placements carry NO verification predicate (a different reference frame
than the D1 predicates) -> unfittable; NO gate Requirement -- additive context.

FAIL-SOFT, PER VARGA: each varga computes in its own try, so one failing varga
never drops the others. Returns {} if none succeed; never raises.

Python 3.11.
"""
from __future__ import annotations

import logging

from agent.calculations.vargas.divisional import compute_varga

logger = logging.getLogger(__name__)

__all__ = ["build_divisional_facts"]

_SURFACED = (
    ("D10", "career"), ("D7", "children"), ("D2", "wealth"),
    ("D30", "health"), ("D12", "parents"), ("D3", "siblings"),
    ("D24", "education"),
)


def build_divisional_facts(chart: dict) -> dict:
    """Compute the surfaced varga charts from chart['meta'] (jd_ut, asc_lon).

    Returns {code: {"name","domain","lagna","placements":{planet:{sign,house}}}}
    -- any subset that succeeds; {} if none. Never raises.
    """
    meta = (chart or {}).get("meta") or {}
    jd = meta.get("jd_ut")
    asc = meta.get("asc_lon_sidereal")
    if jd is None or asc is None:
        return {}
    out: dict = {}
    for code, domain in _SURFACED:
        try:
            vc = compute_varga(jd, asc, code)
            out[code] = {
                "name": vc.name,
                "domain": domain,
                "lagna": vc.lagna_sign,
                "placements": {p: {"sign": pl.varga_sign, "house": pl.varga_house}
                               for p, pl in vc.placements.items()},
            }
        except Exception as exc:  # noqa: BLE001 -- one varga failing is not fatal
            logger.warning("divisional %s unavailable: %s", code, exc)
    return out
