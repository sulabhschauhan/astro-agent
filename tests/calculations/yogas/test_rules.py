"""Logic tests for agent/calculations/yogas/rules.py (S133).

These are UNIT tests of the yoga LOGIC over synthetic fact blocks built by
hand -- they prove each check fires and does not fire under the right
placements, and that the detector never raises. They deliberately do NOT
assert oracle verdicts: validating the calculations against sulabh.md /
surbhi.md 10c is the job of scripts/probe_yoga_charts.py, which computes each
chart from birth details FIRST and compares AFTER (P-027). Nothing here feeds
an oracle value into a calculation.
"""
from __future__ import annotations

import pytest

from agent.calculations.yogas import rules, detector


# --------------------------------------------------------------- fact builders

def _pp(**planets):
    """planet_positions from Graha=(house, sign[, dignity]) kwargs."""
    out = {}
    for g, spec in planets.items():
        if len(spec) == 3:
            h, s, d = spec
            out[g] = {"house": h, "sign": s, "dignity": d}
        else:
            h, s = spec
            out[g] = {"house": h, "sign": s}
    return out


def _lords(mapping):
    """house_lords from {house: (lord, sign, in_house)}."""
    return {h: {"lord": lord, "sign": sign, "in_house": ih}
            for h, (lord, sign, ih) in mapping.items()}


def _verdict(rows, rid):
    for r in rows:
        if r["id"] == rid:
            return r
    return None


def _fired(rows, rid):
    v = _verdict(rows, rid)
    assert v is not None, f"{rid} not present; got {[r['id'] for r in rows]}"
    return v["fired"]


# ------------------------------------------------------------- raja / dharma

def test_dharma_karmadhipati_fires_when_9th_and_10th_lord_share_a_house():
    facts = {"house_lords": _lords({9: ("Sun", "Leo", 4), 10: ("Mercury", "Virgo", 4)})}
    assert _fired(rules._detect_raja(facts), "dharma_karmadhipati") is True


def test_dharma_karmadhipati_not_fired_when_lords_in_different_houses():
    facts = {"house_lords": _lords({9: ("Sun", "Leo", 4), 10: ("Mercury", "Virgo", 7)})}
    assert _fired(rules._detect_raja(facts), "dharma_karmadhipati") is False


def test_kendra_trikona_link_fires_on_conjunction():
    # 4th lord and 5th lord in the same house.
    facts = {"house_lords": _lords({4: ("Moon", "Cancer", 2), 5: ("Sun", "Leo", 2)}),
             "aspects": {"aspected_by": {}}}
    assert _fired(rules._detect_raja(facts), "kendra_trikona_4_5") is True


def test_yogakaraka_reported_when_one_planet_lords_kendra_and_kona():
    facts = {"house_lords": _lords({4: ("Saturn", "Capricorn", 1), 5: ("Saturn", "Aquarius", 1)}),
             "aspects": {"aspected_by": {}}}
    v = _verdict(rules._detect_raja(facts), "kendra_trikona_4_5")
    assert v["fired"] is True and "Yogakaraka" in v["name"]


# ------------------------------------------------------------- vipareeta own-house

def test_harsha_fires_when_6th_lord_in_6th():
    facts = {"house_lords": _lords({6: ("Mars", "Scorpio", 6), 8: ("Jupiter", "Pisces", 3),
                                    12: ("Venus", "Libra", 5)}),
             "planet_positions": {}}
    assert _fired(rules._detect_special(facts), "harsha_yoga") is True


def test_sarala_not_fired_when_8th_lord_elsewhere():
    facts = {"house_lords": _lords({6: ("Mars", "Scorpio", 6), 8: ("Jupiter", "Pisces", 12),
                                    12: ("Venus", "Libra", 5)}),
             "planet_positions": {}}
    assert _fired(rules._detect_special(facts), "sarala_yoga") is False


def test_vipareeta_rows_carry_no_contested_flag_anymore():
    facts = {"house_lords": _lords({6: ("Mars", "Scorpio", 6)}), "planet_positions": {}}
    v = _verdict(rules._detect_special(facts), "harsha_yoga")
    assert "contested" not in v and "contested_note" not in v


# ------------------------------------------------------------- vipareeta pairs

def test_vipareeta_6_12_fires_on_conjunction():
    # 6th and 12th lords in one sign.
    facts = {"house_lords": _lords({6: ("Mars", "Scorpio", 3), 8: ("Sun", "Leo", 4),
                                    12: ("Venus", "Libra", 3)}),
             "planet_positions": _pp(Mars=(3, "Gemini"), Venus=(3, "Gemini"), Sun=(4, "Cancer"))}
    assert _fired(rules._vry_dusthana_pairs(facts), "vipareeta_6_12_link") is True


def test_vipareeta_6_8_fires_on_samasaptaka():
    facts = {"house_lords": _lords({6: ("Mars", "Scorpio", 3), 8: ("Sun", "Leo", 9),
                                    12: ("Venus", "Libra", 5)}),
             "planet_positions": _pp(Mars=(1, "Aries"), Sun=(7, "Libra"), Venus=(5, "Leo"))}
    assert _fired(rules._vry_dusthana_pairs(facts), "vipareeta_6_8_link") is True


def test_vipareeta_pair_degenerate_when_one_planet_lords_both():
    facts = {"house_lords": _lords({6: ("Mars", "Scorpio", 3), 8: ("Mars", "Aries", 3),
                                    12: ("Venus", "Libra", 5)}),
             "planet_positions": _pp(Mars=(3, "Gemini"), Venus=(5, "Leo"))}
    v = _verdict(rules._vry_dusthana_pairs(facts), "vipareeta_6_8_link")
    assert v["fired"] is False and "one planet" in v["reason"]


# ------------------------------------------------------------- moon/sun yogas

def test_gajakesari_fires_in_mutual_kendra():
    facts = {"planet_positions": _pp(Moon=(1, "Aries"), Jupiter=(4, "Cancer"))}
    assert _fired(rules._detect_special(facts), "gajakesari_yoga") is True


def test_gajakesari_not_fired_off_kendra():
    facts = {"planet_positions": _pp(Moon=(1, "Aries"), Jupiter=(5, "Leo"))}
    assert _fired(rules._detect_special(facts), "gajakesari_yoga") is False


def test_vesi_fires_with_planet_in_2nd_from_sun():
    facts = {"planet_positions": _pp(Sun=(1, "Aries"), Mars=(2, "Taurus"))}
    assert _fired(rules._detect_jhora_set(facts), "vesi") is True


def test_anaphaa_fires_with_planet_in_12th_from_moon():
    # 12th sign from Aries is Pisces.
    facts = {"planet_positions": _pp(Moon=(1, "Aries"), Mars=(12, "Pisces"))}
    assert _fired(rules._detect_jhora_set(facts), "anaphaa") is True


def test_sunaphaa_and_anaphaa_are_distinct():
    facts = {"planet_positions": _pp(Moon=(1, "Aries"), Mars=(2, "Taurus"))}
    rows = rules._detect_jhora_set(facts)
    assert _fired(rows, "sunaphaa") is True
    assert _fired(rows, "anaphaa") is False


def test_nipuna_fires_when_sun_mercury_together():
    facts = {"planet_positions": _pp(Sun=(1, "Aries"), Mercury=(1, "Aries"))}
    assert _fired(rules._detect_jhora_set(facts), "nipuna") is True


# ------------------------------------------------------------- adhi + mercury benefic

def test_mercury_benefic_with_a_benefic_companion():
    # Mercury shares its house with Sun (malefic) and Jupiter (benefic).
    facts = {"planet_positions": _pp(Mercury=(5, "Leo"), Sun=(5, "Leo"), Jupiter=(5, "Leo"))}
    assert rules._is_benefic(facts, "Mercury") is True


def test_mercury_malefic_when_only_malefic_company():
    facts = {"planet_positions": _pp(Mercury=(5, "Leo"), Sun=(5, "Leo"))}
    assert rules._is_benefic(facts, "Mercury") is False


def test_mercury_benefic_when_alone():
    facts = {"planet_positions": _pp(Mercury=(5, "Leo"))}
    assert rules._is_benefic(facts, "Mercury") is True


def test_adhi_counts_widened_mercury_as_giver():
    # Moon Aquarius; 7th from Aquarius is Leo. Mercury+Jupiter in Leo -> both
    # benefic (Mercury via Jupiter's company) -> both Adhi givers.
    facts = {"planet_positions": _pp(Moon=(5, "Aquarius"), Mercury=(11, "Leo"),
                                     Jupiter=(11, "Leo"), Sun=(11, "Leo"))}
    v = _verdict(rules._detect_jhora_set(facts), "adhi")
    assert v["fired"] is True and "Mercury" in v["reason"]


# ------------------------------------------------------------- naabhasa sankhya

@pytest.mark.parametrize("signs,expected_id", [
    (["Aries", "Taurus", "Gemini", "Cancer", "Leo"], "naabhasa_paasa"),      # 5
    (["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo"], "naabhasa_daama"),  # 6
    (["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra"], "naabhasa_veenaa"),  # 7
])
def test_naabhasa_sankhya_names_by_distinct_sign_count(signs, expected_id):
    grahas = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn")
    pp = {g: {"house": 1, "sign": signs[i % len(signs)]} for i, g in enumerate(grahas)}
    v = rules._naabhasa_sankhya({"planet_positions": pp})
    assert v["id"] == expected_id and v["fired"] is True


# ------------------------------------------------------------- kalpadruma

def test_kalpadruma_fires_when_chain_well_placed():
    # lagna Aries -> lord Mars; Mars in Aries (house 1) -> dispositor Mars ...
    # every chain link resolves to Mars in a kendra, and its navamsa lord too.
    facts = {"ascendant_sign": "Aries",
             "planet_positions": _pp(Mars=(1, "Aries")),
             "navamsa": {"placements": {"Mars": {"sign": "Aries", "house": 1}}}}
    assert rules._kalpadruma(facts)["fired"] is True


# ------------------------------------------------------------- karakas

def test_raja_ak_pik_fires_when_together():
    facts = {"chara_karakas": {"AK": "Sun", "PiK": "Mercury"},
             "planet_positions": _pp(Sun=(1, "Aries"), Mercury=(1, "Aries"))}
    assert _fired(rules._karaka_rules(facts), "raja_ak_pik") is True


def test_raja_sambandha_ak_fires_when_amk_in_kona_from_ak():
    # PVR 11.8(6): AK Aries (0), AmK Leo (4) -> 5th from AK -> kona -> fires.
    facts = {"chara_karakas": {"AK": "Jupiter", "AmK": "Rahu"},
             "planet_positions": _pp(Jupiter=(1, "Aries"), Rahu=(5, "Leo"))}
    assert _fired(rules._karaka_rules(facts), "raja_sambandha_ak") is True


def test_raja_sambandha_lagna_fires_when_amk_in_trine_from_lagna():
    # PVR 11.8(5): AmK in the 5th house (a trine from lagna) fires even though
    # it is only the 2nd from AK (the AK rule does not fire) -- the Sulabh case.
    facts = {"chara_karakas": {"AK": "Sun", "AmK": "Jupiter"},
             "planet_positions": _pp(Sun=(4, "Pisces"), Jupiter=(5, "Aries"))}
    rows = rules._karaka_rules(facts)
    assert _fired(rows, "raja_sambandha_lagna") is True
    assert _fired(rows, "raja_sambandha_ak") is False


def test_raja_sambandha_both_not_fired():
    facts = {"chara_karakas": {"AK": "Jupiter", "AmK": "Rahu"},
             "planet_positions": _pp(Jupiter=(1, "Aries"), Rahu=(2, "Taurus"))}
    rows = rules._karaka_rules(facts)
    assert _fired(rows, "raja_sambandha_lagna") is False
    assert _fired(rows, "raja_sambandha_ak") is False


# ------------------------------------------------------------- yogada family

def test_yogada_gl_only():
    # Sun occupies both lagna and GL sign; no HL given.
    facts = {"ascendant_sign": "Aries", "ghati_lagna_sign": "Aries",
             "planet_positions": _pp(Sun=(1, "Aries"))}
    rows = rules._yogada(facts)
    assert _fired(rows, "yogada_gl_sun") is True


def test_yogada_hl_only():
    facts = {"ascendant_sign": "Aries", "hora_lagna_sign": "Aries",
             "planet_positions": _pp(Sun=(1, "Aries"))}
    assert _fired(rules._yogada(facts), "yogada_hl_sun") is True


def test_maha_yogada_when_linked_to_lagna_gl_and_hl():
    facts = {"ascendant_sign": "Aries", "ghati_lagna_sign": "Aries",
             "hora_lagna_sign": "Aries",
             "planet_positions": _pp(Sun=(1, "Aries"))}
    rows = rules._yogada(facts)
    assert _fired(rows, "maha_yogada_sun") is True
    # and it must NOT also emit the plain GL/HL rows for the same graha
    assert _verdict(rows, "yogada_gl_sun") is None
    assert _verdict(rows, "yogada_hl_sun") is None


# ------------------------------------------------------------- pancha mahapurusha

def test_sasa_fires_saturn_own_sign_in_kendra():
    facts = {"planet_positions": _pp(Saturn=(4, "Capricorn", "Own Sign"))}
    assert _fired(rules._pancha_mahapurusha(facts), "pmp_sasa") is True


def test_pmp_not_fired_when_not_in_kendra():
    facts = {"planet_positions": _pp(Saturn=(3, "Capricorn", "Own Sign"))}
    assert _fired(rules._pancha_mahapurusha(facts), "pmp_sasa") is False


def test_pmp_not_fired_when_debilitated():
    facts = {"planet_positions": _pp(Mars=(4, "Cancer", "Debilitated"))}
    assert _fired(rules._pancha_mahapurusha(facts), "pmp_ruchaka") is False


# ------------------------------------------------------------- neecha bhanga

def test_neecha_bhanga_fires_when_dispositor_exalted():
    # Sun debilitated in Libra; Libra's lord Venus is exalted.
    facts = {"planet_positions": _pp(Sun=(7, "Libra", "Debilitated"),
                                     Venus=(6, "Pisces", "Exalted")),
             "house_lords": _lords({7: ("Venus", "Libra", 6)})}
    v = _verdict(rules._detect_neecha(facts), "neecha_bhanga_sun")
    assert v["fired"] is True


def test_neecha_bhanga_new_exaltation_sign_lord_condition():
    # Sun debilitated in Libra. Dispositor Venus NOT exalted and off-kendra.
    # But Sun's exaltation sign is Aries, whose lord Mars sits in a kendra ->
    # the S133 exaltation-sign-lord condition alone cancels the debilitation.
    facts = {"planet_positions": _pp(Sun=(7, "Libra", "Debilitated"),
                                     Venus=(3, "Sagittarius"),
                                     Mars=(1, "Aries", "Own Sign"),
                                     Moon=(9, "Gemini")),
             "house_lords": _lords({7: ("Venus", "Libra", 3), 1: ("Mars", "Aries", 1)})}
    v = _verdict(rules._detect_neecha(facts), "neecha_bhanga_sun")
    assert v["fired"] is True
    assert any("exaltation_sign_lord_kendra=held" in e for e in v["evidence"])


def test_neecha_bhanga_all_conditions_fail():
    # Sun debilitated in Libra; Venus not exalted & off-kendra; Mars (exalt-sign
    # lord) off-kendra; no navamsa exaltation.
    facts = {"planet_positions": _pp(Sun=(7, "Libra", "Debilitated"),
                                     Venus=(3, "Sagittarius"),
                                     Mars=(3, "Gemini"),
                                     Moon=(1, "Aries")),
             "house_lords": _lords({7: ("Venus", "Libra", 3), 1: ("Mars", "Aries", 3)})}
    v = _verdict(rules._detect_neecha(facts), "neecha_bhanga_sun")
    assert v["fired"] is False


# ------------------------------------------------------------- detector contract

def test_detector_never_raises_on_garbage():
    assert detector.detect_yogas("not a dict").errors
    assert detector.detect_yogas({}).errors == []  # empty facts -> verdicts, no error


def test_detector_wraps_rows_into_verdicts():
    facts = {"planet_positions": _pp(Moon=(1, "Aries"), Jupiter=(4, "Cancer"))}
    report = detector.detect_yogas(facts)
    ids = {v.id for v in report.verdicts}
    assert "gajakesari_yoga" in ids
    assert any(v.fired for v in report.verdicts)


# ------------------------------------------------------------- S133 fixes

def test_yogakaraka_not_flagged_for_lagna_lord_owning_a_kendra():
    # One planet owns the 1st and the 4th (both quadrants; 1st is also a trine).
    # That is NOT a yogakaraka -- the quadrant must be 4/7/10 and the trine 5/9.
    facts = {"house_lords": _lords({1: ("Jupiter", "Sagittarius", 5),
                                    4: ("Jupiter", "Pisces", 5)}),
             "aspects": {"aspected_by": {}}}
    assert _verdict(rules._detect_raja(facts), "kendra_trikona_4_1") is None


def test_dharma_karmadhipati_fires_on_mutual_aspect():
    # 9th and 10th lords in different houses but aspecting each other.
    facts = {"house_lords": _lords({9: ("Mercury", "Virgo", 11),
                                    10: ("Moon", "Cancer", 5)}),
             "aspects": {"aspected_by": {"Mercury": ["Moon"], "Moon": ["Mercury"]}}}
    assert _fired(rules._detect_raja(facts), "dharma_karmadhipati") is True


def test_dharma_karmadhipati_fires_on_exchange():
    facts = {"house_lords": _lords({9: ("Mercury", "Virgo", 10),
                                    10: ("Moon", "Cancer", 9)}),
             "aspects": {"aspected_by": {}}}
    v = _verdict(rules._detect_raja(facts), "dharma_karmadhipati")
    assert v["fired"] is True and "exchange" in v["reason"]


def test_pmp_moolatrikona_via_degrees():
    # Saturn in Aquarius at 5deg (its moolatrikona range) in a kendra. The
    # fact-block dignity label would miss this; the degree path catches it.
    facts = {"planet_positions": {"Saturn": {"house": 4, "sign": "Aquarius"}},
             "planet_degrees": {"Saturn": 5.0}}
    v = _verdict(rules._pancha_mahapurusha(facts), "pmp_sasa")
    assert v["fired"] is True and "moolatrikona" in v["reason"].lower()


def test_mercury_malefic_by_aspect_only():
    # Mercury alone in its house but aspected only by Saturn (a malefic) -> malefic.
    facts = {"planet_positions": _pp(Mercury=(5, "Leo")),
             "aspects": {"aspected_by": {"Mercury": ["Saturn"]}}}
    assert rules._is_benefic(facts, "Mercury") is False
