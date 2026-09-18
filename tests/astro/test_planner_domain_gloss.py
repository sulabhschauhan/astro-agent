"""
Domain-vocabulary tests for agent/astro/planner.py's SYSTEM_PROMPT.

TWO THINGS ARE PINNED HERE.

(1) EVERY selectable domain carries a definition and, where it needs one, a
    scope guard. The 16 DOMAINS were bare token names, which let the planner
    pick the widest label on any question (CLAUDE.md Working Style #35,
    diagnostics/KNOWN_PATTERNS.md P-030).

(2) `technique_method` IS NOT SELECTABLE AT ALL (S136). It named the corpus's
    procedural chapters -- 45/100 units, 61.4% of corpus, 99.2% of
    HARD_CONTEXT_CEILING on one selection -- and, decisively, no end user asks
    how the system computes anything. Answering a methodology question would
    disclose how this project is configured, so such a question is REFUSED as
    out of scope. The tag stays in the corpus data; the DOMAIN is gone.

No live LLM call anywhere in this file -- static prompt-text assertions plus
stub-LLM fixtures, per project convention.
"""
import re

from agent.astro import planner as P

# Domains that legitimately need a narrowing guard. technique_method is NOT
# here because it no longer exists as a domain.
NARROW_GUARDED = {"planetary_nature"}


def _domain_line(domain: str) -> str:
    """The single SYSTEM_PROMPT line starting with `domain ->`, or '' if
    absent."""
    m = re.search(rf"^{re.escape(domain)} -> (.+)$", P.SYSTEM_PROMPT, re.MULTILINE)
    return m.group(1).strip() if m else ""


def _stub(obj):
    import json as _json

    def _call(question):
        return _json.dumps(obj)
    return _call


# ------------------------------------------- (a) vocabulary shape and glosses
def test_closed_vocabulary_is_fifteen_domains():
    assert len(P.DOMAINS) == 15
    assert len(set(P.DOMAINS)) == 15, "DOMAINS has a duplicate"


def test_every_domain_has_a_nonempty_gloss_on_its_own_line():
    for domain in P.DOMAINS:
        gloss = _domain_line(domain)
        assert gloss, f"{domain!r} has no ' -> definition' line in SYSTEM_PROMPT"


def test_widen_mandate_sentence_is_preserved_verbatim():
    """Glosses constrain what each term MEANS; they must not reverse the
    widen mandate."""
    assert ("If a question could plausibly touch several, LIST THEM ALL. "
            "Widening is correct; narrowing is a failure.") in P.SYSTEM_PROMPT
    assert 'A question that asks "when" always includes timing_dasha.' in P.SYSTEM_PROMPT


def test_planetary_nature_carries_an_only_guard():
    gloss = _domain_line("planetary_nature")
    assert "ONLY" in gloss
    assert "AS SUCH" in gloss


def test_life_subject_domains_carry_no_only_guard():
    """ONLY-scoping is reserved for the instrument domain; a life-subject
    domain must stay freely selectable per the widen mandate."""
    for domain in P.DOMAINS:
        if domain in NARROW_GUARDED:
            continue
        gloss = _domain_line(domain)
        assert "ONLY" not in gloss, (
            f"{domain!r} unexpectedly carries an ONLY guard: {gloss!r}")


def test_gloss_wording_agrees_with_fallback_keywords():
    """Prompt and deterministic fallback must not silently diverge."""
    for domain, keywords in P._FALLBACK_GLOSS.items():
        if domain in NARROW_GUARDED:
            continue
        gloss = _domain_line(domain).lower()
        assert any(kw in gloss for kw in keywords), (
            f"{domain!r} gloss {gloss!r} shares no keyword with "
            f"_FALLBACK_GLOSS{keywords!r}")


# ------------------------------- (b) technique_method is gone, on every path
def test_technique_method_is_not_a_selectable_domain():
    assert "technique_method" not in P.DOMAINS


def test_technique_method_is_not_offered_in_the_prompt_vocabulary():
    """It must not appear as a selectable ' -> ' entry. (The module's own
    provenance comments may still name it; those are not prompt text.)"""
    assert _domain_line("technique_method") == ""
    section1 = P.SYSTEM_PROMPT.split("2. HOUSES")[0]
    assert "technique_method" not in section1


def test_technique_method_is_not_in_the_deterministic_fallback():
    assert "technique_method" not in P._FALLBACK_GLOSS


def test_no_domain_keys_on_the_bare_word_how():
    """REGRESSION GUARD. _FALLBACK_GLOSS['technique_method'] led with "how",
    which matches ordinary readings ("how will my career go", "how is my
    marriage") -- so the deterministic fallback pulled 61.4% of the corpus on
    one of the commonest words in the language. Never reintroduce it."""
    for domain, keywords in P._FALLBACK_GLOSS.items():
        assert "how" not in keywords, (
            f"{domain!r} keys on the bare word 'how' -- see P-030")


def test_planner_rejects_a_plan_that_emits_technique_method():
    """Belt and braces: the closed-vocabulary validator now refuses it for
    free, so even a stale or jailbroken planner cannot reach those chapters."""
    obj = {"domains": ["technique_method"], "houses": [10],
           "whose_chart": "self", "time_scope": "none", "in_scope": True,
           "reasoning": "stale planner emitting a retired domain."}
    normalised, errors = P.validate_plan_object(obj)
    assert normalised is None
    assert any("outside closed vocabulary" in e for e in errors)


# ------------------------------------- (c) methodology questions are refused
def test_prompt_declares_methodology_questions_out_of_scope():
    assert "ALSO OUT OF SCOPE, ALWAYS" in P.SYSTEM_PROMPT
    assert "COMPUTES or DERIVES" in P.SYSTEM_PROMPT
    assert '"in_scope": false with empty "domains"' in P.SYSTEM_PROMPT


def test_empty_domains_is_legal_when_out_of_scope():
    """The refusal shape the prompt now asks for must survive validation.
    Before S136 it failed as 'domains must be a non-empty list' and fell
    through to fallback_plan, which would keyword-match a question the
    planner had just correctly declared out of scope."""
    obj = {"domains": [], "houses": [], "whose_chart": "self",
           "time_scope": "none", "in_scope": False,
           "reasoning": "asks how shadbala is computed -- methodology."}
    normalised, errors = P.validate_plan_object(obj)
    assert errors == []
    assert normalised is not None
    assert normalised["domains"] == []
    assert normalised["in_scope"] is False


def test_empty_domains_is_still_illegal_when_in_scope():
    """In scope but nothing to fetch is a contradiction, not a refusal."""
    obj = {"domains": [], "houses": [10], "whose_chart": "self",
           "time_scope": "none", "in_scope": True,
           "reasoning": "in scope but planned nothing."}
    normalised, errors = P.validate_plan_object(obj)
    assert normalised is None
    assert any("non-empty list when in_scope is true" in e for e in errors)


def test_methodology_question_plans_a_refusal_end_to_end():
    question = "How is shadbala calculated for a planet?"
    obj = {"domains": [], "houses": [], "whose_chart": "self",
           "time_scope": "none", "in_scope": False,
           "reasoning": "asks how shadbala is computed; methodology, not a reading."}
    plan = P.plan_question(question, llm=_stub(obj), log_path=None)
    assert plan.in_scope is False
    assert plan.domains == []


def test_which_varga_question_is_also_methodology():
    """'Which varga is used for career' asks about the machinery, even though
    it names a life area."""
    question = "Which varga is used for career, and how is it built?"
    obj = {"domains": [], "houses": [], "whose_chart": "self",
           "time_scope": "none", "in_scope": False,
           "reasoning": "asks which technique is used, not what the chart says."}
    plan = P.plan_question(question, llm=_stub(obj), log_path=None)
    assert plan.in_scope is False
    assert plan.domains == []


# ------------------------------- (d) readings that SOUND technical stay in
def test_yoga_reading_is_a_reading_not_a_method_question():
    question = "What do my chart's yogas say about my career?"
    obj = {"domains": ["career"], "houses": [10], "whose_chart": "self",
           "time_scope": "none", "in_scope": True,
           "reasoning": "asks what the yogas mean for career, a reading."}
    plan = P.plan_question(question, llm=_stub(obj), log_path=None)
    assert plan.in_scope is True
    assert plan.domains == ["career"]
    assert "ONLY" not in _domain_line("career")


def test_dasha_effect_question_widens_and_stays_in_scope():
    question = "How will my career be affected during my current Saturn dasha?"
    obj = {"domains": ["career", "timing_dasha"], "houses": [10],
           "whose_chart": "self", "time_scope": "present", "in_scope": True,
           "reasoning": "career during a dasha period; both domains apply."}
    plan = P.plan_question(question, llm=_stub(obj), log_path=None)
    assert plan.in_scope is True
    assert plan.domains == ["career", "timing_dasha"]
    assert "dasha" in _domain_line("timing_dasha").lower()
