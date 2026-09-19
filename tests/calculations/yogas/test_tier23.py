"""BPHS ch19 (longevity), ch15 (home and conveyances), ch24 (the bhava-lord
table, selected), ch35 (Naabhasa) and ch37/ch38 (lunar and solar yogas).

HARDEST CASE FIRST (Working Style #3): every rule gets a chart built to FIRE
it. The Naabhasa aakriti rules in particular say "ALL the planets", so each of
those charts places all seven grahas explicitly -- a fixture that leaves grahas
on a filler sign would make every one of them unfireable, which is exactly the
`_GRAHAS`/nodes defect S137 caught the last time.

Facts are synthetic (P-027: nothing is read from an oracle file).
"""
from __future__ import annotations

import re

import pytest

from agent.calculations.yogas import rules as R
from tests.calculations.yogas.test_dhana_daridra import _SIGNS, facts, fired

_ALL7 = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn")


def run(f):
    return R._detect_tier23(f)


def row(rows, rid):
    for r in rows:
        if r["id"] == rid:
            return r
    raise AssertionError(f"no row {rid!r} in {[r['id'] for r in rows]}")


def with_dignity(f, graha, dignity):
    f["planet_positions"][graha]["dignity"] = dignity
    return f


def with_navamsa(f, pairs):
    f["navamsa"] = {"placements": {g: {"sign": s} for g, s in pairs.items()}}
    return f


def with_aspects_by(f, mapping):
    f["aspects"]["aspects_by_planet"] = mapping
    return f


def spread(asc: str, houses: dict[str, int]):
    """Place every graha by HOUSE number rather than by sign.

    The Naabhasa family is defined over houses from the ascendant, and stating
    those charts as sign literals invites an off-by-one that the test would
    then encode as truth.
    """
    ai = _SIGNS.index(asc)
    return facts(asc, {g: _SIGNS[(ai + h - 1) % 12] for g, h in houses.items()})


def fill(asc, houses, default):
    out = {g: default for g in _ALL7}
    out.update(houses)
    return spread(asc, out)


# ── ch19: longevity ────────────────────────────────────────────────────────

def test_v1_eighth_lord_in_an_angle():
    """Aries rising -> 8th Scorpio, lord Mars. Mars in Cancer is the 4th."""
    assert fired(run(facts("Aries", {"Mars": "Cancer"})),
                 "ayush_v1_8th_lord_in_kendra") is True


def test_v1_does_not_fire_from_a_cadent_placement():
    assert fired(run(facts("Aries", {"Mars": "Gemini"})),
                 "ayush_v1_8th_lord_in_kendra") is False


def test_v2_eighth_lord_in_the_eighth_with_a_malefic():
    f = facts("Aries", {"Mars": "Scorpio", "Saturn": "Scorpio"})
    assert fired(run(f), "ayush_v2_short_life_8th_lord_in_8th") is True


def test_v2_needs_the_company_not_merely_the_placement():
    """The 8th lord alone in the 8th is v1's long-life case, not v2's."""
    f = facts("Aries", {"Mars": "Scorpio"})
    assert fired(run(f), "ayush_v2_short_life_8th_lord_in_8th") is False


def test_v3_saturn_in_the_eighth_with_a_malefic():
    f = facts("Aries", {"Saturn": "Scorpio", "Sun": "Scorpio"})
    assert fired(run(f), "ayush_v3_saturn_in_8th_afflicted") is True


def test_v3_carries_the_commentary_flag_because_the_sloka_only_states_an_analogy():
    """The verse says "similarly consider Saturn and the 10th lord" and stops.
    The placements come from the translator's note, and the row must say so or
    the reader cannot discount it."""
    f = facts("Aries", {"Saturn": "Scorpio", "Sun": "Scorpio"})
    assert "commentary_expansion=RSanthanam_note" in row(run(f),
                                                         "ayush_v3_saturn_in_8th_afflicted")["evidence"]


def test_v3b_tenth_lord_in_the_eighth_with_a_malefic():
    """Aries rising -> 10th Capricorn, lord Saturn; 8th is Scorpio."""
    f = facts("Aries", {"Saturn": "Scorpio", "Sun": "Scorpio"})
    assert fired(run(f), "ayush_v3b_10th_lord_in_8th_afflicted") is True


def test_v4_sixth_lord_in_the_twelfth():
    f = facts("Aries", {"Mercury": "Pisces"})
    assert fired(run(f), "ayush_v4_6th_lord_in_12th") is True


def test_v4b_sixth_and_twelfth_lords_both_at_home():
    f = facts("Aries", {"Mercury": "Virgo", "Jupiter": "Pisces"})
    assert fired(run(f), "ayush_v4b_6th_and_12th_lords_in_own_houses") is True


def test_v4b_needs_both_lords_not_one():
    f = facts("Aries", {"Mercury": "Virgo"})
    assert fired(run(f), "ayush_v4b_6th_and_12th_lords_in_own_houses") is False


def test_v4c_sixth_lord_in_the_lagna_with_the_twelfth_lord_in_the_eighth():
    f = facts("Aries", {"Mercury": "Aries", "Jupiter": "Scorpio"})
    assert fired(run(f), "ayush_v4c_6th_lord_in_lagna_12th_lord_in_8th") is True


def test_v5_trio_in_own_signs():
    """Aries rising -> ascendant and 8th lords are both Mars, 5th lord the Sun."""
    f = facts("Aries", {"Mars": "Aries", "Sun": "Leo"})
    assert fired(run(f), "ayush_v5_lords_1_5_8_in_own_rasi_or_navamsa") is True


def test_v5_own_navamsa_alone_is_sufficient():
    f = with_navamsa(facts("Aries", {"Mars": "Gemini", "Sun": "Gemini"}),
                     {"Mars": "Aries", "Sun": "Leo"})
    assert fired(run(f), "ayush_v5_lords_1_5_8_in_own_rasi_or_navamsa") is True


def test_v5_records_that_the_friendly_sign_arm_is_missing():
    """The rule under-fires by construction; that has to be visible, because a
    NOT-FIRED here does not mean the verse's condition failed."""
    ev = row(run(facts("Aries", {})), "ayush_v5_lords_1_5_8_in_own_rasi_or_navamsa")["evidence"]
    assert "friendly_sign_arm_not_applied" in ev


def test_v6_four_significators_all_well_disposed():
    """Aries rising: lagna/8th lord Mars in the 1st, 10th lord Saturn in the 4th."""
    f = facts("Aries", {"Mars": "Aries", "Saturn": "Cancer"})
    assert fired(run(f), "ayush_v6_lords_1_8_10_and_saturn_well_disposed") is True


def test_v6_one_bad_placement_breaks_it():
    f = facts("Aries", {"Mars": "Aries", "Saturn": "Gemini"})
    assert fired(run(f), "ayush_v6_lords_1_8_10_and_saturn_well_disposed") is False


def test_v9_eighth_lord_fallen_with_a_malefic_in_the_eighth():
    f = with_dignity(facts("Aries", {"Mars": "Cancer", "Saturn": "Scorpio"}),
                     "Mars", "Debilitated")
    assert fired(run(f), "ayush_v9_8th_lord_fallen_with_malefic_in_8th") is True


def test_v9_records_the_strength_arm_it_cannot_evaluate():
    f = facts("Aries", {})
    assert "lagna_lord_strength_arm_not_applied" in row(
        run(f), "ayush_v9_8th_lord_fallen_with_malefic_in_8th")["evidence"]


def test_v10_malefics_on_the_eighth_the_eighth_lord_and_the_twelfth():
    """Taurus rising -> 8th Sagittarius (lord Jupiter), 12th Aries."""
    f = facts("Taurus", {"Jupiter": "Leo", "Saturn": "Leo",
                         "Sun": "Sagittarius", "Mars": "Aries"})
    assert fired(run(f), "ayush_v10_malefics_on_8th_house_lord_and_12th") is True


def test_v10_needs_all_three_afflictions():
    f = facts("Taurus", {"Jupiter": "Leo", "Sun": "Sagittarius", "Mars": "Aries"})
    assert fired(run(f), "ayush_v10_malefics_on_8th_house_lord_and_12th") is False


def test_v12_malefics_on_the_fifth_the_eighth_and_the_eighth_lord():
    """Taurus rising -> 5th Virgo, 8th Sagittarius, 8th lord Jupiter."""
    f = facts("Taurus", {"Jupiter": "Leo", "Saturn": "Leo",
                         "Sun": "Virgo", "Mars": "Sagittarius"})
    assert fired(run(f), "ayush_v12_malefics_on_5th_8th_and_8th_lord") is True


def test_v13_eighth_lord_home_and_the_moon_besieged():
    f = facts("Taurus", {"Jupiter": "Sagittarius", "Moon": "Aries", "Mars": "Aries"})
    assert fired(run(f), "ayush_v13_8th_lord_in_8th_moon_besieged") is True


def test_v13_is_cancelled_by_a_benefic_aspect_on_the_moon():
    """The verse's own exemption -- "be bereft of beneficial aspect"."""
    f = facts("Taurus", {"Jupiter": "Sagittarius", "Moon": "Aries", "Mars": "Aries"},
              aspected_by={"Moon": ["Jupiter"]})
    assert fired(run(f), "ayush_v13_8th_lord_in_8th_moon_besieged") is False


def test_v14_lagna_lord_exalted_moon_eleventh_jupiter_eighth():
    """Taurus rising -> lagna lord Venus (exalted in Pisces, the 11th);
    the 8th is Sagittarius."""
    f = with_dignity(facts("Taurus", {"Venus": "Pisces", "Moon": "Pisces",
                                      "Jupiter": "Sagittarius"}), "Venus", "Exalted")
    assert fired(run(f), "ayush_v14_lagna_lord_exalted_moon_11th_jupiter_8th") is True


# ── ch15: home, property, conveyances ──────────────────────────────────────

def test_v2_residential_comforts():
    """Aries rising -> 4th Cancer, lord the Moon; Jupiter aspects the 4th."""
    f = with_aspects_by(facts("Aries", {"Moon": "Cancer", "Jupiter": "Capricorn"}),
                        {"Jupiter": [4]})
    assert fired(run(f), "sukha_v2_residential_comforts") is True


def test_v2_needs_the_benefic_aspect():
    f = facts("Aries", {"Moon": "Cancer"})
    assert fired(run(f), "sukha_v2_residential_comforts") is False


def test_v3_fourth_lord_in_its_own_sign():
    assert fired(run(facts("Aries", {"Moon": "Cancer"})),
                 "sukha_v3_lands_and_conveyances") is True


def test_v3_records_the_translation_divergence():
    """The English reads "5th lord"; the sloka reads sukha-sthaana-adhipa, the
    4th lord. A silent resolution of that is a claim nobody can audit."""
    ev = row(run(facts("Aries", {})), "sukha_v3_lands_and_conveyances")["evidence"]
    assert any(e.startswith("translation_divergence=") for e in ev)


def test_v4_fourth_and_tenth_lords_together_in_an_angle():
    f = facts("Aries", {"Moon": "Cancer", "Saturn": "Cancer"})
    assert fired(run(f), "sukha_v4_mansions") is True


def test_v4_does_not_fire_when_they_are_together_outside_an_angle():
    f = facts("Aries", {"Moon": "Gemini", "Saturn": "Gemini"})
    assert fired(run(f), "sukha_v4_mansions") is False


def test_v6_long_living_mother():
    """4th lord the Moon exalted in Taurus, and Jupiter sits in the 4th."""
    f = with_dignity(facts("Aries", {"Moon": "Taurus", "Jupiter": "Cancer"}),
                     "Moon", "Exalted")
    assert fired(run(f), "sukha_v6_long_living_mother") is True


def test_v8_quadrupeds():
    f = facts("Aries", {"Sun": "Cancer", "Moon": "Sagittarius",
                        "Saturn": "Sagittarius", "Mars": "Aquarius"})
    assert fired(run(f), "sukha_v8_quadrupeds") is True


def test_v10_early_conveyances():
    """Taurus rising -> benefic lagna lord Venus; 4th lord the Sun in the 11th
    (Pisces); Venus itself in the 12th (Aries)."""
    f = facts("Taurus", {"Venus": "Aries", "Sun": "Pisces"})
    assert fired(run(f), "sukha_v10_conveyance_early") is True


def test_v10_records_that_the_fall_arm_is_not_applied():
    ev = row(run(facts("Taurus", {})), "sukha_v10_conveyance_early")["evidence"]
    assert any(e.startswith("fall_arm_not_applied=") for e in ev)


def test_v11_mid_life_conveyances():
    """Aries rising -> 4th Cancer, lord the Moon; the Moon exalted in Taurus
    with Venus, and the Sun in the 4th."""
    f = with_dignity(facts("Aries", {"Sun": "Cancer", "Moon": "Taurus",
                                     "Venus": "Taurus"}), "Moon", "Exalted")
    assert fired(run(f), "sukha_v11_conveyance_mid") is True


def test_v12_later_conveyances_via_the_exaltation_navamsa():
    """4th lord the Moon and 10th lord Saturn share the navamsa Taurus, which
    is the Moon's exaltation sign."""
    f = with_navamsa(facts("Aries", {}), {"Moon": "Taurus", "Saturn": "Taurus"})
    assert fired(run(f), "sukha_v12_conveyance_late") is True


def test_v12_needs_the_shared_navamsa_to_be_the_exaltation_one():
    f = with_navamsa(facts("Aries", {}), {"Moon": "Gemini", "Saturn": "Gemini"})
    assert fired(run(f), "sukha_v12_conveyance_late") is False


def test_v13_exchange_between_the_fourth_and_eleventh_lords():
    f = facts("Aries", {"Moon": "Aquarius", "Saturn": "Cancer"})
    assert fired(run(f), "sukha_v13_conveyance_exchange") is True


def test_v13_is_not_satisfied_by_one_leg_of_the_exchange():
    f = facts("Aries", {"Moon": "Aquarius"})
    assert fired(run(f), "sukha_v13_conveyance_exchange") is False


# ── ch24: the bhava-lord table ─────────────────────────────────────────────

@pytest.mark.parametrize("lord,house,expected", [
    (1, 1, "ch24_v1"),      # chapter opens with the ascendant lord
    (4, 1, "ch24_v37"),     # section heading "EFFECTS OF THE 4TH LORD"
    (5, 1, "ch24_v49"),
    (10, 1, "ch24_v109"),
    (12, 1, "ch24_v133"),
    (6, 10, "ch24_v70"),    # "happy in foreign countries"
    (11, 6, "ch24_v126"),   # "living in foreign places"
    (11, 12, "ch24_v132"),
])
def test_the_ch24_verse_arithmetic_matches_the_chapters_own_headings(lord, house, expected):
    """The citation is DERIVED, not tabulated, so it has to be pinned against
    verse numbers read out of the chapter itself."""
    assert R._ch24_verse(lord, house) == expected


def test_fourth_lord_in_the_ascendant_fires_the_learning_cell():
    f = facts("Aries", {"Moon": "Aries"})
    r = row(run(f), "ch24_l4_h1")
    assert r["fired"] is True
    assert r["evidence"][0] == "ch24_v37"


def test_eleventh_lord_in_the_sixth_fires_the_foreign_residence_cell():
    """Aries rising -> 11th Aquarius, lord Saturn; the 6th is Virgo."""
    f = facts("Aries", {"Saturn": "Virgo"})
    r = row(run(f), "ch24_l11_h6")
    assert r["fired"] is True
    assert "topic=videsha" in r["evidence"]


def test_every_ch24_row_is_emitted_even_when_it_does_not_fire():
    """A selected cell that vanishes when it fails is a cell the gate cannot
    tell apart from one we never implemented."""
    ids = {r["id"] for r in run(facts("Aries", {}))}
    assert {f"ch24_l{l}_h{h}" for l, h in R._CH24_SELECTED} <= ids


# ── ch35: Naabhasa ─────────────────────────────────────────────────────────

def test_rajju_all_seven_in_movable_signs():
    f = fill("Aries", {"Sun": 4, "Moon": 7, "Mars": 10}, 1)
    assert fired(run(f), "naabhasa_rajju") is True


def test_rajju_is_broken_by_a_single_graha_in_another_mode():
    f = fill("Aries", {"Sun": 4, "Moon": 7, "Mars": 10, "Saturn": 2}, 1)
    assert fired(run(f), "naabhasa_rajju") is False


def test_musala_all_seven_in_fixed_signs():
    f = fill("Aries", {"Sun": 5, "Moon": 8, "Mars": 11}, 2)
    assert fired(run(f), "naabhasa_musala") is True


def test_nala_all_seven_in_dual_signs():
    f = fill("Aries", {"Sun": 6, "Moon": 9, "Mars": 12}, 3)
    assert fired(run(f), "naabhasa_nala") is True


def test_maala_benefics_in_three_angles():
    f = facts("Aries", {"Jupiter": "Aries", "Venus": "Cancer", "Moon": "Libra"})
    assert fired(run(f), "naabhasa_maala") is True


def test_maala_needs_three_distinct_angles_not_three_benefics():
    f = facts("Aries", {"Jupiter": "Aries", "Venus": "Aries", "Moon": "Aries"})
    assert fired(run(f), "naabhasa_maala") is False


def test_sarpa_malefics_in_three_angles():
    f = facts("Aries", {"Sun": "Aries", "Mars": "Cancer", "Saturn": "Libra"})
    assert fired(run(f), "naabhasa_sarpa") is True


@pytest.mark.parametrize("rid,houses", [
    ("naabhasa_sakata", (1, 7)),
    ("naabhasa_vihaga", (4, 10)),
    ("naabhasa_sringataka", (1, 5, 9)),
    ("naabhasa_kamala", (1, 4, 7, 10)),
    ("naabhasa_yupa", (1, 2, 3, 4)),
    ("naabhasa_sara", (4, 5, 6, 7)),
    ("naabhasa_sakthi", (7, 8, 9, 10)),
    ("naabhasa_danda", (10, 11, 12, 1)),
    ("naabhasa_nauka", (1, 2, 3, 4, 5, 6, 7)),
    ("naabhasa_koota", (4, 5, 6, 7, 8, 9, 10)),
    ("naabhasa_chatra", (7, 8, 9, 10, 11, 12, 1)),
    ("naabhasa_chapa", (10, 11, 12, 1, 2, 3, 4)),
    ("naabhasa_chakra", (1, 3, 5, 7, 9, 11)),
    ("naabhasa_samudra", (2, 4, 6, 8, 10, 12)),
])
def test_each_confined_aakriti_fires_on_a_chart_built_for_it(rid, houses):
    """Spread the seven grahas across exactly the houses the shape names."""
    f = fill("Aries", {g: houses[i % len(houses)] for i, g in enumerate(_ALL7)},
             houses[0])
    assert fired(run(f), rid) is True


@pytest.mark.parametrize("rid,outlier", [
    ("naabhasa_sakata", 6),
    ("naabhasa_kamala", 6),
    ("naabhasa_chakra", 6),
    ("naabhasa_nauka", 9),   # Nauka spans houses 1..7, so 6 is INSIDE its shape
])
def test_an_aakriti_does_not_fire_on_partial_occupancy(rid, outlier):
    """These verses all say ALL the planets. One graha outside the shape is the
    difference between a yoga and a coincidence.

    The outlier house is per-shape on purpose: a single shared outlier would sit
    inside the wider shapes and the test would pass by accident.
    """
    f = fill("Aries", {"Saturn": outlier}, 1)
    assert fired(run(f), rid) is False


def test_gada_two_successive_angles():
    f = fill("Aries", {"Sun": 4, "Moon": 4, "Mars": 4}, 1)
    assert fired(run(f), "naabhasa_gada") is True


def test_gada_does_not_fire_on_two_opposite_angles():
    """1 and 7 are Sakata's shape, not Gada's -- they are not successive."""
    f = fill("Aries", {"Sun": 7, "Moon": 7, "Mars": 7}, 1)
    rows = run(f)
    assert fired(rows, "naabhasa_gada") is False
    assert fired(rows, "naabhasa_sakata") is True


def test_hala_one_of_the_three_non_angular_trine_sets():
    f = fill("Aries", {"Sun": 6, "Moon": 10, "Mars": 2}, 2)
    assert fired(run(f), "naabhasa_hala") is True


def test_vaapi_all_seven_outside_the_angles():
    f = fill("Aries", {"Sun": 5, "Moon": 8, "Mars": 11}, 2)
    assert fired(run(f), "naabhasa_vaapi") is True


def test_vajra_benefics_in_the_first_and_seventh_malefics_in_the_fourth_and_tenth():
    f = fill("Aries", {"Jupiter": 1, "Venus": 7, "Moon": 1,
                       "Sun": 4, "Mars": 10, "Saturn": 4, "Mercury": 4}, 1)
    assert fired(run(f), "naabhasa_vajra") is True


def test_yava_is_vajras_mirror():
    f = fill("Aries", {"Jupiter": 4, "Venus": 10, "Moon": 4,
                       "Sun": 1, "Mars": 7, "Saturn": 1, "Mercury": 1}, 4)
    assert fired(run(f), "naabhasa_yava") is True


def test_vajra_needs_both_arms_not_the_translations_literal_or():
    """The English reads "benefics in 1 and 7 OR malefics in 4 and 10". Taken
    literally that fires on any chart with Jupiter and Venus angular, which no
    shape yoga can mean. Benefics angular with the malefics scattered must NOT
    fire."""
    f = fill("Aries", {"Jupiter": 1, "Venus": 7, "Moon": 1,
                       "Sun": 3, "Mars": 6, "Saturn": 9, "Mercury": 12}, 1)
    assert fired(run(f), "naabhasa_vajra") is False


def test_the_sankhya_suppression_row_names_its_blockers():
    """ch35 v17 makes the sankhya yogas inoperable when another Naabhasa yoga
    holds. The suppression is reported, not applied silently to the sankhya
    row, so the sankhya verdict stays auditable."""
    f = fill("Aries", {"Sun": 4, "Moon": 7, "Mars": 10}, 1)
    r = row(run(f), "naabhasa_sankhya_suppressed")
    assert r["fired"] is True
    assert "naabhasa_rajju" in r["reason"]


def test_the_sankhya_suppression_row_does_not_fire_on_a_shapeless_chart():
    f = fill("Aries", {"Sun": 2, "Moon": 3, "Mars": 5, "Mercury": 6,
                       "Jupiter": 8, "Venus": 9, "Saturn": 12}, 1)
    assert fired(run(f), "naabhasa_sankhya_suppressed") is False


# ── ch37 / ch38: lunar and solar ───────────────────────────────────────────

def test_durudhara_needs_both_flanks_of_the_moon():
    f = facts("Aries", {"Moon": "Aries", "Mars": "Taurus", "Jupiter": "Pisces"})
    assert fired(run(f), "durudhara") is True


def test_durudhara_does_not_fire_on_one_flank():
    """One flank alone is Sunaphaa or Anaphaa, which are separate rows."""
    f = facts("Aries", {"Moon": "Aries", "Mars": "Taurus", "Jupiter": "Gemini"})
    assert fired(run(f), "durudhara") is False


def test_durudhara_ignores_the_sun():
    """The sloka excludes the Sun explicitly."""
    f = facts("Aries", {"Moon": "Aries", "Sun": "Taurus", "Jupiter": "Pisces"})
    assert fired(run(f), "durudhara") is False


def test_kemadruma_the_strict_four_clause_form():
    """Moon alone in the 1st; every other graha (bar the Sun) in the 3rd, so
    nothing is with the Moon, in its 2nd or 12th, or in an angle."""
    f = fill("Aries", {"Moon": 1}, 3)
    assert fired(run(f), "kemadruma") is True


def test_kemadruma_is_broken_by_a_graha_in_an_angle():
    """The angular clause is the one later texts drop; keeping it is the whole
    point of citing ch37 v11 rather than a summary."""
    f = fill("Aries", {"Moon": 1, "Saturn": 7}, 3)
    assert fired(run(f), "kemadruma") is False


def test_kemadruma_is_broken_by_a_graha_beside_the_moon():
    f = fill("Aries", {"Moon": 1, "Saturn": 1}, 3)
    assert fired(run(f), "kemadruma") is False


def test_chandra_dhana_counts_benefics_in_the_upachayas_from_the_moon():
    # Everything but Jupiter is parked in the 2nd, which is NOT an upachaya --
    # the count is the graded part of the sloka, so it has to be isolated.
    f = fill("Aries", {"Moon": 1, "Jupiter": 3}, 2)
    r = row(run(f), "chandra_dhana_upachaya")
    assert r["fired"] is True
    assert "benefic_count=1" in r["evidence"]


def test_chandra_dhana_does_not_fire_with_no_benefic_in_an_upachaya():
    f = fill("Aries", {"Moon": 1}, 2)
    assert fired(run(f), "chandra_dhana_upachaya") is False


def test_vosi_a_planet_in_the_twelfth_from_the_sun():
    f = facts("Aries", {"Sun": "Aries", "Jupiter": "Pisces"})
    assert fired(run(f), "vosi") is True


def test_vosi_ignores_the_moon():
    f = facts("Aries", {"Sun": "Aries", "Moon": "Pisces"})
    assert fired(run(f), "vosi") is False


def test_ubhayachari_needs_both_flanks_of_the_sun():
    f = facts("Aries", {"Sun": "Aries", "Jupiter": "Pisces", "Venus": "Taurus"})
    rows = run(f)
    assert fired(rows, "ubhayachari") is True
    assert fired(rows, "vosi") is True


def test_ubhayachari_does_not_fire_on_one_flank():
    f = facts("Aries", {"Sun": "Aries", "Jupiter": "Pisces"})
    assert fired(run(f), "ubhayachari") is False


# ── invariants over the whole batch ────────────────────────────────────────

_SLOKA = re.compile(r"^ch\d+_v\d+$")


def test_every_row_cites_a_sloka_as_its_first_evidence_token():
    """P-029's other half: the detector says nothing about MEANING, so the
    verse id is the only route the reader has back to the doctrine. A row
    without one is a fact with no text behind it."""
    missing = [r["id"] for r in run(facts("Aries", {}))
               if not (r["evidence"] and _SLOKA.match(str(r["evidence"][0])))]
    assert missing == []


def test_row_ids_are_unique_across_the_batch():
    ids = [r["id"] for r in run(facts("Aries", {}))]
    assert len(ids) == len(set(ids))


def test_no_row_id_collides_with_the_pre_existing_detector():
    """The Naabhasa sankhya rows already use the `naabhasa_` prefix; a
    collision there would silently shadow an oracle-validated verdict."""
    f = facts("Aries", {})
    new = {r["id"] for r in run(f)}
    old = {r["id"] for r in (R._detect_raja(f) + R._detect_special(f)
                             + R._detect_neecha(f) + R._detect_jhora_set(f)
                             + R._detect_dhana(f) + R._detect_kalatra_santana(f))}
    assert new & old == set()


def test_every_row_reports_a_reason_whether_it_fired_or_not():
    for r in run(facts("Aries", {})):
        assert r["reason"].strip(), r["id"]


def test_the_batch_is_wired_into_detect():
    f = facts("Aries", {})
    assert {r["id"] for r in run(f)} <= {r["id"] for r in R.detect(f)}
