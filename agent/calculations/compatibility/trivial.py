"""Trivial-arithmetic Ashtakoot koota calculators -- P2.4.1a.

Implements the four lowest-arithmetic koota calculators: Varna, Vashya,
Tara, Gana. Each takes (boy: KootaNatalInfo, girl: KootaNatalInfo) and
returns a KootaResult (agent.calculations.compatibility.koota_types).
Reads only from agent.calculations.compatibility._ashtakoot_tables, which
is READ-ONLY in this phase (P2.4.1a dependency-discipline lock) -- no new
constants were needed; all four calculators were fully servable by the
P2.4.0 tables as shipped.

TARA ALGORITHM -- locked at the P2.4.1a research gate, with citations:

1. Counting convention: inclusive count from one native's nakshatra to the
   other's. count = ((to_nak - from_nak) % 27) + 1, range 1-27 (same-
   nakshatra -> count=1). Source: Muhurtha-Chinthamani p.166 ("Counting is
   to be done from the Nakshtra of the girl to that of the boy, and then
   ... from the Nakshtra of the boy to that of the girl"). Independently
   corroborated by a third-party worked example (jagannathhora.com, Tara
   Koot article): Ashwini(1st) to Punarvasu(7th) -> count=7 -> remainder 7
   -> Vadha -- reproduces exactly under this same formula (0-indexed:
   ((6-0)%27)+1=7).
2. Favorable set: remainder = count % 9, in {1,2,4,6,8,0} = AUSPICIOUS,
   in {3,5,7} = INAUSPICIOUS (Vipat/Pratyari/Vadha tara positions).
   Source: same citation. Already locked as
   _ashtakoot_tables.TARA_REMAINDER_CATEGORY -- no new constant needed.
3. Per-direction scoring: both directions auspicious -> 3 (max); one
   auspicious one inauspicious -> 1.5; both inauspicious -> 0. Already
   locked as _ashtakoot_tables.TARA_SCORE.

Acceptance test (per the research gate): for the real Sulabh (nakshatra
15=Vishakha) x Surbhi (nakshatra 23=Shatabhisha) pair -- both independently
ephemeris-computed and cross-validated against 3 other unrelated koota
classifications in the same AstroSage fixture (Gana, Nadi, Yoni, Bhakoot
all converge on these exact nakshatra/sign values) -- this formula gives
boy->girl count=9 (remainder 0, AUSPICIOUS) and girl->boy count=20
(remainder 2, AUSPICIOUS), both auspicious, reproducing AstroSage's
reported 3/3 exactly.

KNOWN, SURFACED, NON-BLOCKING DISCREPANCY: AstroSage's report displays
this pair's Tara row as "Boy: Janma, Girl: Vipat" (named tara positions).
The formula above does not reproduce those specific NAMES for this pair --
it computes Sampat (tara-number 2) and Ati-mitra (tara-number 9), not
Janma/Vipat. Both of those ARE auspicious too (as are Janma/Sampat/Kshema/
Sadhaka/Mitra/Ati-mitra generally), so the SCORE still matches (3/3)
either way, but the specific display-label mapping AstroSage uses for the
two directions was not reconciled despite testing multiple counting-
convention variants (1-indexed vs 0-indexed, with/without the inclusive
+1) and sanity-checking the geocoded birth coordinates against
tests/fixtures/geocoded_locations.json (negligible, sub-arcminute
differences -- not the cause). _ashtakoot_tables.py has no tara-NAME
table at all (only AUSPICIOUS/INAUSPICIOUS categories), so this
calculator's KootaResult.details reports the actually-computed counts and
categories, never a fabricated tara-name label.

STRUCTURAL NOTE on Tara's symmetry (surfaced and resolved with Sulabh):
TARA_SCORE is value-symmetric -- TARA_SCORE[(x,y)] == TARA_SCORE[(y,x)]
for every (x,y) in {AUSPICIOUS, INAUSPICIOUS}^2. This means
compute_tara_koota(A, B).score == compute_tara_koota(B, A).score ALWAYS,
for any A/B, even though the two per-direction counts/categories
genuinely differ. Tara's "asymmetric calculator" character lives in its
per-direction intermediates (KootaResult.details), not in the final
score -- see test_trivial.py's symmetry-contract tests for Tara.
"""

from agent.calculations.compatibility import _ashtakoot_tables as ak
from agent.calculations.compatibility.koota_types import KootaNatalInfo, KootaResult


def _validate_natal_info(info: KootaNatalInfo, label: str) -> None:
    if not (0 <= info.moon_sign <= 11):
        raise ValueError(f"{label}.moon_sign must be 0..11, got {info.moon_sign}")
    if not (0 <= info.nakshatra <= 26):
        raise ValueError(f"{label}.nakshatra must be 0..26, got {info.nakshatra}")
    if not (0.0 <= info.moon_longitude < 360.0):
        raise ValueError(
            f"{label}.moon_longitude must be in [0, 360), got {info.moon_longitude}"
        )


def compute_varna_koota(boy: KootaNatalInfo, girl: KootaNatalInfo) -> KootaResult:
    """Varna Koota (max 1). Classical patriarchal scoring: boy_varna_rank
    >= girl_varna_rank scores 1, else 0 -- directly the (boy_varna,
    girl_varna) lookup in ak.VARNA_SCORE (see its module-section docstring
    for the hierarchy and citation). Asymmetric: swapping boy/girl can
    change the score.
    """
    _validate_natal_info(boy, "boy")
    _validate_natal_info(girl, "girl")

    boy_varna = ak.VARNA_BY_SIGN[boy.moon_sign]
    girl_varna = ak.VARNA_BY_SIGN[girl.moon_sign]
    score = ak.VARNA_SCORE[(boy_varna, girl_varna)]

    return KootaResult(
        score=float(score),
        max_score=ak.KOOTA_SCORE_WEIGHTS["Varna"],
        details={"boy_varna": boy_varna, "girl_varna": girl_varna},
        warnings=(),
    )


def _vashya_group(info: KootaNatalInfo) -> str:
    """Resolve a native's Vashya group, routing Sagittarius/Capricorn
    (signs 8, 9) through the half-sign table per the P2.4.0 lock. Boundary
    convention: degree-in-sign in [0, 15) -> half 0; [15, 30) -> half 1
    (inclusive lower / exclusive upper, matching this project's general
    range convention -- e.g. panchaka.py's [300, 360) -- and PyJHora's own
    pada-floor arithmetic: pada = floor(degree_in_sign / 7.5) + 1, which
    puts exactly 15.0 deg at pada 3, i.e. half 1). This precise boundary
    side was not pinned down numerically in P2.4.0's docstring text itself
    (a data-only module has no comparison logic to pin it with); applying
    the project's own established inclusive-lower/exclusive-upper
    convention here rather than treating it as a fresh ambiguity.
    """
    sign = info.moon_sign
    if sign in (8, 9):
        degree_in_sign = info.moon_longitude % 30.0
        half = 0 if degree_in_sign < 15.0 else 1
        return ak.VASHYA_BY_SIGN_HALF[(sign, half)]
    return ak.VASHYA_BY_SIGN[sign]


def compute_vashya_koota(boy: KootaNatalInfo, girl: KootaNatalInfo) -> KootaResult:
    """Vashya Koota (max 2). Directional lookup in ak.VASHYA_SCORE, keyed
    (bride_group, groom_group) per that table's own citation -- bride=girl,
    groom=boy. Asymmetric: swapping boy/girl can change the score (Vashya
    measures mutual control/dominance, not a symmetric compatibility).
    """
    _validate_natal_info(boy, "boy")
    _validate_natal_info(girl, "girl")

    boy_group = _vashya_group(boy)
    girl_group = _vashya_group(girl)
    score = ak.VASHYA_SCORE[(girl_group, boy_group)]

    return KootaResult(
        score=float(score),
        max_score=ak.KOOTA_SCORE_WEIGHTS["Vashya"],
        details={"boy_vashya_group": boy_group, "girl_vashya_group": girl_group},
        warnings=(),
    )


def _tara_count_and_category(from_nak: int, to_nak: int) -> tuple[int, str]:
    count = ((to_nak - from_nak) % 27) + 1
    remainder = count % 9
    return count, ak.TARA_REMAINDER_CATEGORY[remainder]


def compute_tara_koota(boy: KootaNatalInfo, girl: KootaNatalInfo) -> KootaResult:
    """Tara Koota (max 3). See module docstring for the locked algorithm,
    citations, and the surfaced score-symmetry structural note. Computes
    both directional counts/categories (genuinely direction-dependent
    intermediates) and combines them via ak.TARA_SCORE, keyed
    (girl_to_boy_category, boy_to_girl_category) per that table's own
    citation -- value-symmetric by construction, so the final SCORE is
    swap-invariant even though the intermediates are not.
    """
    _validate_natal_info(boy, "boy")
    _validate_natal_info(girl, "girl")

    boy_to_girl_count, boy_to_girl_category = _tara_count_and_category(
        boy.nakshatra, girl.nakshatra
    )
    girl_to_boy_count, girl_to_boy_category = _tara_count_and_category(
        girl.nakshatra, boy.nakshatra
    )
    score = ak.TARA_SCORE[(girl_to_boy_category, boy_to_girl_category)]

    return KootaResult(
        score=float(score),
        max_score=ak.KOOTA_SCORE_WEIGHTS["Tara"],
        details={
            "boy_to_girl_count": boy_to_girl_count,
            "boy_to_girl_category": boy_to_girl_category,
            "girl_to_boy_count": girl_to_boy_count,
            "girl_to_boy_category": girl_to_boy_category,
        },
        warnings=(),
    )


def compute_gana_koota(boy: KootaNatalInfo, girl: KootaNatalInfo) -> KootaResult:
    """Gana Koota (max 6). Symmetric lookup in ak.GANA_SCORE -- swapping
    boy/girl never changes the score (see that table's own citation note
    on the classical source's qualitative-only cross-gana ordering).
    """
    _validate_natal_info(boy, "boy")
    _validate_natal_info(girl, "girl")

    boy_gana = ak.GANA_BY_NAKSHATRA[boy.nakshatra]
    girl_gana = ak.GANA_BY_NAKSHATRA[girl.nakshatra]
    score = ak.GANA_SCORE[(boy_gana, girl_gana)]

    return KootaResult(
        score=float(score),
        max_score=ak.KOOTA_SCORE_WEIGHTS["Gana"],
        details={"boy_gana": boy_gana, "girl_gana": girl_gana},
        warnings=(),
    )
