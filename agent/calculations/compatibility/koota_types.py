"""Shared types for the Ashtakoot koota calculators (P2.4.1a/b/c).

Naming-convention note: NOT underscore-prefixed, unlike _ashtakoot_tables.py.
The underscore-prefix convention in this package (and in
calculations/core/_dignity_tables.py, _friendship_tables.py,
_panchanga_tables.py, _aspects_tables.py) marks internal, data-only lookup
tables with no public API surface of their own -- callers go through a
public calculator module, never import the table module's contents
directly as their primary interface. KootaNatalInfo and KootaResult are
the opposite: they ARE the public API surface every koota calculator
function consumes and returns. This matches the project's existing
precedent for dataclass-holding public modules (chandrabala.py's
ChandrabalaStatus/ChandrabalaWindow, muhurta_scorer.py's MuhurtaScore/
MuhurtaWindow, navamsa.py's NavamsaPlacement/NavamsaChart -- none of those
carry an underscore prefix either).

Validation (moon_sign in 0..11, nakshatra in 0..26, moon_longitude in
[0, 360)) is NOT performed here -- these are plain frozen dataclasses, no
__post_init__ checks, matching the project's existing precedent (e.g.
ChandrabalaStatus has no self-validation; compute_chandrabala() raises
ValueError instead). Each koota calculator function in trivial.py (and
its P2.4.1b/c siblings) validates its own KootaNatalInfo inputs.
"""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class KootaNatalInfo:
    moon_sign: int          # 0=Aries..11=Pisces
    moon_longitude: float   # sidereal degrees, [0, 360)
    nakshatra: int          # 0=Ashwini..26=Revati


@dataclass(frozen=True)
class KootaResult:
    score: float                    # half-points are real (e.g. Graha Maitri's 0.5 tier)
    max_score: int                  # matches KOOTA_SCORE_WEIGHTS in _ashtakoot_tables.py
    details: dict[str, Any]         # per-koota intermediates (e.g. boy_varna, girl_vashya_group)
    warnings: tuple[str, ...]       # deterministic order, empty tuple if none
