"""Tests for agent/infra/chart_profile.py -- build_domain_profile()'s
yogini_dasha dispatch branch (Session 73, Prompt 4).

Wired directly into build_domain_profile()/_VALID_DOMAINS (unlike arudha_
lagna/upapada_lagna's own standalone-builder-first landing) -- there is no
separate build_yogini_profile() helper to test in isolation, since the
branch is a thin call site onto agent/calculations/dashas/yogini.py's
already-complete compute_yogini_dasha()/current_yogini_md() (see the
branch's own comment in chart_profile.py). calc_router.py/orchestrator.py's
own _VALID_DOMAINS already admit "yogini_dasha" (Session 72/Prompt 3), but
result_formatter.py does not yet (Prompt 5) -- so this file exercises
build_domain_profile() directly, not the full orchestrator.answer_question()
chain (see tests/test_yogini_routing.py's own xfail
test_yogini_orchestrator_returns_current_md for that gap).

Sulabh natal inputs / current-MD-lord fixture ("Mars", as of 2026-07-24)
mirror tests/test_yogini_dasha.py's own test_current_md_lookup_today()
exactly -- same chart, same query date, same expected lord.
"""
import swisseph as swe

from agent.infra import chart_profile
from agent.infra.chart_profile import build_domain_profile


def _sulabh_chart():
    from agent.chart_calculator import calculate_chart
    return calculate_chart("Sulabh", "6 Apr 1988", "00:30", "Calcutta, India")


def test_yogini_dasha_in_valid_domains():
    assert "yogini_dasha" in chart_profile._VALID_DOMAINS


def test_yogini_current_md_lord_sulabh_today():
    # As of 2026-07-24, current MD lord must be "Mars" (2024-07-06 ->
    # 2028-07-06 per tests/fixtures/jhora_sulabh.md's Yogini section),
    # mirroring tests/test_yogini_dasha.py's own
    # test_current_md_lookup_today() at the chart_profile layer.
    evaluated_at_jd = swe.julday(2026, 7, 24, 0.0)
    profile = build_domain_profile("yogini_dasha", _sulabh_chart(), evaluated_at_jd)
    assert profile.payload["current_md"]["lord"] == "Mars"
    assert profile.payload["current_md"]["yogini_name"] == "Bhramari"


def test_yogini_profile_shape():
    evaluated_at_jd = swe.julday(2026, 7, 24, 0.0)
    profile = build_domain_profile("yogini_dasha", _sulabh_chart(), evaluated_at_jd)
    assert profile.domain == "yogini_dasha"
    assert profile.stub_caveats == ()
    assert profile.uncertainty_virupa == 0.0
    assert profile.uncertainty_days == 0.0
    current_md = profile.payload["current_md"]
    assert set(current_md) == {"lord", "yogini_name", "start_jd", "end_jd"}
    assert current_md["start_jd"] < evaluated_at_jd < current_md["end_jd"]
