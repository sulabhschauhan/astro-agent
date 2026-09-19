"""BPHS ch18 (Seventh House / marriage) and ch16 (Fifth House / children).

HARDEST CASE FIRST: every rule gets a chart built to FIRE it. Nullifications
the verse states are tested on BOTH arms -- a rule whose exemption is untested
is a rule that will silently over-fire.
"""
from __future__ import annotations

import pytest

from agent.calculations.yogas import rules as R
from tests.calculations.yogas.test_dhana_daridra import facts, fired


def run(f):
    return R._detect_kalatra_santana(f)


def with_dignity(f, graha, dignity):
    f["planet_positions"][graha]["dignity"] = dignity
    return f


def with_navamsa(f, pairs):
    f["navamsa"] = {"placements": {g: {"sign": s} for g, s in pairs.items()}}
    return f


# ── ch18: marriage ─────────────────────────────────────────────────────────

def test_v1_seventh_lord_in_its_own_sign():
    """Aries rising -> 7th is Libra, lord Venus. Venus in Libra is own sign."""
    f = facts("Aries", {"Venus": "Libra"})
    assert fired(run(f), "kalatra_v1_7th_lord_strong_placed") is True


def test_v1_also_fires_on_exaltation():
    f = with_dignity(facts("Aries", {"Venus": "Pisces"}), "Venus", "Exalted")
    assert fired(run(f), "kalatra_v1_7th_lord_strong_placed") is True


def test_v1_does_not_fire_on_a_plain_placement():
    f = facts("Aries", {"Venus": "Gemini"})
    assert fired(run(f), "kalatra_v1_7th_lord_strong_placed") is False


def test_v2_seventh_lord_in_a_dusthana():
    """Aries rising, Venus (7th lord) in Virgo = the 6th."""
    f = facts("Aries", {"Venus": "Virgo"})
    assert fired(run(f), "kalatra_v2_7th_lord_in_dusthana") is True


def test_v2_IS_EXEMPTED_by_own_sign_or_exaltation():
    """The verse excludes own-sign and exaltation placement explicitly, so the
    exemption is part of the rule, not a later cancelling pass.

    Leo rising -> 7th Aquarius, lord Saturn. Saturn in Capricorn is the 6th AND
    its own sign.
    """
    f = facts("Leo", {"Saturn": "Capricorn"})
    rows = run(f)
    assert fired(rows, "kalatra_v2_7th_lord_in_dusthana") is False
    assert fired(rows, "kalatra_v1_7th_lord_strong_placed") is True


def test_v6_plurality_saturn_or_venus_sign_with_benefic_aspect():
    """Aries rising -> 7th lord Venus; put it in Capricorn (a Saturn sign) with
    Jupiter aspecting."""
    f = facts("Aries", {"Venus": "Capricorn", "Jupiter": "Cancer"},
              aspected_by={"Venus": ["Jupiter"]})
    assert fired(run(f), "kalatra_v6_plurality") is True


def test_v6_needs_the_benefic_aspect():
    f = facts("Aries", {"Venus": "Capricorn"})
    assert fired(run(f), "kalatra_v6_plurality") is False


def test_v6_exaltation_alone_is_sufficient():
    """The verse's second arm: "should the 7th lord be particularly in
    exaltation, the same effects"."""
    f = with_dignity(facts("Aries", {"Venus": "Pisces"}), "Venus", "Exalted")
    assert fired(run(f), "kalatra_v6_plurality") is True


# ── ch16: children ─────────────────────────────────────────────────────────

def test_v1_both_lords_well_placed():
    """Aries rising -> lagna lord Mars, 5th lord Sun. Mars in Aries (own, and a
    kendra); Sun in Leo (the 5th, a trine)."""
    f = facts("Aries", {"Mars": "Aries", "Sun": "Leo"})
    assert fired(run(f), "santana_v1_lords_well_placed") is True


def test_v1_fails_when_either_lord_is_badly_placed():
    f = facts("Aries", {"Mars": "Aries", "Sun": "Virgo"})
    assert fired(run(f), "santana_v1_lords_well_placed") is False


def test_v1b_fifth_lord_in_a_dusthana():
    f = facts("Aries", {"Sun": "Virgo"})
    assert fired(run(f), "santana_v1b_5th_lord_in_dusthana") is True


def test_v4_fifth_lord_in_sixth_with_lagna_lord_joined_by_mars():
    """Taurus rising -> lagna lord Venus, 5th lord Mercury. Mercury in Libra is
    the 6th; Venus with Mars."""
    f = facts("Taurus", {"Mercury": "Libra", "Venus": "Gemini", "Mars": "Gemini"})
    assert fired(run(f), "santana_v4_5th_lord_6th_lagna_lord_mars") is True


def test_v5_single_issue_mercury_and_ketu_in_the_fifth():
    """Aries rising -> 5th Leo, 5th lord Sun. Sun fallen in Libra (the 7th)?
    No -- the verse needs the dusthana too, so put the Sun in Libra = 7th fails;
    use Capricorn rising: 5th Taurus, lord Venus, fallen in Virgo = the 9th...
    Simplest: Leo rising -> 5th Sagittarius, lord Jupiter, fallen in Capricorn
    = the 6th."""
    f = with_dignity(
        facts("Leo", {"Jupiter": "Capricorn", "Mercury": "Sagittarius",
                      "Ketu": "Sagittarius"}), "Jupiter", "Debilitated")
    assert fired(run(f), "santana_v5_one_child_mercury_ketu") is True


def test_v5_needs_the_fifth_lord_actually_fallen():
    f = facts("Leo", {"Jupiter": "Capricorn", "Mercury": "Sagittarius",
                      "Ketu": "Sagittarius"})
    assert fired(run(f), "santana_v5_one_child_mercury_ketu") is False


def test_v6_single_issue_saturn_and_mercury_with_no_aspect_to_the_fifth():
    f = with_dignity(
        facts("Leo", {"Jupiter": "Capricorn", "Saturn": "Sagittarius",
                      "Mercury": "Sagittarius"}), "Jupiter", "Debilitated")
    assert fired(run(f), "santana_v6_one_child_saturn_mercury") is True


def test_v6_is_cancelled_when_the_fifth_lord_aspects_the_fifth():
    f = with_dignity(
        facts("Leo", {"Jupiter": "Capricorn", "Saturn": "Sagittarius",
                      "Mercury": "Sagittarius"}), "Jupiter", "Debilitated")
    f["aspects"]["aspects_by_planet"] = {"Jupiter": [5]}
    assert fired(run(f), "santana_v6_one_child_saturn_mercury") is False


def test_v7_progeny_after_difficulty():
    """Leo rising -> 9th lord Mars, 5th lord Jupiter."""
    f = with_dignity(
        facts("Leo", {"Mars": "Leo", "Jupiter": "Capricorn",
                      "Mercury": "Sagittarius", "Ketu": "Sagittarius"}),
        "Jupiter", "Debilitated")
    assert fired(run(f), "santana_v7_progeny_after_difficulty") is True


@pytest.mark.parametrize("placement,dignity,expected", [
    ("Virgo", None, True),        # the 6th
    ("Leo", None, True),          # the 5th itself
    ("Libra", "Debilitated", True),
    ("Sagittarius", None, False),  # the 9th, undignified: none of the arms
])
def test_v8_issues_with_difficulty_arms(placement, dignity, expected):
    f = facts("Aries", {"Sun": placement})
    if dignity:
        with_dignity(f, "Sun", dignity)
    assert fired(run(f), "santana_v8_issues_with_difficulty") is expected


def test_v10_luminaries_need_BOTH_the_same_rasi_and_the_same_navamsa():
    same = with_navamsa(facts("Aries", {"Sun": "Leo", "Moon": "Leo"}),
                        {"Sun": "Taurus", "Moon": "Taurus"})
    assert fired(run(same), "santana_v10_luminaries_same_rasi_and_navamsa") is True

    rasi_only = with_navamsa(facts("Aries", {"Sun": "Leo", "Moon": "Leo"}),
                             {"Sun": "Taurus", "Moon": "Gemini"})
    assert fired(run(rasi_only), "santana_v10_luminaries_same_rasi_and_navamsa") is False, (
        "the navamsa half is required by the verse")


def test_v10_is_unevaluable_rather_than_false_without_a_navamsa():
    """D9 is fail-soft (S130). Absent navamsa must not fire the rule."""
    f = facts("Aries", {"Sun": "Leo", "Moon": "Leo"})
    assert fired(run(f), "santana_v10_luminaries_same_rasi_and_navamsa") is False


def test_v13_fifth_lord_joined_with_the_moon():
    f = facts("Aries", {"Sun": "Gemini", "Moon": "Gemini"})
    assert fired(run(f), "santana_v13_daughters") is True


# ── the boundary this batch deliberately did not cross ─────────────────────

def test_no_rule_characterises_a_spouse_or_predicts_a_death():
    """ch18 vv.7-13, ch18 v3b, ch19 v42 and ch16 v14 are computable and are NOT
    built: spouse sexual conduct, spouse's body, death of a spouse, and
    "questionable birth". That is a product call for Sulabh, and this test is
    what stops it being reversed by accident."""
    f = facts("Aries", {"Sun": "Leo", "Venus": "Libra", "Moon": "Gemini"})
    banned = ("harlot", "libidin", "breast", "private parts", "questionable birth",
              "death of wife", "will not live", "illegal")
    for r in R.detect(f):
        blob = f"{r['id']} {r['name']} {r['reason']}".lower()
        assert not any(b in blob for b in banned), r["id"]


def test_every_new_rule_cites_its_sloka():
    f = facts("Aries", {"Sun": "Leo", "Venus": "Libra"})
    for r in run(f):
        assert any("ch18_v" in str(e) or "ch16_v" in str(e) for e in r["evidence"]), r["id"]


def test_no_reason_teaches_the_doctrine():
    f = facts("Aries", {"Sun": "Leo", "Venus": "Libra"})
    banned = ("will be", "native will", "confers", "bestow", "signifies")
    for r in run(f):
        assert not any(b in r["reason"].lower() for b in banned), (r["id"], r["reason"])


def test_the_detector_never_raises_on_a_broken_fact_block():
    for bad in ({}, {"house_lords": {}}, {"house_lords": {"1": {}}},
                {"ascendant_sign": "Nonsense", "house_lords": {"1": {"lord": "Mars"}}}):
        assert isinstance(R._detect_kalatra_santana(bad), list)
