"""Ashtakoot composite scorer -- P2.4.2.

Calls all 8 koota calculators (trivial.py: Varna/Vashya/Tara/Gana;
sign_lord.py: GrahaMaitri/Bhakoot; matrix.py: Yoni/Nadi) and aggregates
their results into a single AshtakootResult. No new calculation logic
lives here -- pure orchestration over the already-locked P2.4.1a/b/c
calculators; this module never touches pyswisseph or any
_ashtakoot_tables.py constant beyond the dosha-name mapping below.

AstroSage oracle lock: Sulabh x Surbhi = 27.5/36, "Preferable", no
active doshas (Nadi 8/8, Bhakoot 7/7 both clear) -- see
tests/calculations/compatibility/test_ashtakoot.py's AC-1.

Validation: no validation logic is duplicated here. compute_varna_koota
is called first in the fixed call order below, so an out-of-range
moon_sign or nakshatra on either native raises ValueError naturally from
that first call, before any other calculator runs.
"""

from agent.calculations.compatibility.koota_types import (
    AshtakootResult,
    KootaNatalInfo,
    KootaResult,
)
from agent.calculations.compatibility.matrix import (
    compute_nadi_koota,
    compute_yoni_koota,
)
from agent.calculations.compatibility.sign_lord import (
    compute_bhakoot_koota,
    compute_graha_maitri_koota,
)
from agent.calculations.compatibility.trivial import (
    compute_gana_koota,
    compute_tara_koota,
    compute_varna_koota,
    compute_vashya_koota,
)

# Interpretation bands (locked, not tunable by Claude Code).
# Source: JHora guide (18.0 minimum for "Preferable") + modern
# operational convention (12.0 lower bound for "Marginal"). Scope:
# Indian arranged-marriage screening only -- not validated as a
# universal compatibility metric or for other matching traditions.
#
# The locked spec describes three bands (>=18.0, 12.0-17.5, <12.0),
# leaving an apparent textual gap between 17.5 and 18.0. In practice
# there is no gap: every individual koota score in this system is a
# multiple of 0.5 (Varna/Yoni/Gana/Bhakoot/Nadi are plain integers;
# Vashya/Tara/GrahaMaitri's half-point tiers are themselves multiples
# of 0.5), so total_score is always a multiple of 0.5 -- no achievable
# total can ever fall strictly between 17.5 and 18.0. The descending
# >=18.0 / >=12.0 check below is therefore exactly equivalent to the
# locked band boundaries for every value this scorer can actually
# produce.
ASHTAKOOT_INTERPRETATION_THRESHOLDS: tuple[tuple[float, str], ...] = (
    (18.0, "Preferable"),
    (12.0, "Marginal — consult astrologer"),
    (0.0, "Not Preferable"),
)

# Bhakoot's three classical dosha types (P2.4.1b lock), keyed by the
# same canonical ascending tuple ak.BHAKOOT_CANCELLATION_RULES /
# sign_lord.py's dosha_type use -- not a new table, just the classical
# display name for each tuple already locked in P2.4.1b's design chat.
_BHAKOOT_DOSHA_NAME_BY_TYPE: dict[tuple[int, int], str] = {
    (2, 12): "Bhakoot_Dwirdwadash",
    (5, 9): "Bhakoot_NavPancham",
    (6, 8): "Bhakoot_Shadashtak",
}


def _interpret(total_score: float) -> str:
    for lower_bound, label in ASHTAKOOT_INTERPRETATION_THRESHOLDS:
        if total_score >= lower_bound:
            return label
    raise AssertionError(
        f"total_score {total_score} matched no threshold band -- "
        f"unreachable, the lowest band starts at 0.0"
    )


def compute_ashtakoot_compatibility(
    boy: KootaNatalInfo, girl: KootaNatalInfo
) -> AshtakootResult:
    """Run all 8 Ashtakoot koota calculators and aggregate the result.

    doshas reports only the classically-named ACTIVE, uncancelled
    doshas: "Nadi_Dosha" (V1 has no Nadi cancellation path, so this
    fires whenever Nadi scores 0) and, for Bhakoot, whichever of
    "Bhakoot_Dwirdwadash"/"Bhakoot_NavPancham"/"Bhakoot_Shadashtak"
    applies when a dosha distance was hit AND not cancelled (Bhakoot's
    own cancellation path can still clear it back to 7/7, in which case
    nothing is appended here).
    """
    varna = compute_varna_koota(boy, girl)
    vashya = compute_vashya_koota(boy, girl)
    tara = compute_tara_koota(boy, girl)
    yoni = compute_yoni_koota(boy, girl)
    maitri = compute_graha_maitri_koota(boy, girl)
    gana = compute_gana_koota(boy, girl)
    bhakoot = compute_bhakoot_koota(boy, girl)
    nadi = compute_nadi_koota(boy, girl)

    kootas: dict[str, KootaResult] = {
        "Varna": varna,
        "Vashya": vashya,
        "Tara": tara,
        "Yoni": yoni,
        "GrahaMaitri": maitri,
        "Gana": gana,
        "Bhakoot": bhakoot,
        "Nadi": nadi,
    }

    total_score = sum(r.score for r in kootas.values())

    doshas: list[str] = []
    if nadi.details["dosha"] is True:
        doshas.append("Nadi_Dosha")
    bhakoot_dosha_type = bhakoot.details["dosha_type"]
    if bhakoot_dosha_type is not None and bhakoot.score == 0:
        doshas.append(_BHAKOOT_DOSHA_NAME_BY_TYPE[bhakoot_dosha_type])

    warnings = tuple(w for r in kootas.values() for w in r.warnings)

    return AshtakootResult(
        total_score=total_score,
        max_score=36,
        kootas=kootas,
        doshas=doshas,
        interpretation=_interpret(total_score),
        warnings=warnings,
    )
