"""BPHS ch41 (Combinations For Wealth) and ch42 (Combinations For Penury).

HARDEST CASE FIRST (Working Style #3): every rule gets a chart built to FIRE it,
not merely one that fails it. A rule that never fires in a test is a rule whose
positive arm is unproven, and this catalogue is full of sign-locked verses that
would otherwise sit silently not-firing forever.

Facts are synthetic and minimal, in the shape `frontend/app.py` composes and the
capture writes. Nothing here is read from an oracle file (P-027).
"""
from __future__ import annotations

import pytest

from agent.calculations.yogas import rules as R

_SIGNS = ("Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra",
          "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces")
_LORD = {"Aries": "Mars", "Taurus": "Venus", "Gemini": "Mercury",
         "Cancer": "Moon", "Leo": "Sun", "Virgo": "Mercury", "Libra": "Venus",
         "Scorpio": "Mars", "Sagittarius": "Jupiter", "Capricorn": "Saturn",
         "Aquarius": "Saturn", "Pisces": "Jupiter"}


def facts(asc: str, placements: dict[str, str], aspected_by: dict | None = None):
    """Build a fact block from an ascendant sign and graha -> sign placements.

    House numbers and `house_lords` are DERIVED from the ascendant so a test
    cannot accidentally assert an internally inconsistent chart.
    """
    ai = _SIGNS.index(asc)
    def house(sign):
        return ((_SIGNS.index(sign) - ai) % 12) + 1
    # Every classical graha is placed, because a real chart always places them
    # all and a None `in_house` is not a state production can reach. Unlisted
    # grahas go to the 3rd sign, well away from the houses these verses test.
    filler = _SIGNS[(ai + 2) % 12]
    full = {g: filler for g in ("Sun", "Moon", "Mars", "Mercury", "Jupiter",
                                "Venus", "Saturn")}
    full.update(placements)
    placements = full
    pos = {g: {"house": house(s), "sign": s} for g, s in placements.items()}
    lords = {}
    for h in range(1, 13):
        sign = _SIGNS[(ai + h - 1) % 12]
        lord = _LORD[sign]
        lords[h] = {"lord": lord, "sign": sign,
                    "in_house": house(placements[lord]) if lord in placements else None}
    return {"ascendant_sign": asc, "planet_positions": pos, "house_lords": lords,
            "aspects": {"conjunctions": [], "aspects_by_planet": {},
                        "aspected_by": aspected_by or {}}}


def fired(rows, rid):
    for r in rows:
        if r["id"] == rid:
            return r["fired"]
    return None


def run(f):
    return R._detect_dhana(f)


# ── ch41 vv.2-8: great affluence ───────────────────────────────────────────

def test_the_general_formula_bphs_states_itself_fires():
    """v8's closing note: the 5th lord in the 5th while the 11th lord is in the
    11th. Sagittarius rising -> 5th Aries (Mars), 11th Libra (Venus)."""
    f = facts("Sagittarius", {"Mars": "Aries", "Venus": "Libra"})
    assert fired(run(f), "dhana_maha_5_11") is True


def test_the_general_formula_does_not_fire_when_only_one_lord_is_home():
    f = facts("Sagittarius", {"Mars": "Aries", "Venus": "Taurus"})
    assert fired(run(f), "dhana_maha_5_11") is False


def test_v7_mars_in_own_fifth_with_venus_in_eleventh():
    f = facts("Sagittarius", {"Mars": "Aries", "Venus": "Libra"})
    assert fired(run(f), "dhana_v7_mars_5_venus_11") is True


def test_v2_venus_fifth_mars_eleventh():
    """Capricorn rising -> 5th Taurus (Venus), 11th Scorpio (Mars)."""
    f = facts("Capricorn", {"Venus": "Taurus", "Mars": "Scorpio"})
    assert fired(run(f), "dhana_v2_venus_5_mars_11") is True


def test_v3_requires_all_three_of_moon_mars_jupiter_in_the_eleventh():
    """Taurus rising -> 5th Virgo (Mercury), 11th Pisces (Jupiter)."""
    full = facts("Taurus", {"Mercury": "Virgo", "Moon": "Pisces",
                            "Mars": "Pisces", "Jupiter": "Pisces"})
    assert fired(run(full), "dhana_v3_mercury_5") is True
    partial = facts("Taurus", {"Mercury": "Virgo", "Moon": "Pisces",
                               "Jupiter": "Pisces"})
    assert fired(run(partial), "dhana_v3_mercury_5") is False, "Mars is required"


def test_v4_sun_in_leo_fifth():
    """Aries rising -> 5th Leo, 11th Aquarius."""
    f = facts("Aries", {"Sun": "Leo", "Saturn": "Aquarius", "Moon": "Aquarius",
                        "Jupiter": "Aquarius"})
    assert fired(run(f), "dhana_v4_sun_5") is True


def test_v8_moon_in_cancer_fifth_saturn_eleventh():
    """Pisces rising -> 5th Cancer, 11th Capricorn."""
    f = facts("Pisces", {"Moon": "Cancer", "Saturn": "Capricorn"})
    assert fired(run(f), "dhana_v8_moon_5_saturn_11") is True


def test_a_sign_locked_verse_is_not_emitted_when_its_sign_cannot_arise():
    """Aries rising puts Leo on the 5th, so the Venus-5th verse (v2) cannot
    apply at all. It is ABSENT, not ruled out -- reporting "your 5th is not a
    Venus sign" on every chart would be noise, and a rule that cannot apply is
    not a rule this chart failed."""
    f = facts("Aries", {"Sun": "Leo"})
    assert fired(run(f), "dhana_v2_venus_5_mars_11") is None


# ── ch41 vv.9-15: wealth through own-sign lagna ────────────────────────────

@pytest.mark.parametrize("asc,graha,supporters,rid", [
    ("Leo", "Sun", ("Mars", "Jupiter"), "dhana_lagna_sun"),
    ("Cancer", "Moon", ("Mercury", "Jupiter"), "dhana_lagna_moon"),
    ("Aries", "Mars", ("Mercury", "Venus", "Saturn"), "dhana_lagna_mars"),
    ("Gemini", "Mercury", ("Saturn", "Jupiter"), "dhana_lagna_mercury"),
    ("Sagittarius", "Jupiter", ("Mercury", "Mars"), "dhana_lagna_jupiter"),
    ("Libra", "Venus", ("Saturn", "Mercury"), "dhana_lagna_venus"),
    ("Capricorn", "Saturn", ("Mars", "Jupiter"), "dhana_lagna_saturn"),
])
def test_each_wealth_verse_fires_by_aspect(asc, graha, supporters, rid):
    """"Conjunct OR aspected by" -- the aspect arm."""
    f = facts(asc, {graha: asc}, aspected_by={graha: list(supporters)})
    assert fired(run(f), rid) is True


def test_the_conjunction_arm_fires_too():
    """Same verse, the other half of the text's disjunction: supporters sharing
    the sign rather than aspecting."""
    f = facts("Leo", {"Sun": "Leo", "Mars": "Leo", "Jupiter": "Leo"})
    assert fired(run(f), "dhana_lagna_sun") is True


def test_a_missing_supporter_does_not_fire():
    f = facts("Leo", {"Sun": "Leo", "Mars": "Leo"})
    assert fired(run(f), "dhana_lagna_sun") is False


def test_the_graha_must_be_in_its_OWN_sign_rising():
    """Sun in the 1st but not in Leo is not this verse."""
    f = facts("Aries", {"Sun": "Aries"}, aspected_by={"Sun": ["Mars", "Jupiter"]})
    assert fired(run(f), "dhana_lagna_sun") is False


# ── ch42: penury, and the nullifications the text supplies ─────────────────

def test_v4_ketu_with_lagna_and_lagna_lord_in_the_eighth():
    f = facts("Aries", {"Ketu": "Aries", "Mars": "Scorpio"})
    assert fired(run(f), "daridra_v4_ketu_lagna_lord_8th") is True


def test_v4_needs_both_halves():
    f = facts("Aries", {"Ketu": "Aries", "Mars": "Taurus"})
    assert fired(run(f), "daridra_v4_ketu_lagna_lord_8th") is False


def test_v6_lagna_lord_with_a_dusthana_lord_and_no_benefic_aspect():
    """Aries rising: Mars is lagna lord; Mercury rules the 6th (Virgo). Put
    them together, with no benefic aspecting Mars."""
    f = facts("Aries", {"Mars": "Gemini", "Mercury": "Gemini"})
    assert fired(run(f), "daridra_v6_lagna_lord_with_evil_lord") is True


def test_v6_is_nullified_by_a_benefic_aspect():
    f = facts("Aries", {"Mars": "Gemini", "Mercury": "Gemini", "Jupiter": "Libra"},
              aspected_by={"Mars": ["Jupiter"]})
    assert fired(run(f), "daridra_v6_lagna_lord_with_evil_lord") is False


def test_v7_fifth_lord_in_sixth_and_ninth_lord_in_twelfth():
    """Aries rising -> 5th lord Sun, 9th lord Jupiter."""
    f = facts("Aries", {"Sun": "Virgo", "Jupiter": "Pisces"})
    assert fired(run(f), "daridra_v7_5th_in_6th_9th_in_12th") is True


def test_v16_mars_and_saturn_in_the_second_destroy_wealth():
    f = facts("Aries", {"Mars": "Taurus", "Saturn": "Taurus"})
    rows = run(f)
    assert fired(rows, "daridra_v16_mars_saturn_2nd") is True
    assert fired(rows, "dhana_v17_mars_saturn_2nd_mercury_aspect") is False


def test_v16_is_REVERSED_to_great_wealth_when_mercury_aspects_both():
    """The text states the affliction and its undoing in one breath, so the
    nullification is part of the rule, not a later cancelling pass."""
    f = facts("Aries", {"Mars": "Taurus", "Saturn": "Taurus", "Mercury": "Scorpio"},
              aspected_by={"Mars": ["Mercury"], "Saturn": ["Mercury"]})
    rows = run(f)
    assert fired(rows, "daridra_v16_mars_saturn_2nd") is False
    assert fired(rows, "dhana_v17_mars_saturn_2nd_mercury_aspect") is True


def test_v17_sun_in_the_second_splits_on_saturns_aspect():
    afflicted = facts("Aries", {"Sun": "Taurus", "Saturn": "Scorpio"},
                      aspected_by={"Sun": ["Saturn"]})
    assert fired(run(afflicted), "daridra_v17_sun_2nd_saturn_aspect") is True
    assert fired(run(afflicted), "dhana_v17_sun_2nd_unaspected") is False

    clean = facts("Aries", {"Sun": "Taurus", "Saturn": "Leo"})
    assert fired(run(clean), "daridra_v17_sun_2nd_saturn_aspect") is False
    assert fired(run(clean), "dhana_v17_sun_2nd_unaspected") is True, (
        "the same verse's positive arm must be reported, not merely implied")


def test_v18_saturn_in_the_second_aspected_by_the_sun():
    f = facts("Aries", {"Saturn": "Taurus", "Sun": "Scorpio"},
              aspected_by={"Saturn": ["Sun"]})
    assert fired(run(f), "daridra_v18_saturn_2nd_sun_aspect") is True


# ── catalogue invariants ───────────────────────────────────────────────────

def test_every_rule_carries_its_sloka_in_the_evidence():
    """P-029: reasons state observed placements only, so the VERSE has to live
    in the evidence or the citation is nowhere."""
    f = facts("Aries", {"Sun": "Leo", "Mars": "Taurus", "Saturn": "Taurus"})
    for r in run(f):
        assert any("ch41_v" in str(e) or "ch42_v" in str(e) for e in r["evidence"]), r["id"]


def test_no_reason_teaches_the_doctrine():
    """P-029: a reason reports the chart, never what the rule means."""
    f = facts("Aries", {"Sun": "Leo"})
    banned = ("will be", "native will", "confers", "bestow", "signifies")
    for r in run(f):
        low = r["reason"].lower()
        assert not any(b in low for b in banned), (r["id"], r["reason"])


def test_rule_ids_are_unique_across_the_whole_detector():
    f = facts("Aries", {"Sun": "Leo", "Moon": "Cancer", "Mars": "Taurus",
                        "Mercury": "Gemini", "Jupiter": "Pisces",
                        "Venus": "Libra", "Saturn": "Taurus"})
    ids = [r["id"] for r in R.detect(f)]
    assert len(ids) == len(set(ids)), [i for i in ids if ids.count(i) > 1]


def test_the_detector_never_raises_on_an_empty_or_broken_fact_block():
    for bad in ({}, {"house_lords": {}}, {"ascendant_sign": "Nonsense"},
                {"house_lords": {"1": {}}, "planet_positions": None}):
        assert isinstance(R._detect_dhana(bad), list)
