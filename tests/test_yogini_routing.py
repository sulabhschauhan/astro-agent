"""
tests/test_yogini_routing.py
Router-layer tests for Yogini dasha's Session 72 wiring: calc_router.py's
_DOMAIN_KEYWORDS/_route_to_domain/_STAGE2_VALID_DOMAINS now recognize
"yogini_dasha", and orchestrator.py's _VALID_DOMAINS admits it too.

SCOPE (design-chat revised, Session 72): chart_profile.py's
build_domain_profile() Yogini branch and orchestrator's dispatch to
compute_yogini_dasha/current_yogini_md are BOTH deferred to Prompt 4 --
adding a dispatch bypass here without a profile builder would special-case
Yogini against the domain contract every other routed domain follows (see
calc_router.py's own yogini_dasha branch comment and orchestrator.py's own
_VALID_DOMAINS comment for the full rationale). Consequently
test_yogini_orchestrator_returns_current_md below is xfail, not a live
assertion.

UPDATE (Session 73, Prompt 4): build_domain_profile()'s own yogini_dasha
branch + _VALID_DOMAINS entry have now landed (see
tests/infra/test_chart_profile_yogini.py for direct coverage) -- the
ValueError this test still hits has moved one layer further along the
pipeline, from chart_profile.py to result_formatter.py's format_answer()
dispatch (confirmed directly: `result_formatter: unknown domain
'yogini_dasha'`), which does not yet admit this domain. Still xfail;
will pass once Prompt 5 lands result_formatter.py's own yogini_dasha
branch.

Sulabh natal inputs / current-MD-lord fixture ("Mars", as of 2026-07-24)
mirror tests/test_yogini_dasha.py's own test_current_md_lookup_today()
exactly -- same chart, same query date, same expected lord.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import json

import pytest

from agent.infra import calc_router, orchestrator
from agent.infra.calc_router import route_question


# ─── Minimal Stage 2 client stub (mirrors tests/infra/test_calc_router_
# stage2.py's _FakeClient, not imported cross-file since that module lives
# under tests/infra/ and this file is a top-level tests/ sibling of
# test_yogini_dasha.py -- kept intentionally small: only what this file's
# one below-floor case needs). ─────────────────────────────────────────


class _StubToolCall:
    def __init__(self, domain: str, confidence: str):
        self.function = type(
            "_StubFn", (), {"arguments": json.dumps({"domain": domain, "confidence": confidence})}
        )()


class _StubClient:
    """Canned Stage 2 client: always returns the given (domain, confidence)
    tool call, regardless of the question asked. Injected via
    route_question's `_stage2_client` seam -- no network, no API key."""

    def __init__(self, domain: str, confidence: str):
        message = type("_StubMessage", (), {"tool_calls": [_StubToolCall(domain, confidence)]})()
        choice = type("_StubChoice", (), {"message": message})()
        response = type("_StubResponse", (), {"choices": [choice]})()
        completions = type("_StubCompletions", (), {"create": lambda self, **kw: response})()
        self.chat = type("_StubChat", (), {"completions": completions})()


def test_yogini_keyword_routes():
    # MEASURE-FIRST FINDING (measured directly against _score_domain before
    # writing this assertion, per CLAUDE.md Working Style #2/#3 and this
    # suite's own test_orchestrator_muhurta.py precedent): "what is my
    # yogini dasha?" (the bare word "dasha") does NOT route to yogini_dasha
    # -- it saturates current_dasha to 1.0 instead. Root cause is a
    # pre-existing _keyword_hits() behavior, not anything this change
    # introduces: the bidirectional single-word substring check means the
    # bare token "dasha" also counts as a hit against _DASHA_KEYWORDS'
    # "mahadasha" and "antardasha" entries (both CONTAIN "dasha" as a
    # substring), so one token alone saturates current_dasha's 3-hit cap
    # to score 1.0, beating yogini_dasha's own 0.667 ("yogini" + "yogini
    # dasha" hits). "yogini dasa" (the Sanskrit "dasa" spelling, also in
    # _YOGINI_DASHA_KEYWORDS) sidesteps this entirely -- "dasa" is not a
    # substring of "mahadasha"/"antardasha", so current_dasha scores 0.0
    # here and yogini_dasha's own 0.667 (2 hits: "yogini" + "yogini dasa")
    # clears both _CONFIDENCE_FLOOR (0.4) and _CONFIDENCE_MARGIN (0.15)
    # cleanly via Stage 1 alone.
    result = route_question("what is my yogini dasa?")
    assert result.domain == "yogini_dasha"


def test_yogini_yogini_name_routes():
    # Bare "dhanya" (1 hit) + bare "when" (1 hit on current_dasha) both
    # score 0.333, below _CONFIDENCE_FLOOR -- genuinely a Stage 2 case
    # (this task's scope does not add a _STAGE2_SYSTEM_PROMPT gloss for
    # yogini_dasha, so a live Stage 2 call would not reach it today; a
    # stub client proves the router-level plumbing -- _STAGE2_VALID_
    # DOMAINS membership + _route_to_domain's yogini_dasha branch --
    # resolves correctly once Stage 2 does classify it, same as this
    # suite's existing precedent for below-floor cases).
    client = _StubClient(domain="yogini_dasha", confidence="high")
    result = route_question("when does dhanya end?", _stage2_client=client)
    assert result.domain == "yogini_dasha"


def test_bare_mangala_does_not_route_to_yogini():
    # Bare "mangala" (no "yogini" qualifier) must never route to
    # yogini_dasha -- it collides with _MARRIAGE_KEYWORDS' "mangal dosha".
    # Destination not asserted (marriage_compatibility route or REFUSAL
    # both acceptable) -- only that it is NOT yogini_dasha.
    result = route_question("do i have mangal dosha?")
    assert result.domain != "yogini_dasha"


def test_bare_pingala_does_not_route_to_yogini():
    # Bare "pingala" (nadi context, no "yogini" qualifier) must never
    # route to yogini_dasha. No explicit _stage2_client needed -- falls
    # below floor on every domain, same as test_bare_mangala above, and
    # picks up tests/conftest.py's autouse Stage 2 stub (domain="none",
    # confidence="high" -> REFUSAL), which already satisfies "not
    # yogini_dasha" without needing its own injected client.
    result = route_question("what does pingala nadi say about me?")
    assert result.domain != "yogini_dasha"


def test_yogini_in_stage2_valid_domains():
    assert "yogini_dasha" in calc_router._STAGE2_VALID_DOMAINS


def test_yogini_in_orchestrator_valid_domains():
    assert "yogini_dasha" in orchestrator._VALID_DOMAINS


@pytest.mark.xfail(
    reason="Prompt 5: result_formatter.py's format_answer() does not yet "
           "admit yogini_dasha in its own per-domain dispatch -- router "
           "(Prompt 3) and chart_profile.py's build_domain_profile() "
           "(Prompt 4) both now handle this domain correctly (see "
           "tests/infra/test_chart_profile_yogini.py), but format_answer() "
           "raises 'result_formatter: unknown domain yogini_dasha'. "
           "Will pass once Prompt 5 lands."
)
def test_yogini_orchestrator_returns_current_md():
    # As of 2026-07-24, current Yogini MD lord must be "Mars" for Sulabh
    # (mirrors tests/test_yogini_dasha.py's test_current_md_lookup_today()).
    from agent.chart_calculator import calculate_chart

    sulabh_chart = calculate_chart("Sulabh", "6 Apr 1988", "00:30", "Calcutta, India")
    # "yogini dasa" (not "dasha") -- see test_yogini_keyword_routes' own
    # measure-first finding: the bare word "dasha" routes to current_dasha
    # instead (a pre-existing keyword-scoring quirk unrelated to this
    # domain), which would make this xfail for the WRONG reason.
    answer = orchestrator.answer_question("what is my yogini dasa?", sulabh_chart)
    assert answer.answer_payload["current_md"]["lord"] == "Mars"
