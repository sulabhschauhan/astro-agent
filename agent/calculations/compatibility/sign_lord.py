"""Sign-lord-routed Ashtakoot koota calculators -- P2.4.1b.

Implements the two koota calculators whose classical rule is keyed off each
native's Janma Rashi (Moon-sign) LORD rather than the sign/nakshatra value
directly: Graha Maitri (planetary friendship between the two Moon-sign
lords) and Bhakoot (sign-distance dosha, with a same-lord/friend-lords
cancellation path). Cross-koota helpers shared by both -- sign-lord
routing (_sign_lords) and sign-distance arithmetic (_bhakoot_distances) --
live in this module per the P2.4.1 design lock, alongside the STRICT
mutual-friendship helper (_relation) both calculators' cancellation/scoring
paths depend on.

Each public function takes (boy: KootaNatalInfo, girl: KootaNatalInfo) and
returns a KootaResult (agent.calculations.compatibility.koota_types). Reads
only from agent.calculations.compatibility._ashtakoot_tables and
agent.calculations.core._friendship_tables, both READ-ONLY in this phase
(P2.4.1b dependency-discipline lock) -- no new constants were needed.

GRAHA MAITRI -- same-lord short-circuit (locked, P2.4.1b design chat):
GRAHA_MAITRI_SCORE has no "same lord" cell by design (per its own
module-section docstring in _ashtakoot_tables.py) -- "same lord" is a
distinct classical case from a friendship-relation lookup, not a 4th
relation value. compute_graha_maitri_koota() handles it explicitly: same
lord -> max score (5), never consulting GRAHA_MAITRI_SCORE for that case.

GRAHA MAITRI -- score swap-invariance (structural note, same pattern as
trivial.py's Tara note): GRAHA_MAITRI_SCORE is fully value-symmetric --
GRAHA_MAITRI_SCORE[(x,y)] == GRAHA_MAITRI_SCORE[(y,x)] for all 9
(x,y) in {Friend,Neutral,Enemy}^2 (5/4/4/3/1/1/0.5/0.5/0 -- every
off-diagonal pair matches its mirror). Swapping boy/girl swaps which lord
plays "boy_relation_to_girl_lord" vs "girl_relation_to_boy_lord" (the two
intermediates cross-swap value-for-value -- genuinely direction-aware), but
because the score table is symmetric under that swap, the final SCORE is
provably swap-invariant for ANY pair, not just the specific test pairs.

BHAKOOT -- directional distance choice is immaterial (locked in the
P2.4.1b implementation prompt, proven here): for any two distinct signs,
d_boy_to_girl + d_girl_to_boy == 14 (k+1 and 13-k for k=(girl-boy)%12,
k in 1..11), and BHAKOOT_SCORE_BY_DISTANCE[d] == BHAKOOT_SCORE_BY_DISTANCE
[14-d] holds for every d in 1..12 in the locked table -- not just the
three dosha pairs {2,12}/{5,9}/{6,8}, but every complementary pair
(3,11) and (4,10) too. base_score is therefore swap-invariant by table
construction for any input, mirroring Tara's score-symmetry proof in
trivial.py.

BHAKOOT -- dosha-type identification reuses BHAKOOT_DISTANCE_EFFECT rather
than re-encoding the {2,12}/{5,9}/{6,8} membership separately: the
qualitative effect name ("poverty"/"loss_of_progeny"/"death") already
locked in _ashtakoot_tables.py is a 1:1 proxy for the dosha-type tuple, so
_DOSHA_TYPE_BY_EFFECT below is a pure re-keying of an existing locked
table, not a new classical claim.

BHAKOOT -- cancellation-failure-reason classification (NOT individually
locked by the design chat beyond the two named test cases BK-5/BK-6; this
module's own design choice, surfaced rather than silently picked): once
same-lord and STRICT friend-lords both fail, the two per-direction
relations are classified into exactly one of three buckets --
"mutual_enemies" (both directions Enemy), "asymmetric_friendship_fails_strict"
(one direction Friend, the other Neutral or Enemy -- STRICT needed BOTH),
or "neither_lord_counts_the_other_a_friend" (the remaining Neutral/Neutral
or Neutral/Enemy combinations, where Friend never appears in either
direction so "asymmetric" would mischaracterize it). Only the first two
buckets are exercised by the locked BK-5/BK-6 fixtures; the third exists
for completeness over the full relation space (see
test_bhakoot_koota_structural_invariant_full_sign_space).
"""

from agent.calculations.compatibility import _ashtakoot_tables as ak
from agent.calculations.compatibility.koota_types import KootaNatalInfo, KootaResult
from agent.calculations.core._friendship_tables import NATURAL_FRIENDSHIP

_DOSHA_TYPE_BY_EFFECT: dict[str, tuple[int, int]] = {
    "poverty": (2, 12),
    "loss_of_progeny": (5, 9),
    "death": (6, 8),
}


def _validate_moon_sign(info: KootaNatalInfo, label: str) -> None:
    if not (0 <= info.moon_sign <= 11):
        raise ValueError(f"{label}.moon_sign must be 0..11, got {info.moon_sign}")


def _sign_lords(boy: KootaNatalInfo, girl: KootaNatalInfo) -> tuple[str, str]:
    """Sign-lord routing, shared by both calculators in this module."""
    return ak.SIGN_LORD[boy.moon_sign], ak.SIGN_LORD[girl.moon_sign]


def _bhakoot_distances(boy_sign: int, girl_sign: int) -> tuple[int, int]:
    """Sign-distance arithmetic, shared module helper (Bhakoot-only today,
    kept alongside _sign_lords per the docstring's cross-koota-helper note).
    """
    d_boy_to_girl = ((girl_sign - boy_sign) % 12) + 1
    d_girl_to_boy = ((boy_sign - girl_sign) % 12) + 1
    return d_boy_to_girl, d_girl_to_boy


def _relation(actor: str, target: str) -> str:
    """actor's natural (sthira) relation to target -- "Friend"/"Neutral"/
    "Enemy", read directly off the raw NATURAL_FRIENDSHIP table (asymmetric
    by design; actor!=target always holds at both call sites in this
    module, since same-lord is checked separately before either calculator
    ever calls this).
    """
    entry = NATURAL_FRIENDSHIP[actor]
    if target in entry["friends"]:
        return "Friend"
    if target in entry["neutral"]:
        return "Neutral"
    return "Enemy"  # target in entry["enemies"]


def compute_graha_maitri_koota(boy: KootaNatalInfo, girl: KootaNatalInfo) -> KootaResult:
    """Graha Maitri Koota (max 5). Same-lord short-circuits to the max
    score (5); otherwise looks up the two lords' mutual natural-friendship
    relation in ak.GRAHA_MAITRI_SCORE, keyed (boy_relation_to_girl_lord,
    girl_relation_to_boy_lord). See module docstring for the same-lord
    rationale and the score's swap-invariance proof.
    """
    _validate_moon_sign(boy, "boy")
    _validate_moon_sign(girl, "girl")

    boy_lord, girl_lord = _sign_lords(boy, girl)

    if boy_lord == girl_lord:
        return KootaResult(
            score=5.0,
            max_score=ak.KOOTA_SCORE_WEIGHTS["GrahaMaitri"],
            details={
                "boy_moon_sign_lord": boy_lord,
                "girl_moon_sign_lord": girl_lord,
                "boy_relation_to_girl_lord": "same_lord_short_circuit",
                "girl_relation_to_boy_lord": "same_lord_short_circuit",
                "shortcut": "same_lord",
            },
            warnings=(),
        )

    boy_relation_to_girl_lord = _relation(boy_lord, girl_lord)
    girl_relation_to_boy_lord = _relation(girl_lord, boy_lord)
    score = ak.GRAHA_MAITRI_SCORE[(boy_relation_to_girl_lord, girl_relation_to_boy_lord)]

    return KootaResult(
        score=float(score),
        max_score=ak.KOOTA_SCORE_WEIGHTS["GrahaMaitri"],
        details={
            "boy_moon_sign_lord": boy_lord,
            "girl_moon_sign_lord": girl_lord,
            "boy_relation_to_girl_lord": boy_relation_to_girl_lord,
            "girl_relation_to_boy_lord": girl_relation_to_boy_lord,
        },
        warnings=(),
    )


def _bhakoot_cancellation_failure_reason(boy_relation: str, girl_relation: str) -> str:
    """Classify why neither cancellation path fired, once same-lord and
    STRICT friend-lords have both already failed. See module docstring for
    the three-bucket rationale (only the first two are locked-test-covered).
    """
    if boy_relation == "Enemy" and girl_relation == "Enemy":
        return "mutual_enemies"
    if "Friend" in (boy_relation, girl_relation):
        return "asymmetric_friendship_fails_strict"
    return "neither_lord_counts_the_other_a_friend"


def compute_bhakoot_koota(boy: KootaNatalInfo, girl: KootaNatalInfo) -> KootaResult:
    """Bhakoot Koota (max 7). Distance-keyed dosha lookup in
    ak.BHAKOOT_SCORE_BY_DISTANCE; on a dosha distance, applies the locked
    same-lord-or-STRICT-mutual-friend-lords cancellation rule from
    ak.BHAKOOT_CANCELLATION_RULES (currently identical across all three
    dosha types -- see _ashtakoot_tables.py's Bhakoot section comment
    block for the full citation and the STRICT-mutual definition). See
    module docstring for the directional-choice-is-immaterial proof and
    the dosha-type-via-BHAKOOT_DISTANCE_EFFECT re-keying.
    """
    _validate_moon_sign(boy, "boy")
    _validate_moon_sign(girl, "girl")

    boy_lord, girl_lord = _sign_lords(boy, girl)
    d_boy_to_girl, d_girl_to_boy = _bhakoot_distances(boy.moon_sign, girl.moon_sign)
    base_score = ak.BHAKOOT_SCORE_BY_DISTANCE[d_boy_to_girl]

    if base_score == 7:
        return KootaResult(
            score=7.0,
            max_score=ak.KOOTA_SCORE_WEIGHTS["Bhakoot"],
            details={
                "boy_moon_sign_lord": boy_lord,
                "girl_moon_sign_lord": girl_lord,
                "distance_boy_to_girl": d_boy_to_girl,
                "distance_girl_to_boy": d_girl_to_boy,
                "dosha_type": None,
                "cancellation": None,
                "auspicious_distance_pair": (d_boy_to_girl, d_girl_to_boy),
            },
            warnings=(),
        )

    # base_score == 0: dosha distance. BHAKOOT_CANCELLATION_RULES is keyed
    # by the canonical ascending dosha-type tuple, not the directional
    # distance -- recover it via the already-locked qualitative effect
    # name rather than re-deriving {2,12}/{5,9}/{6,8} membership.
    effect = ak.BHAKOOT_DISTANCE_EFFECT[d_boy_to_girl]
    dosha_type = _DOSHA_TYPE_BY_EFFECT[effect]
    assert ak.BHAKOOT_CANCELLATION_RULES[dosha_type] == "same_lord_or_friend_lords", (
        f"BHAKOOT_CANCELLATION_RULES[{dosha_type}] is not the expected rule -- "
        f"_ashtakoot_tables.py changed underneath this calculator; STOP, do not "
        f"silently proceed with a different rule."
    )

    if boy_lord == girl_lord:
        return KootaResult(
            score=7.0,
            max_score=ak.KOOTA_SCORE_WEIGHTS["Bhakoot"],
            details={
                "boy_moon_sign_lord": boy_lord,
                "girl_moon_sign_lord": girl_lord,
                "distance_boy_to_girl": d_boy_to_girl,
                "distance_girl_to_boy": d_girl_to_boy,
                "dosha_type": dosha_type,
                "cancellation": "same_lord",
            },
            warnings=(),
        )

    boy_relation_to_girl_lord = _relation(boy_lord, girl_lord)
    girl_relation_to_boy_lord = _relation(girl_lord, boy_lord)
    cancelled_by_friends = (
        boy_relation_to_girl_lord == "Friend" and girl_relation_to_boy_lord == "Friend"
    )

    if cancelled_by_friends:
        return KootaResult(
            score=7.0,
            max_score=ak.KOOTA_SCORE_WEIGHTS["Bhakoot"],
            details={
                "boy_moon_sign_lord": boy_lord,
                "girl_moon_sign_lord": girl_lord,
                "distance_boy_to_girl": d_boy_to_girl,
                "distance_girl_to_boy": d_girl_to_boy,
                "dosha_type": dosha_type,
                "cancellation": "friend_lords_strict",
                "boy_relation_to_girl_lord": boy_relation_to_girl_lord,
                "girl_relation_to_boy_lord": girl_relation_to_boy_lord,
            },
            warnings=(),
        )

    reason = _bhakoot_cancellation_failure_reason(
        boy_relation_to_girl_lord, girl_relation_to_boy_lord
    )
    return KootaResult(
        score=0.0,
        max_score=ak.KOOTA_SCORE_WEIGHTS["Bhakoot"],
        details={
            "boy_moon_sign_lord": boy_lord,
            "girl_moon_sign_lord": girl_lord,
            "distance_boy_to_girl": d_boy_to_girl,
            "distance_girl_to_boy": d_girl_to_boy,
            "dosha_type": dosha_type,
            "cancellation": None,
            "cancellation_failure_reason": reason,
            "boy_relation_to_girl_lord": boy_relation_to_girl_lord,
            "girl_relation_to_boy_lord": girl_relation_to_boy_lord,
        },
        warnings=(),
    )
