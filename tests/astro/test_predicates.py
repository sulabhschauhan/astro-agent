"""Tests for agent/astro/predicates.py.

Three things matter here, in this order:
  (1) CONTRADICTED is reachable ONLY from a present, disagreeing fact. Every
      absence, malformation and unknown type must land UNEVALUABLE -- a wrong
      drop silences a true claim invisibly (S124, S125).
  (2) The vocabulary is closed, glossed and scope-guarded (Working Style #35).
  (3) No degree-level predicate exists (S130: tables are sign-level, meta values
      are rounded).
"""
from __future__ import annotations

import pytest

from agent.astro import predicates as P


# A fact block in the EXACT shape frontend/app.py composes and
# diagnostics/qa_capture writes -- taken from 20260918T193426Z.md, not invented.
FACTS = {
    "ascendant_sign": "Sagittarius",
    "lord_house_map": {1: 5, 2: 1, 6: 6, 9: 4, 10: 4},
    "house_lords": {
        1: {"lord": "Jupiter", "sign": "Sagittarius", "in_house": 5},
        10: {"lord": "Mercury", "sign": "Virgo", "in_house": 4},
    },
    "planet_positions": {
        "Sun": {"house": 4, "sign": "Pisces"},
        "Moon": {"house": 12, "sign": "Scorpio", "dignity": "Debilitated"},
        "Mars": {"house": 2, "sign": "Capricorn", "dignity": "Exalted"},
        "Mercury": {"house": 4, "sign": "Pisces", "dignity": "Debilitated"},
        "Jupiter": {"house": 5, "sign": "Aries"},
    },
    "aspects": {
        "conjunctions": ["Sun conjunct Mercury (4th house)"],
        "aspects_by_planet": {"Sun": [10], "Mars": [5, 8, 9]},
        "aspected_by": {"Jupiter": ["Ketu", "Mars"], "Mars": ["Jupiter"],
                        "Venus": ["Moon"]},
    },
    "navamsa": {
        "placements": {
            "Mercury": {"sign": "Virgo", "house": 12, "dignity": "Exalted"},
            "Sun": {"sign": "Capricorn", "house": 4},
        },
        "d9_lagna_sign": "Libra",
    },
    "yogas": {
        "fired": [{"id": "adhi", "name": "Adhi"},
                  {"id": "vesi", "name": "Vesi"},
                  {"id": "harsha_yoga", "name": "Harsha Yoga"}],
        "ruled_out": [{"id": "gajakesari_yoga", "name": "Gajakesari Yoga"},
                      {"id": "sarala_yoga", "name": "Sarala Yoga"}],
        "errors": [],
    },
}


def v(pred):
    return P.evaluate(pred, FACTS)[0]


# ── the vocabulary is closed, glossed and guarded (Working Style #35) ───────

def test_every_predicate_carries_a_gloss_and_a_scope_guard():
    """P-030: bare token names handed to an LLM is the defect. Mechanical."""
    for name, (fn, fact_class, gloss, guard) in P.PREDICATES.items():
        assert callable(fn), name
        assert isinstance(gloss, str) and len(gloss) > 10, f"{name} gloss too thin"
        assert isinstance(guard, str) and len(guard) > 10, f"{name} guard too thin"


def test_every_predicate_reads_a_declared_fact_class():
    """The registry replaces the three-register asymmetry: a predicate must name
    the FACT_BLOCK_PROVIDES key it reads, or be the escape hatch."""
    from agent.astro.capability_gate import FACT_BLOCK_PROVIDES
    for name, cls in P.PREDICATE_FACT_CLASS.items():
        if name == "unfittable":
            assert cls == ""
            continue
        assert cls in FACT_BLOCK_PROVIDES, f"{name} reads undeclared class {cls!r}"


def test_no_degree_level_predicate_exists():
    """Ephemeris Auditor, S130 accepted gap: exaltation tables carry SIGNS and
    meta.jd_ut / asc_lon_sidereal are rounded. A degree predicate would look
    evaluable and be false at the precision it implies."""
    for name in P.PREDICATES:
        assert "degree" not in name and "deg_" not in name, name


def test_unknown_predicate_type_is_unevaluable_never_contradicted():
    assert v({"type": "planet_nakshatra", "graha": "Sun"}) == P.UNEVALUABLE
    assert v({"type": None}) == P.UNEVALUABLE
    assert P.evaluate("not a dict", FACTS)[0] == P.UNEVALUABLE


# ── each evaluator: satisfied / contradicted / absent ──────────────────────

@pytest.mark.parametrize("pred,expected", [
    ({"type": "lord_in_house", "lord_of": 10, "house": 4}, P.SATISFIED),
    ({"type": "lord_in_house", "lord_of": 10, "house": 7}, P.CONTRADICTED),
    ({"type": "lord_in_house", "lord_of": 3, "house": 1}, P.UNEVALUABLE),
    ({"type": "house_lord_is", "house": 10, "graha": "Mercury"}, P.SATISFIED),
    ({"type": "house_lord_is", "house": 10, "graha": "Saturn"}, P.CONTRADICTED),
    ({"type": "planet_in_house", "graha": "Jupiter", "house": 5}, P.SATISFIED),
    ({"type": "planet_in_house", "graha": "Jupiter", "house": 1}, P.CONTRADICTED),
    ({"type": "planet_in_sign", "graha": "Mars", "sign": "Capricorn"}, P.SATISFIED),
    ({"type": "planet_in_sign", "graha": "Mars", "sign": "Aries"}, P.CONTRADICTED),
    ({"type": "planet_dignity", "graha": "Mars", "dignity": "Exalted"}, P.SATISFIED),
    ({"type": "planet_dignity", "graha": "Mars", "dignity": "Debilitated"}, P.CONTRADICTED),
    # Jupiter holds no head dignity -> a real negative, the planet IS present.
    ({"type": "planet_dignity", "graha": "Jupiter", "dignity": "Exalted"}, P.CONTRADICTED),
    ({"type": "conjunction", "grahas": ["Sun", "Mercury"]}, P.SATISFIED),
    ({"type": "conjunction", "grahas": ["Mercury", "Sun"]}, P.SATISFIED),  # order-free
    ({"type": "conjunction", "grahas": ["Sun", "Saturn"]}, P.CONTRADICTED),
    ({"type": "aspects_house", "graha": "Sun", "house": 10}, P.SATISFIED),
    ({"type": "aspects_house", "graha": "Sun", "house": 3}, P.CONTRADICTED),
    ({"type": "aspects_house", "graha": "Ketu", "house": 3}, P.UNEVALUABLE),
    ({"type": "aspected_by", "graha": "Jupiter", "by": "Ketu"}, P.SATISFIED),
    ({"type": "aspected_by", "graha": "Jupiter", "by": "Sun"}, P.CONTRADICTED),
    ({"type": "mutual_aspect", "grahas": ["Jupiter", "Mars"]}, P.SATISFIED),
    ({"type": "mutual_aspect", "grahas": ["Venus", "Moon"]}, P.CONTRADICTED),
    ({"type": "navamsa_sign", "graha": "Mercury", "sign": "Virgo"}, P.SATISFIED),
    ({"type": "navamsa_sign", "graha": "Mercury", "sign": "Pisces"}, P.CONTRADICTED),
    ({"type": "navamsa_dignity", "graha": "Mercury", "dignity": "Exalted"}, P.SATISFIED),
    ({"type": "navamsa_sign", "graha": "Saturn", "sign": "Leo"}, P.UNEVALUABLE),
    ({"type": "ascendant_is", "sign": "Sagittarius"}, P.SATISFIED),
    ({"type": "ascendant_is", "sign": "Leo"}, P.CONTRADICTED),
])
def test_evaluator_verdicts(pred, expected):
    assert v(pred) == expected


# ── the case that motivated the module ─────────────────────────────────────

@pytest.mark.parametrize("yid,expected", [
    ("adhi", P.SATISFIED),
    ("vesi", P.SATISFIED),
    ("harsha_yoga", P.SATISFIED),
    ("gajakesari_yoga", P.CONTRADICTED),
    ("sarala_yoga", P.CONTRADICTED),
])
def test_yoga_fired_reads_the_detectors_own_verdict(yid, expected):
    """These five were demoted live as 'unverified' while the detector had
    already computed them. That is the defect this module removes."""
    assert v({"type": "yoga_fired", "yoga_id": yid}) == expected


def test_a_yoga_outside_the_catalogue_is_coverage_not_refutation():
    """The wider-BPHS-set gap must read as 'we do not compute this', never as
    'this does not apply' -- the difference between honest silence and a lie."""
    verdict, reason = P.evaluate({"type": "yoga_fired", "yoga_id": "chamara"}, FACTS)
    assert verdict == P.UNEVALUABLE
    assert "catalogue" in reason


def test_yoga_ruled_out_is_its_own_predicate_for_the_counterweight():
    assert v({"type": "yoga_ruled_out", "yoga_id": "gajakesari_yoga"}) == P.SATISFIED
    assert v({"type": "yoga_ruled_out", "yoga_id": "adhi"}) == P.CONTRADICTED


# ── fail-safe: absence never refutes ───────────────────────────────────────

@pytest.mark.parametrize("facts", [None, {}, {"yogas": None}, {"aspects": "junk"},
                                   {"planet_positions": []}])
def test_no_fact_block_can_ever_produce_a_contradiction(facts):
    """S124 carried into verification: a filter that cannot judge must KEEP."""
    for name in P.PREDICATES:
        verdict, _ = P.evaluate({"type": name, "graha": "Sun", "house": 4,
                                 "lord_of": 10, "sign": "Pisces",
                                 "dignity": "Exalted", "by": "Moon",
                                 "grahas": ["Sun", "Moon"], "yoga_id": "adhi"},
                                facts)
        assert verdict != P.CONTRADICTED, f"{name} refuted on absent facts"


def test_malformed_arguments_are_unevaluable():
    for pred in ({"type": "lord_in_house", "lord_of": 99, "house": 4},
                 {"type": "lord_in_house", "lord_of": True, "house": 4},
                 {"type": "planet_in_house", "graha": "Pluto", "house": 4},
                 {"type": "planet_in_sign", "graha": "Sun", "sign": "Ophiuchus"},
                 {"type": "conjunction", "grahas": ["Sun"]},
                 {"type": "conjunction", "grahas": ["Sun", "Sun"]},
                 {"type": "planet_dignity", "graha": "Mars", "dignity": "Friendly"},
                 {"type": "yoga_fired", "yoga_id": ""}):
        assert v(pred) == P.UNEVALUABLE, pred


def test_an_evaluator_that_raises_costs_a_verdict_not_the_answer(monkeypatch):
    def boom(p, f):
        raise RuntimeError("detector exploded")
    entry = P.PREDICATES["yoga_fired"]
    monkeypatch.setitem(P.PREDICATES, "yoga_fired", (boom,) + entry[1:])
    verdict, reason = P.evaluate({"type": "yoga_fired", "yoga_id": "adhi"}, FACTS)
    assert verdict == P.UNEVALUABLE and "RuntimeError" in reason


def test_unfittable_is_always_unevaluable_and_never_a_pass():
    assert v({"type": "unfittable", "note": "needs Karakamsa"}) == P.UNEVALUABLE
    assert v({"type": "unfittable"}) == P.UNEVALUABLE


# ── the roll-up rule ───────────────────────────────────────────────────────

def test_any_contradiction_sinks_the_claim():
    r = P.evaluate_claim([{"type": "yoga_fired", "yoga_id": "adhi"},
                          {"type": "lord_in_house", "lord_of": 10, "house": 7}],
                         FACTS)
    assert r["verdict"] == P.CONTRADICTED


def test_all_satisfied_is_satisfied():
    r = P.evaluate_claim([{"type": "yoga_fired", "yoga_id": "adhi"},
                          {"type": "planet_in_house", "graha": "Jupiter", "house": 5}],
                         FACTS)
    assert r["verdict"] == P.SATISFIED and r["n_satisfied"] == 2


def test_a_mix_of_satisfied_and_unevaluable_is_unevaluable_and_still_ships():
    """The heart of it: partial knowledge is hedged, never dropped."""
    r = P.evaluate_claim([{"type": "yoga_fired", "yoga_id": "adhi"},
                          {"type": "yoga_fired", "yoga_id": "chamara"}], FACTS)
    assert r["verdict"] == P.UNEVALUABLE
    assert r["n_satisfied"] == 1 and r["n_unevaluable"] == 1


def test_a_claim_with_no_preconditions_is_unevaluable_not_satisfied():
    """Silence about a precondition is not evidence that one holds."""
    assert P.evaluate_claim([], FACTS)["verdict"] == P.UNEVALUABLE
    assert P.evaluate_claim(None, FACTS)["verdict"] == P.UNEVALUABLE


def test_coverage_reports_per_fact_class():
    res = [P.evaluate_claim([{"type": "yoga_fired", "yoga_id": "adhi"}], FACTS),
           P.evaluate_claim([{"type": "yoga_fired", "yoga_id": "chamara"}], FACTS),
           P.evaluate_claim([{"type": "lord_in_house", "lord_of": 10, "house": 4}], FACTS)]
    cov = P.coverage(res)
    assert cov["claims"] == 3
    assert cov["by_fact_class"]["yogas"][P.SATISFIED] == 1
    assert cov["by_fact_class"]["yogas"][P.UNEVALUABLE] == 1
    assert cov["by_fact_class"]["lord_house_map"][P.SATISFIED] == 1
    assert 0.0 < cov["typed_coverage"] <= 1.0
