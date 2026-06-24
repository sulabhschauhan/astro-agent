"""Symmetric-matrix-lookup Ashtakoot koota calculators -- P2.4.1c.

Hosts the koota calculators whose classical rule reduces to a single
lookup in a pre-built symmetric matrix, keyed by nakshatra-derived group
membership: Yoni (animal-yoni compatibility) and, in a follow-up prompt,
Nadi (Adi/Madhya/Antya pulse grouping). compute_nadi_koota is deliberately
NOT implemented or stubbed here -- Nadi's classical cancellation rule
("same_sign_different_pada", already locked in ak.NADI_CANCELLATION_RULE)
still awaits AstroSage ground-truth data on how that cancellation
interacts with the raw same-Nadi dosha before a calculator can be written
against it. This file ships with exactly one public function.

compute_yoni_koota() takes (boy: KootaNatalInfo, girl: KootaNatalInfo) and
returns a KootaResult (agent.calculations.compatibility.koota_types).
Reads only from agent.calculations.compatibility._ashtakoot_tables, which
is READ-ONLY in this phase (P2.4.1c dependency-discipline lock) -- no new
constants were needed.

Yoni is the cleanest of the 8 kootas per its own module-section docstring
in _ashtakoot_tables.py: no cancellation logic, no directional asymmetry,
no edge cases -- a pure 2-lookup + 1-matrix-cell algorithm. Swap-invariance
is unconditional: ak.YONI_SCORE_MATRIX is symmetric by classical
convention (already enforced by P2.4.0's own
test_yoni_score_matrix_is_symmetric structural test), so
compute_yoni_koota(A, B).score == compute_yoni_koota(B, A).score for
every input pair, not just the ones exercised by this module's own tests.

Implementation note: ak.YONI_SCORE_MATRIX is a 14x14 tuple-of-tuples
indexed by YONI_ANIMALS' integer position, not a dict keyed by
(animal_name, animal_name) pairs (unlike e.g. ak.VARNA_SCORE or
ak.GANA_SCORE, which ARE such dicts) -- _YONI_INDEX below is a local,
code-only re-keying (animal name -> row/column position), not a new
table addition; it mirrors the same index_of pattern already used in
tests/calculations/compatibility/test__ashtakoot_tables.py's own Mahabair
matrix check.
"""

from agent.calculations.compatibility import _ashtakoot_tables as ak
from agent.calculations.compatibility.koota_types import KootaNatalInfo, KootaResult

_YONI_INDEX: dict[str, int] = {animal: i for i, animal in enumerate(ak.YONI_ANIMALS)}


def _validate_nakshatra(info: KootaNatalInfo, label: str) -> None:
    if not (0 <= info.nakshatra <= 26):
        raise ValueError(f"{label}.nakshatra must be 0..26, got {info.nakshatra}")


def compute_yoni_koota(boy: KootaNatalInfo, girl: KootaNatalInfo) -> KootaResult:
    """Yoni Koota (max 4). Resolves each native's animal yoni from their
    nakshatra (ak.YONI_BY_NAKSHATRA), then looks up the symmetric
    compatibility score for that pair of animals in ak.YONI_SCORE_MATRIX.
    See module docstring for the swap-invariance proof and the
    dict-vs-matrix indexing note.
    """
    _validate_nakshatra(boy, "boy")
    _validate_nakshatra(girl, "girl")

    boy_yoni = ak.YONI_BY_NAKSHATRA[boy.nakshatra]
    girl_yoni = ak.YONI_BY_NAKSHATRA[girl.nakshatra]
    score = ak.YONI_SCORE_MATRIX[_YONI_INDEX[boy_yoni]][_YONI_INDEX[girl_yoni]]

    return KootaResult(
        score=float(score),
        max_score=4,
        details={
            "boy_yoni": boy_yoni,
            "girl_yoni": girl_yoni,
            "is_same_yoni": boy_yoni == girl_yoni,
        },
        warnings=(),
    )
