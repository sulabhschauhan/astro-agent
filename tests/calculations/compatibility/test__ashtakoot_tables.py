"""Structural invariant tests for agent/calculations/compatibility/_ashtakoot_tables.py.

P2.4.0 scope: structural invariants only (completeness, partition,
typo-guard via canonical-name import, score-weight totals). No paired-
chart fixture tests -- this phase ships constants only, no calculator.

Stop-on-fail per the implementation prompt; no test depends on another.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))  # project root

import pytest

from agent.calculations.compatibility import _ashtakoot_tables as ak
from agent.calculations.core._friendship_tables import NATURAL_FRIENDSHIP
from agent.calculations.core._panchanga_tables import NAKSHATRA_NAMES

ALL_SIGNS = set(range(12))
ALL_NAKSHATRAS = set(range(27))


def _nak(name: str) -> int:
    """Resolve a nakshatra name to its canonical 0-26 index -- typo guard
    per the prompt's 'import canonical lists, don't redefine' requirement.
    """
    return NAKSHATRA_NAMES.index(name)


# ── 1. Score weights ─────────────────────────────────────────────────────────

def test_score_weights_cover_exactly_eight_kootas():
    assert set(ak.KOOTA_SCORE_WEIGHTS.keys()) == {
        "Varna", "Vashya", "Tara", "Yoni", "GrahaMaitri", "Gana", "Bhakoot", "Nadi",
    }


def test_score_weights_sum_to_36():
    assert sum(ak.KOOTA_SCORE_WEIGHTS.values()) == 36
    assert ak.TOTAL_KOOTA_SCORE == 36


@pytest.mark.parametrize(
    "koota,expected",
    [("Varna", 1), ("Vashya", 2), ("Tara", 3), ("Yoni", 4),
     ("GrahaMaitri", 5), ("Gana", 6), ("Bhakoot", 7), ("Nadi", 8)],
)
def test_score_weights_match_muhurtha_chinthamani_p160(koota, expected):
    assert ak.KOOTA_SCORE_WEIGHTS[koota] == expected


# ── 2. Varna ──────────────────────────────────────────────────────────────────

def test_varna_by_sign_covers_all_12_signs():
    assert set(ak.VARNA_BY_SIGN.keys()) == ALL_SIGNS


def test_varna_by_sign_values_are_canonical_groups():
    for sign, group in ak.VARNA_BY_SIGN.items():
        assert group in ak.VARNA_GROUPS, f"sign {sign}: unrecognized Varna group {group!r}"


def test_varna_by_sign_partitions_into_groups_of_three():
    from collections import Counter
    counts = Counter(ak.VARNA_BY_SIGN.values())
    assert counts == {g: 3 for g in ak.VARNA_GROUPS}


def test_varna_score_is_full_cross_product_in_0_or_1():
    expected_keys = {(g, b) for g in ak.VARNA_GROUPS for b in ak.VARNA_GROUPS}
    assert set(ak.VARNA_SCORE.keys()) == expected_keys
    assert all(v in (0, 1) for v in ak.VARNA_SCORE.values())


def test_varna_score_same_varna_always_scores_1():
    for g in ak.VARNA_GROUPS:
        assert ak.VARNA_SCORE[(g, g)] == 1


# ── 3. Vashya ─────────────────────────────────────────────────────────────────

def test_vashya_whole_sign_dict_covers_exactly_ten_signs():
    assert set(ak.VASHYA_BY_SIGN.keys()) == ALL_SIGNS - {8, 9}


def test_vashya_half_sign_dict_covers_sagittarius_and_capricorn_both_halves():
    assert set(ak.VASHYA_BY_SIGN_HALF.keys()) == {(8, 0), (8, 1), (9, 0), (9, 1)}


def test_vashya_groups_partition_all_12_signs_without_overlap_or_gap():
    # Every one of the 12 signs is resolvable to exactly one Vashya group,
    # either directly (10 signs) or via (sign, half) for both halves (2 signs).
    resolved_whole = set(ak.VASHYA_BY_SIGN.keys())
    resolved_half_signs = {sign for (sign, _half) in ak.VASHYA_BY_SIGN_HALF.keys()}
    assert resolved_whole | resolved_half_signs == ALL_SIGNS
    assert resolved_whole.isdisjoint(resolved_half_signs)


def test_vashya_values_are_canonical_groups():
    for v in ak.VASHYA_BY_SIGN.values():
        assert v in ak.VASHYA_GROUPS
    for v in ak.VASHYA_BY_SIGN_HALF.values():
        assert v in ak.VASHYA_GROUPS


def test_vashya_score_is_full_cross_product_in_0_to_2():
    expected_keys = {(a, b) for a in ak.VASHYA_GROUPS for b in ak.VASHYA_GROUPS}
    assert set(ak.VASHYA_SCORE.keys()) == expected_keys
    assert all(0 <= v <= 2 for v in ak.VASHYA_SCORE.values())


def test_vashya_score_same_group_always_scores_max():
    for g in ak.VASHYA_GROUPS:
        assert ak.VASHYA_SCORE[(g, g)] == 2


def test_vashya_score_is_directional_not_forced_symmetric():
    # Vashya measures control/dominance -- the matrix is asymmetric by
    # classical design (Manava-Vanachara=0 but Vanachara-Manava=0 happens
    # to match here; assert the matrix is NOT silently auto-symmetrized by
    # checking a known-asymmetric pair from the source table survives).
    assert ak.VASHYA_SCORE[("Chatushpada", "Vanachara")] == 1.5
    assert ak.VASHYA_SCORE[("Vanachara", "Chatushpada")] == 0
    assert ak.VASHYA_SCORE[("Chatushpada", "Vanachara")] != ak.VASHYA_SCORE[("Vanachara", "Chatushpada")]


# ── 4. Tara ───────────────────────────────────────────────────────────────────

def test_tara_remainder_category_covers_all_nine_remainders():
    assert set(ak.TARA_REMAINDER_CATEGORY.keys()) == set(range(9))


def test_tara_remainder_category_matches_classical_inauspicious_set():
    inauspicious = {r for r, cat in ak.TARA_REMAINDER_CATEGORY.items() if cat == "INAUSPICIOUS"}
    assert inauspicious == {3, 5, 7}


def test_tara_score_is_full_cross_product():
    expected_keys = {(a, b) for a in ("AUSPICIOUS", "INAUSPICIOUS") for b in ("AUSPICIOUS", "INAUSPICIOUS")}
    assert set(ak.TARA_SCORE.keys()) == expected_keys


def test_tara_score_values_match_classical_max_and_zero():
    assert ak.TARA_SCORE[("AUSPICIOUS", "AUSPICIOUS")] == 3.0
    assert ak.TARA_SCORE[("INAUSPICIOUS", "INAUSPICIOUS")] == 0.0
    assert ak.TARA_SCORE[("AUSPICIOUS", "INAUSPICIOUS")] == ak.TARA_SCORE[("INAUSPICIOUS", "AUSPICIOUS")] == 1.5


# ── 5. Yoni ───────────────────────────────────────────────────────────────────

def test_yoni_by_nakshatra_covers_all_27_nakshatras():
    assert set(ak.YONI_BY_NAKSHATRA.keys()) == ALL_NAKSHATRAS


def test_yoni_animal_list_closed_under_fourteen_canonical_yonis():
    assert len(ak.YONI_ANIMALS) == 14
    assert len(set(ak.YONI_ANIMALS)) == 14, "duplicate animal name in YONI_ANIMALS"
    assert set(ak.YONI_BY_NAKSHATRA.values()) <= set(ak.YONI_ANIMALS)


def test_yoni_every_animal_used_at_least_once():
    assert set(ak.YONI_BY_NAKSHATRA.values()) == set(ak.YONI_ANIMALS)


@pytest.mark.parametrize(
    "name_a,name_b,expected_animal",
    [
        ("Ashwini", "Shatabhisha", "Ashwa"),
        ("Swati", "Hasta", "Mahisha"),
        ("Dhanishtha", "Purva Bhadrapada", "Simha"),
        ("Bharani", "Revati", "Gaja"),
        ("Pushya", "Krittika", "Mesha"),
        ("Shravana", "Purva Ashadha", "Vanara"),
        ("Mrigashira", "Rohini", "Sarpa"),
        ("Jyeshtha", "Anuradha", "Mriga"),
        ("Mula", "Ardra", "Shwana"),
        ("Punarvasu", "Ashlesha", "Marjara"),
        ("Magha", "Purva Phalguni", "Mushaka"),
        ("Vishakha", "Chitra", "Vyaghra"),
        ("Uttara Phalguni", "Uttara Bhadrapada", "Gow"),
    ],
)
def test_yoni_by_nakshatra_matches_muhurtha_chinthamani_p167_pairs(name_a, name_b, expected_animal):
    # Typo guard: resolves names via NAKSHATRA_NAMES (canonical list), not
    # hand-coded indices, per the prompt's import-don't-redefine requirement.
    assert ak.YONI_BY_NAKSHATRA[_nak(name_a)] == expected_animal
    assert ak.YONI_BY_NAKSHATRA[_nak(name_b)] == expected_animal


def test_yoni_uttara_ashadha_alone_is_nakula_abhijit_folded_in():
    assert ak.YONI_BY_NAKSHATRA[_nak("Uttara Ashadha")] == "Nakula"


def test_yoni_score_matrix_is_14x14():
    assert len(ak.YONI_SCORE_MATRIX) == 14
    assert all(len(row) == 14 for row in ak.YONI_SCORE_MATRIX)


def test_yoni_score_matrix_values_in_0_to_4():
    for row in ak.YONI_SCORE_MATRIX:
        assert all(0 <= v <= 4 for v in row)


def test_yoni_score_matrix_diagonal_is_all_four_same_yoni_max():
    for i in range(14):
        assert ak.YONI_SCORE_MATRIX[i][i] == 4


def test_yoni_score_matrix_is_symmetric():
    for i in range(14):
        for j in range(14):
            assert ak.YONI_SCORE_MATRIX[i][j] == ak.YONI_SCORE_MATRIX[j][i], (
                f"YONI_SCORE_MATRIX not symmetric at ({i},{j})"
            )


def test_yoni_mahabair_pairs_score_exactly_zero_in_matrix():
    index_of = {animal: i for i, animal in enumerate(ak.YONI_ANIMALS)}
    assert len(ak.YONI_MAHABAIR_PAIRS) == 7
    for pair in ak.YONI_MAHABAIR_PAIRS:
        a, b = tuple(pair)
        assert ak.YONI_SCORE_MATRIX[index_of[a]][index_of[b]] == 0, (
            f"Mahabair pair {pair} does not score 0 in YONI_SCORE_MATRIX"
        )


# ── 6. Graha Maitri ───────────────────────────────────────────────────────────

def test_ashtakoot_tables_reuses_natural_friendship_not_a_duplicate():
    # Correction 2: import via `is`, not value-equality -- proves there is
    # no local re-transcription drifting from core/_friendship_tables.py.
    assert ak.NATURAL_FRIENDSHIP is NATURAL_FRIENDSHIP


def test_natural_friendship_asymmetry_is_preserved_through_the_reuse():
    # Spot-check one of the 11 known-asymmetric pairs survives the import
    # unchanged (Moon counts Mercury a friend; Mercury counts Moon an enemy).
    assert "Mercury" in NATURAL_FRIENDSHIP["Moon"]["friends"]
    assert "Moon" in NATURAL_FRIENDSHIP["Mercury"]["enemies"]


def test_graha_maitri_score_covers_all_nine_relation_combinations():
    relations = ("Friend", "Neutral", "Enemy")
    expected_keys = {(a, b) for a in relations for b in relations}
    assert set(ak.GRAHA_MAITRI_SCORE.keys()) == expected_keys


def test_graha_maitri_score_values_in_0_to_5():
    assert all(0 <= v <= 5 for v in ak.GRAHA_MAITRI_SCORE.values())


def test_graha_maitri_score_friend_friend_is_max():
    assert ak.GRAHA_MAITRI_SCORE[("Friend", "Friend")] == 5


def test_graha_maitri_score_enemy_enemy_is_zero():
    assert ak.GRAHA_MAITRI_SCORE[("Enemy", "Enemy")] == 0


def test_sign_lord_covers_all_12_signs_with_only_classical_planets():
    assert set(ak.SIGN_LORD.keys()) == ALL_SIGNS
    classical_planets = set(NATURAL_FRIENDSHIP.keys())
    assert set(ak.SIGN_LORD.values()) <= classical_planets, (
        "SIGN_LORD must never resolve to Rahu/Ketu -- no rashi is classically node-lorded"
    )


# ── 7. Gana ───────────────────────────────────────────────────────────────────

def test_gana_by_nakshatra_covers_all_27_nakshatras():
    assert set(ak.GANA_BY_NAKSHATRA.keys()) == ALL_NAKSHATRAS


def test_gana_partitions_into_exactly_three_groups_of_nine():
    from collections import Counter
    counts = Counter(ak.GANA_BY_NAKSHATRA.values())
    assert counts == {g: 9 for g in ak.GANA_GROUPS}


def test_gana_score_same_gana_always_scores_max():
    for g in ak.GANA_GROUPS:
        assert ak.GANA_SCORE[(g, g)] == 6


def test_gana_score_manushya_rakshasa_is_worse_than_deva_manushya():
    assert ak.GANA_SCORE[("Manushya", "Rakshasa")] < ak.GANA_SCORE[("Deva", "Manushya")]


def test_gana_score_deva_rakshasa_is_zero():
    assert ak.GANA_SCORE[("Deva", "Rakshasa")] == 0
    assert ak.GANA_SCORE[("Rakshasa", "Deva")] == 0


# ── 8. Bhakoot ────────────────────────────────────────────────────────────────

def test_bhakoot_score_by_distance_covers_all_twelve_house_counts():
    assert set(ak.BHAKOOT_SCORE_BY_DISTANCE.keys()) == set(range(1, 13))


def test_bhakoot_inauspicious_distances_match_classical_citation():
    inauspicious = {d for d, s in ak.BHAKOOT_SCORE_BY_DISTANCE.items() if s == 0}
    assert inauspicious == {2, 5, 6, 8, 9, 12}


def test_bhakoot_auspicious_distances_score_the_max():
    auspicious = {d for d, s in ak.BHAKOOT_SCORE_BY_DISTANCE.items() if s != 0}
    assert auspicious == {1, 3, 4, 7, 10, 11}
    for d in auspicious:
        assert ak.BHAKOOT_SCORE_BY_DISTANCE[d] == 7


def test_bhakoot_distance_effect_names_match_classical_citation():
    assert ak.BHAKOOT_DISTANCE_EFFECT[6] == ak.BHAKOOT_DISTANCE_EFFECT[8] == "death"
    assert ak.BHAKOOT_DISTANCE_EFFECT[5] == ak.BHAKOOT_DISTANCE_EFFECT[9] == "loss_of_progeny"
    assert ak.BHAKOOT_DISTANCE_EFFECT[2] == ak.BHAKOOT_DISTANCE_EFFECT[12] == "poverty"


def test_bhakoot_cancellation_rules_all_three_locked():
    assert ak.BHAKOOT_CANCELLATION_RULES[(2, 12)] == "same_lord_or_friend_lords"
    assert ak.BHAKOOT_CANCELLATION_RULES[(5, 9)] == "same_lord_or_friend_lords"
    assert ak.BHAKOOT_CANCELLATION_RULES[(6, 8)] == "same_lord_or_friend_lords"


def test_bhakoot_cancellation_rules_dict_is_complete():
    assert set(ak.BHAKOOT_CANCELLATION_RULES.keys()) == {(2, 12), (5, 9), (6, 8)}
    assert all(v is not None for v in ak.BHAKOOT_CANCELLATION_RULES.values())


# ── 9. Nadi ───────────────────────────────────────────────────────────────────

def test_nadi_by_nakshatra_covers_all_27_nakshatras():
    assert set(ak.NADI_BY_NAKSHATRA.keys()) == ALL_NAKSHATRAS


def test_nadi_partitions_into_exactly_three_groups_of_nine():
    from collections import Counter
    counts = Counter(ak.NADI_BY_NAKSHATRA.values())
    assert counts == {g: 9 for g in ak.NADI_GROUPS}


def test_nadi_score_same_nadi_is_zero_different_nadi_is_max():
    for g in ak.NADI_GROUPS:
        assert ak.NADI_SCORE[(g, g)] == 0
    for a in ak.NADI_GROUPS:
        for b in ak.NADI_GROUPS:
            if a != b:
                assert ak.NADI_SCORE[(a, b)] == 8


def test_nadi_cancellation_rule_is_locked():
    assert ak.NADI_CANCELLATION_RULE == "same_sign_different_pada"


@pytest.mark.parametrize(
    "name_a,name_b",
    [
        ("Ashwini", "Ardra"), ("Punarvasu", "Uttara Phalguni"), ("Hasta", "Jyeshtha"),
        ("Mula", "Shatabhisha"), ("Purva Bhadrapada", "Ashwini"), ("Mrigashira", "Pushya"),
        ("Purva Phalguni", "Chitra"), ("Anuradha", "Purva Ashadha"), ("Dhanishtha", "Uttara Bhadrapada"),
        ("Krittika", "Rohini"), ("Ashlesha", "Magha"), ("Swati", "Vishakha"),
    ],
)
def test_nadi_pairs_within_same_group_match_muhurtha_chinthamani_p177(name_a, name_b):
    assert ak.NADI_BY_NAKSHATRA[_nak(name_a)] == ak.NADI_BY_NAKSHATRA[_nak(name_b)]
