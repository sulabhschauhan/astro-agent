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
    # Nothing else is in the block. If a future edit adds dasha lines here,
    # this assertion fires and the author must add the capability key too.
    assert "dasha" not in block.lower(), (
        "the fact block now mentions dasha -- add the matching key to "
        "FACT_BLOCK_PROVIDES in the same change, or the gate will keep "
        "declining questions it could now answer"
    )
    assert CG.FACT_BLOCK_PROVIDES == frozenset(
        {"ascendant_sign", "lord_house_map", "planet_positions", "house_lords",
         "aspects", "dignity", "navamsa", "yogas"})


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


# ── the hard cases: mixed answerable / unanswerable ────────────────────────

def test_marriage_plus_timing_answers_marriage_and_declines_the_timing():
    """'What does my chart say about marriage, and when?' -- the honest middle."""
    plan = _plan(["marriage", "timing_dasha"], time_scope="future")
    v = CG.assess(plan)

    assert v.refuse_outright is False
    assert v.dropped_domains == ["timing_dasha"]
    assert v.plan.domains == ["marriage"]
    assert len(v.messages) == 1
    assert "when" in v.messages[0].lower()
    # the original plan is untouched -- the decision log must stay truthful
    assert plan.domains == ["marriage", "timing_dasha"]


def test_timing_only_question_refuses_outright():
    """'When will I marry?' planned as timing alone -- nothing left to answer."""
    plan = _plan(["timing_dasha"], time_scope="future")
    v = CG.assess(plan)

    assert v.refuse_outright is True
    assert v.dropped_domains == ["timing_dasha"]
    assert v.plan.domains == []
    assert len(v.messages) == 1


def test_future_time_scope_alone_triggers_even_without_the_timing_domain():
    """'How will my career go next year?' may plan only `career` -- but it is
    still asking for a date, and we have no dates."""
    plan = _plan(["career"], time_scope="future")
    v = CG.assess(plan)

    assert v.declined, "a future-scoped question must be told we cannot date it"
    # career itself survives -- the doctrine is still answerable
    assert v.refuse_outright is False
    assert v.plan.domains == ["career"]
    assert v.dropped_domains == []


def test_specific_period_time_scope_also_triggers():
    v = CG.assess(_plan(["wealth"], time_scope="specific_period"))
    assert v.declined
    assert v.refuse_outright is False


@pytest.mark.parametrize("scope", ["none", "past", "present"])
def test_non_forward_time_scopes_do_not_trigger(scope):
    v = CG.assess(_plan(["career"], time_scope=scope))
    assert v.declined == []
    assert v.refuse_outright is False


# ── growth path: a widened fact block silences the gate automatically ──────

def test_widened_fact_block_makes_the_timing_requirement_inert():
    """When vimshottari lands and the block carries dasha_periods, the same
    question must sail through with NO code change beyond the capability key."""
    widened = CG.FACT_BLOCK_PROVIDES | {"dasha_periods"}
    plan = _plan(["marriage", "timing_dasha"], time_scope="future")

    v = CG.assess(plan, provides=widened)

    assert v.declined == []
    assert v.refuse_outright is False
    assert v.plan is plan
    assert v.plan.domains == ["marriage", "timing_dasha"]


# ── structural guards ──────────────────────────────────────────────────────

def test_empty_domains_with_forward_scope_refuses_rather_than_proceeding():
    v = CG.assess(_plan([], time_scope="future"))
    assert v.refuse_outright is True


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
