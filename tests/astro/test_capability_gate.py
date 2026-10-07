"""Tests for agent/astro/capability_gate.py -- the Stage 1.5 honest-refusal gate.

HARDEST CASE FIRST: the tests that matter are the mixed-domain ones, where a
question is partly answerable and partly not. Pure "when will I marry" is easy;
"what does my chart say about marriage and when will it happen" is the case
that decides whether the product is honest or fabricates.
"""
from __future__ import annotations

import pytest

from agent.astro import capability_gate as CG
from agent.astro.planner import Plan


def _plan(domains, time_scope="none", in_scope=True):
    return Plan(
        question="q", domains=list(domains), houses=[1],
        whose_chart="self", time_scope=time_scope,
        in_scope=in_scope, reasoning="r",
    )


# ── the declaration must match reality ─────────────────────────────────────

def test_fact_block_provides_matches_what_pipeline_actually_renders():
    """FACT_BLOCK_PROVIDES is a promise about pipeline._fact_block. If the two
    drift, the gate stops protecting anything -- so pin them together."""
    from agent.astro import pipeline
    facts = {"lord_house_map": {h: 1 for h in range(1, 13)},
             "ascendant_sign": "Leo"}
    block = pipeline._fact_block(facts)

    assert "Ascendant sign:" in block, "ascendant_sign capability claimed but not rendered"
    assert block.count("its lord sits in house") == 12, \
        "lord_house_map capability claimed but 12 placements not rendered"
    # planet_positions: claimed since S129, so the block must render them when
    # the facts carry them -- and must NOT invent a line when they are absent.
    assert "is in house" not in block, "no planet facts supplied, yet planets rendered"
    with_planets = pipeline._fact_block(dict(facts, planet_positions={
        "Sun": {"house": 4, "sign": "Pisces"}, "Ketu": {"house": 9, "sign": "Leo"}}))
    assert "Sun is in house 4 (Pisces)." in with_planets
    assert "Ketu is in house 9 (Leo)." in with_planets
    # These facts carry no dasha_periods, so the guarded dasha section must not
    # render (S141): the block mentions dasha ONLY when the facts carry it, exactly
    # like yogas/navamsa. A dasha render for a dasha-less dict would break the
    # legacy-dict byte-identity pin below.
    assert "dasha" not in block.lower(), (
        "dasha rendered for a facts dict that carries no dasha_periods -- the "
        "dasha section must be guarded on presence")
    assert CG.FACT_BLOCK_PROVIDES == frozenset(
        {"ascendant_sign", "lord_house_map", "planet_positions", "house_lords",
         "aspects", "dignity", "navamsa", "yogas", "dasha_periods", "transits", "shadbala", "ashtakavarga", "jaimini", "divisional",
         "muhurta", "lucky_unlucky",
         "kp_seventh_cusp_sub_lord", "kp_planet_significations"})


def test_dasha_capability_is_rendered_when_the_facts_carry_it():
    """The S141 dasha fact class: rendered when chart_facts carries it, absent
    otherwise, and declared in FACT_BLOCK_PROVIDES (the growth-contract pin).
    Pratyantar is NOT a key here -- it is suppressed in chart_facts._read_dasha,
    so the block can never surface it."""
    from agent.astro import pipeline
    facts = {"lord_house_map": {h: 1 for h in range(1, 13)},
             "ascendant_sign": "Leo"}
    assert "Vimshottari dasha timeline" not in pipeline._fact_block(facts)
    with_dasha = pipeline._fact_block(dict(facts, dasha_periods={
        "mahadasha": {"lord": "Ketu", "start": "1 Aug 2025", "end": "1 Aug 2032"},
        "antardasha": {"lord": "Venus", "start": "29 Dec 2025", "end": "28 Feb 2027"},
        "mahadasha_tree": [
            {"mahadasha": {"lord": "Mercury", "start": "1 Aug 2008", "end": "1 Aug 2025"},
             "antardashas": [{"lord": "Sun", "start": "28 Oct 2014", "end": "4 Sep 2015"}],
             "phase": "past"},
            {"mahadasha": {"lord": "Ketu", "start": "1 Aug 2025", "end": "1 Aug 2032"},
             "antardashas": [{"lord": "Venus", "start": "29 Dec 2025", "end": "28 Feb 2027"}],
             "phase": "current"}],
        "drift_note": "approximate; +/-37 days"}))
    # the COMPLETE tree (gap #2): past MD + its sub-periods, the current MD tagged,
    # and the running sub-period marked -- every date the model needs, so it never
    # computes one.
    assert "Mercury major period (1 Aug 2008 to 1 Aug 2025) [past]" in with_dasha
    assert "Sun sub-period (28 Oct 2014 to 4 Sep 2015)" in with_dasha   # the once-fabricated AD
    assert "Ketu major period (1 Aug 2025 to 1 Aug 2032) [CURRENT]" in with_dasha
    assert "Venus sub-period (29 Dec 2025 to 28 Feb 2027)   <- the sub-period running now" in with_dasha
    assert "do not compute or estimate any period yourself" in with_dasha
    assert "+/-37 days" in with_dasha                                  # drift hedge stated
    assert "dasha_periods" in CG.FACT_BLOCK_PROVIDES


def test_lucky_unlucky_capability_is_rendered_when_the_facts_carry_it():
    """The S147 lucky/unlucky fact class: rendered when chart_facts carries it,
    absent otherwise, and declared in FACT_BLOCK_PROVIDES (the growth-contract
    pin). The verdict carries its ruling planet + houses so the interpreter can
    GROUND the day, not assert it."""
    from agent.astro import pipeline
    facts = {"lord_house_map": {h: 1 for h in range(1, 13)},
             "ascendant_sign": "Leo"}
    assert "Lucky / unlucky weekdays" not in pipeline._fact_block(facts)
    with_lucky = pipeline._fact_block(dict(facts, lucky_unlucky={
        "weekdays": {
            "Thursday": {"lord": "Jupiter", "houses_ruled": [1, 4], "verdict": "favourable"},
            "Friday": {"lord": "Venus", "houses_ruled": [6, 11], "verdict": "avoid"}},
        "favourable_days": ["Thursday"], "avoid_days": ["Friday"]}))
    assert "Lucky / unlucky weekdays" in with_lucky
    assert "Thursday (ruled by Jupiter, lord of house(s) 1, 4)" in with_lucky
    assert "Friday (ruled by Venus, lord of house(s) 6, 11)" in with_lucky
    assert "lucky_unlucky" in CG.FACT_BLOCK_PROVIDES


def test_yogas_capability_is_rendered_when_the_facts_carry_it():
    """The S133 yoga fact class: rendered when chart_facts carries it, absent
    otherwise, and declared in FACT_BLOCK_PROVIDES (the growth-contract pin)."""
    from agent.astro import pipeline
    facts = {"lord_house_map": {h: 1 for h in range(1, 13)},
             "ascendant_sign": "Leo"}
    assert "Yogas PRESENT" not in pipeline._fact_block(facts)
    with_yogas = pipeline._fact_block(dict(facts, yogas={
        "fired": [{"id": "harsha_yoga", "name": "Harsha Yoga",
                   "reason": "the 6th lord is in the 6th"}],
        "ruled_out": [{"id": "gajakesari_yoga", "name": "Gajakesari Yoga",
                       "reason": "not in a mutual kendra"}]}))
    assert "Yogas PRESENT in the chart" in with_yogas
    assert "Harsha Yoga" in with_yogas
    assert "Yogas CHECKED and NOT present" in with_yogas
    assert "yogas" in CG.FACT_BLOCK_PROVIDES


def test_navamsa_is_restated_and_rendered_when_the_caller_supplies_it():
    """D9 has been oracle-clean since S20 and unwired ever since. The adapter
    must restate a caller-supplied chart and never compute one itself."""
    from agent.astro import chart_facts, pipeline
    chart = {
        "house_lord_mapping": [{"house": h, "sign": f"S{h}", "lord": f"L{h}",
                                "lord_in_house": h} for h in range(1, 13)],
        "lagna_chart": {"ascendant": "Sagittarius"},
        "planetary_positions": {"Mercury": {"house": 4, "sign": "Pisces",
                                            "dignity": "Debilitated"}},
        "navamsa": {"d9_lagna_sign": "Gemini",
                    "placements": {
                        "Mercury": {"sign": "Virgo", "house": 4,
                                    "dignity": "Exalted"},
                        "Venus": {"sign": "Leo", "house": 3,
                                  "dignity": "Friendly"}}},
    }
    facts = chart_facts.build_chart_facts(chart)
    nav = facts["navamsa"]["placements"]
    assert nav["Mercury"] == {"sign": "Virgo", "house": 4, "dignity": "Exalted"}
    # the contested tail is filtered in D9 exactly as it is in D1
    assert "dignity" not in nav["Venus"]

    block = pipeline._fact_block(facts)
    assert "In the Navamsa (D9) divisional chart, whose ascendant is Gemini:" in block
    # the remaining Neecha Bhanga route, readable in one line
    assert "Mercury is in Virgo (D9 house 4) -- exalted there" in block


def test_no_navamsa_key_when_the_caller_supplies_none():
    """Composition is the caller's job. Absent D9 is an honest absence, not an
    error, and must not leave an empty key behind."""
    from agent.astro import chart_facts, pipeline
    chart = {
        "house_lord_mapping": [{"house": h, "sign": f"S{h}", "lord": f"L{h}",
                                "lord_in_house": h} for h in range(1, 13)],
        "lagna_chart": {"ascendant": "Sagittarius"},
    }
    facts = chart_facts.build_chart_facts(chart)
    assert "navamsa" not in facts
    assert "Navamsa" not in pipeline._fact_block(facts)


def test_only_the_uncontested_dignity_tiers_are_restated():
    """S130 split. Exalted/Debilitated/Own Sign come from fixed tables locked in
    S21 from PVR Table 6. Friendly/Inimical/Neutral come from _FRIENDS, which is
    the genuinely contested part -- those must never reach the block."""
    from agent.astro import chart_facts
    chart = {
        "house_lord_mapping": [{"house": h, "sign": f"S{h}", "lord": f"L{h}",
                                "lord_in_house": h} for h in range(1, 13)],
        "lagna_chart": {"ascendant": "Sagittarius"},
        "planetary_positions": {
            "Sun": {"house": 4, "sign": "Pisces", "dignity": "Debilitated"},
            "Moon": {"house": 12, "sign": "Scorpio", "dignity": "Debilitated"},
            "Mars": {"house": 2, "sign": "Capricorn", "dignity": "Exalted"},
            "Mercury": {"house": 4, "sign": "Pisces", "dignity": "Friendly"},
            "Jupiter": {"house": 5, "sign": "Aries", "dignity": "Inimical"},
            "Venus": {"house": 6, "sign": "Taurus", "dignity": "Own Sign"},
            "Saturn": {"house": 1, "sign": "Sagittarius", "dignity": "Neutral"},
        },
    }
    pos = chart_facts.build_chart_facts(chart)["planet_positions"]
    assert pos["Moon"]["dignity"] == "Debilitated"
    assert pos["Mars"]["dignity"] == "Exalted"
    assert pos["Venus"]["dignity"] == "Own Sign"
    for contested in ("Mercury", "Jupiter", "Saturn"):
        assert "dignity" not in pos[contested], (
            f"{contested} carries a contested friendship tier into the block")


def test_neecha_bhanga_is_readable_off_the_block_without_inference():
    """The whole point of the S130 dignity + dispositor work: a debilitated
    planet and its dispositor's standing must be one read, not a cross-block
    lookup. Sulabh's chart: Moon debilitated in Scorpio, dispositor Mars exalted
    in Capricorn -- the textbook cancellation."""
    from agent.astro import pipeline
    facts = {
        "lord_house_map": {h: h for h in range(1, 13)},
        "ascendant_sign": "Sagittarius",
        "house_lords": {12: {"lord": "Mars", "sign": "Scorpio", "in_house": 2},
                        2: {"lord": "Saturn", "sign": "Capricorn", "in_house": 1}},
        "planet_positions": {
            "Moon": {"house": 12, "sign": "Scorpio", "dignity": "Debilitated"},
            "Mars": {"house": 2, "sign": "Capricorn", "dignity": "Exalted"}},
    }
    block = pipeline._fact_block(facts)
    assert "Moon is in house 12 (Scorpio) -- debilitated there." in block
    assert "Mars is in house 2 (Capricorn) -- exalted there." in block
    assert ("Moon is in Scorpio, whose lord is Mars; Mars is in Capricorn "
            "-- exalted there") in block


def test_aspects_capability_is_rendered_when_the_facts_carry_it():
    """Pin all three restated aspect fields plus the MUTUAL grouping. Mutual is
    the load-bearing one: a one-way aspect and a mutual one carry different
    doctrinal weight, and a benchmark answer for this chart rated a one-way
    aspect as a certain raja yoga by not distinguishing them."""
    from agent.astro import pipeline
    facts = {"lord_house_map": {h: h for h in range(1, 13)},
             "ascendant_sign": "Sagittarius",
             "aspects": {
                 "conjunctions": ["Sun conjunct Mercury (4th house)"],
                 "aspects_by_planet": {"Mars": [5, 8, 9], "Jupiter": [1, 9, 11]},
                 "aspected_by": {"Jupiter": ["Mars"], "Moon": ["Venus"],
                                 "Saturn": ["Ketu"], "Ketu": ["Saturn"]}}}
    block = pipeline._fact_block(facts)
    assert "Sun conjunct Mercury (4th house)" in block
    assert "Mars aspects houses 5, 8, 9" in block
    # the affliction check the benchmark missed by eye
    assert "Moon is aspected by Venus" in block
    # Mars->Jupiter is ONE-WAY here, so it must NOT appear as mutual
    assert "Planets that aspect EACH OTHER" in block
    assert "  Ketu and Saturn" in block
    assert "  Jupiter and Mars" not in block


def test_fact_block_stays_byte_identical_for_a_legacy_facts_dict():
    """Every S130 key is additive. A pre-S130 chart_facts dict must render
    exactly as it did, or replaying an old capture reports false diffs."""
    from agent.astro import pipeline
    legacy = {"lord_house_map": {h: ((h + 3) % 12) + 1 for h in range(1, 13)},
              "ascendant_sign": "Sagittarius"}
    block = pipeline._fact_block(legacy)
    assert "its lord is" not in block
    assert "Aspects and conjunctions" not in block
    assert "share a house" not in block
    assert block.count("its lord sits in house") == 12


def test_house_lords_capability_is_rendered_when_the_facts_carry_it():
    """house_lords claims TWO things: each house lord's own planet name, and
    the groupings that follow. Pin both -- the grouping is the half that exists
    to stop the Interpreter bridging twelve separate lines by itself."""
    from agent.astro import pipeline
    facts = {"lord_house_map": {1: 5, 4: 5, 9: 4, 10: 4,
                                **{h: h for h in (2, 3, 5, 6, 7, 8, 11, 12)}},
             "ascendant_sign": "Sagittarius",
             "house_lords": {1: {"lord": "Jupiter", "sign": "Sagittarius", "in_house": 5},
                             4: {"lord": "Jupiter", "sign": "Pisces", "in_house": 5},
                             9: {"lord": "Sun", "sign": "Leo", "in_house": 4},
                             10: {"lord": "Mercury", "sign": "Virgo", "in_house": 4}}}
    block = pipeline._fact_block(facts)
    assert "its lord is Sun" in block
    assert "House 9 (Leo)" in block
    # the Dharma-Karmadhipati co-location, STATED rather than left to infer
    assert "the lords of houses 9th, 10th are all in house 4" in block
    # multi-rulership -- the benchmark answer itself missed Venus ruling 6 AND 11
    assert "Jupiter rules houses 1 and 4" in block


def test_every_requirement_names_a_capability_the_block_does_not_yet_have():
    for req in CG.REQUIREMENTS:
        assert req.needs not in CG.FACT_BLOCK_PROVIDES, (
            f"requirement {req.id} guards {req.needs!r}, which the fact block "
            "already provides -- it can never fire; delete it or fix the key"
        )
        assert req.domains or req.time_scopes, f"{req.id} can never trigger"
        assert req.user_message.strip(), f"{req.id} has no user message"


# ── the answerable case: gate must stay out of the way ─────────────────────

@pytest.mark.parametrize("domains", [
    ["career"], ["marriage"], ["health", "longevity"],
    ["wealth", "property", "children"], ["planetary_nature"],
])
def test_non_timing_questions_pass_through_untouched(domains):
    plan = _plan(domains)
    v = CG.assess(plan)
    assert v.refuse_outright is False
    assert v.declined == []
    assert v.dropped_domains == []
    assert v.plan is plan, "an unaffected plan must be passed through, not copied"


# ── the cases that FLIPPED at S141: timing is now answerable ───────────────
# Before S141 these were DECLINED because the fact block carried no dates. Now
# dasha_periods is in the block and REQUIREMENTS is empty, so the gate declines
# nothing -- every timing case passes through. Rewritten from the pre-dasha
# contract; the pre-dasha assertions are what this change deliberately inverts.

def test_marriage_plus_timing_now_answers_both():
    """'What does my chart say about marriage, and when?' -- both halves answer
    now that the dasha timeline is in the fact block (S141). Was: timing dropped,
    marriage kept, one decline message."""
    plan = _plan(["marriage", "timing_dasha"], time_scope="future")
    v = CG.assess(plan)

    assert v.refuse_outright is False
    assert v.declined == []
    assert v.dropped_domains == []
    assert v.plan is plan, "an answerable plan passes through untouched, not copied"
    assert v.plan.domains == ["marriage", "timing_dasha"]


def test_timing_only_question_now_answers():
    """'When will I marry?' planned as timing alone -- answerable now, not refused."""
    plan = _plan(["timing_dasha"], time_scope="future")
    v = CG.assess(plan)

    assert v.refuse_outright is False
    assert v.declined == []
    assert v.dropped_domains == []
    assert v.plan.domains == ["timing_dasha"]


def test_future_time_scope_no_longer_triggers_a_decline():
    """'How will my career go next year?' -- a future scope no longer draws a
    'we have no dates' decline (S141): dates ARE available now."""
    plan = _plan(["career"], time_scope="future")
    v = CG.assess(plan)

    assert v.declined == []
    assert v.refuse_outright is False
    assert v.plan.domains == ["career"]
    assert v.dropped_domains == []


def test_specific_period_time_scope_no_longer_triggers():
    v = CG.assess(_plan(["wealth"], time_scope="specific_period"))
    assert v.declined == []
    assert v.refuse_outright is False


@pytest.mark.parametrize("scope", ["none", "past", "present"])
def test_non_forward_time_scopes_do_not_trigger(scope):
    v = CG.assess(_plan(["career"], time_scope=scope))
    assert v.declined == []
    assert v.refuse_outright is False


# ── growth path: a widened fact block silences the gate automatically ──────

def test_a_provided_capability_is_never_declined():
    """The growth-path property, now the live one (S141): a fact class the block
    provides is never declined. dasha_periods landed for real, so this holds with
    the default provides too, not just a simulated-widened set."""
    widened = CG.FACT_BLOCK_PROVIDES | {"dasha_periods"}
    plan = _plan(["marriage", "timing_dasha"], time_scope="future")

    v = CG.assess(plan, provides=widened)

    assert v.declined == []
    assert v.refuse_outright is False
    assert v.plan is plan
    assert v.plan.domains == ["marriage", "timing_dasha"]


# ── structural guards ──────────────────────────────────────────────────────

def test_empty_domains_with_forward_scope_passes_the_gate_now():
    """S141: with REQUIREMENTS empty the gate declines nothing, so it no longer
    refuses an empty-domains plan -- that refusal now belongs to build_from_plan
    ('no domains planned'), which still fires downstream. The gate's job is only
    to narrow to what the block supports, and an empty plan needs no narrowing."""
    v = CG.assess(_plan([], time_scope="future"))
    assert v.refuse_outright is False
    assert v.declined == []


def test_non_plan_input_raises_loudly():
    with pytest.raises(TypeError, match="planner.Plan"):
        CG.assess({"domains": ["career"], "time_scope": "none"})


def test_verdict_carries_gate_version():
    v = CG.assess(_plan(["career"]))
    assert v.gate_version == CG.CAPABILITY_GATE_VERSION


def test_requirement_ids_are_unique():
    ids = [r.id for r in CG.REQUIREMENTS]
    assert len(ids) == len(set(ids))


def test_gate_makes_no_llm_call():
    """Deterministic by construction -- no transport import anywhere."""
    import ast
    import inspect
    tree = ast.parse(inspect.getsource(CG))
    names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names += [a.name for a in node.names]
        elif isinstance(node, ast.ImportFrom):
            names.append(node.module or "")
    for n in names:
        assert "openai" not in n.lower(), "the capability gate must never call a model"


# ── muhurta (S147): the horizon clarification + the fact render ─────────────

def _muhurta_plan(domains, *, muhurta, horizon):
    return Plan(
        question="q", domains=list(domains), houses=[1], whose_chart="self",
        time_scope="none", in_scope=bool(domains), reasoning="r",
        muhurta=muhurta, muhurta_horizon=horizon,
    )


def test_muhurta_without_horizon_passes_clean_now():
    """S147: muhurta defaults to a 2-year scan from now in the pipeline, so the
    gate no longer asks for a horizon -- a muhurta question passes undeclined."""
    v = CG.assess(_muhurta_plan(["marriage"], muhurta=True, horizon=None))
    assert v.declined == [] and v.refuse_outright is False
    assert "marriage" in v.plan.domains


def test_muhurta_only_without_horizon_also_passes_clean():
    v = CG.assess(_muhurta_plan([], muhurta=True, horizon=None))
    assert v.declined == [] and v.refuse_outright is False


def test_muhurta_flag_with_horizon_passes_the_gate():
    v = CG.assess(_muhurta_plan(["marriage"], muhurta=True,
                                horizon={"mode": "days", "value": 180}))
    assert v.declined == [] and v.refuse_outright is False


def test_plan_without_muhurta_attrs_is_unaffected():
    """A pre-S147 plan (no muhurta attributes) reads False/None and never
    triggers the clarification."""
    v = CG.assess(_plan(["career"]))
    assert all(i != "muhurta_needs_horizon" for i, _ in v.declined)


def test_muhurta_facts_render_when_present():
    from agent.astro import pipeline
    rec_best = {"start": "2026-11-12 03:00 UT", "end": "2026-11-12 09:00 UT",
                "tier": "TIER_1", "favorable_count": 2, "tithi": "Sukla Panchami",
                "yoga": "Siddha", "karana": "Bava", "warnings": ()}
    rec_early = {"start": "2026-10-20 06:00 UT", "end": "2026-10-20 12:00 UT",
                 "tier": "TIER_2", "favorable_count": 1, "tithi": "Sukla Dwitiya",
                 "yoga": "Shubha", "karana": "Taitila",
                 "warnings": ("Janma Tara",)}
    facts = {"lord_house_map": {h: 1 for h in range(1, 13)},
             "ascendant_sign": "Leo",
             "muhurta": {"searched": {"start": "2026-10-04 00:00 UT",
                                      "end": "2027-04-02 00:00 UT",
                                      "span_days": 180, "mode": "days",
                                      "capped": False},
                         "windows": [rec_best, rec_early],
                         "best": rec_best, "earliest_good": rec_early,
                         "none_found": False}}
    block = pipeline._fact_block(facts)
    assert "Muhurta (electional timing)" in block
    assert "BEST window:" in block and "2026-11-12 03:00 UT" in block
    assert "EARLIEST good window:" in block and "2026-10-20 06:00 UT" in block
    assert "Janma Tara" in block            # caution limb surfaced


def test_muhurta_none_found_renders_an_honest_message():
    from agent.astro import pipeline
    facts = {"lord_house_map": {h: 1 for h in range(1, 13)},
             "ascendant_sign": "Leo",
             "muhurta": {"searched": {"start": "2026-10-04 00:00 UT",
                                      "end": "2026-11-03 00:00 UT",
                                      "span_days": 30, "mode": "days",
                                      "capped": False},
                         "windows": [], "best": None, "earliest_good": None,
                         "none_found": True}}
    block = pipeline._fact_block(facts)
    assert "No auspicious window" in block
    assert "BEST window:" not in block


def test_muhurta_absent_renders_nothing():
    from agent.astro import pipeline
    facts = {"lord_house_map": {h: 1 for h in range(1, 13)},
             "ascendant_sign": "Leo"}
    assert "Muhurta (electional timing)" not in pipeline._fact_block(facts)
