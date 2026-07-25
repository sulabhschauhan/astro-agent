"""
tests/infra/test_calc_router_stage2.py

Dedicated unit tests for calc_router.py's Stage 2 LLM-constrained-
classification fallback (Session 49+/P7.1). Every test injects a fake
client via route_question(..., _stage2_client=...) -- confirmed by reading
_stage2_classify's `if client is None:` check that this short-circuits
construction of a real openai.OpenAI entirely, bypassing BOTH the real
network AND the conftest.py autouse OpenAI stub (Session 50/P7.1b). No
network, no OPENAI_API_KEY, no @pytest.mark.integration anywhere here.

Hardest case first (CLAUDE.md Working Style #3): Group A (fail-closed
battery) comes before the happy-path routing tests -- a fail-closed
regression (an exception escaping route_question(), or a guessed domain)
is the highest-severity failure mode for this fallback.

Two assertions in this file deliberately diverge from the original task
prompt's wording, verified against the actual code rather than guessed:
- RouteResult.demotion_reason does NOT distinguish "domain=none" from
  "confidence=medium/low" -- calc_router._stage2_fallback returns the same
  generic "question not classifiable with confidence" string for both
  (see calc_router.py lines ~589-595). The richer distinction
  ("stage2 domain=none" vs "stage2 confidence=... (not high)") exists ONLY
  in diagnostics/calc_router_stage2.log's `outcome` field. Tests below
  assert this accurately rather than asserting a distinction on
  RouteResult that the code doesn't actually make.
"""
from __future__ import annotations

import json

import pytest

from agent.infra import calc_router
from agent.infra.calc_router import route_question
from agent.infra.chart_profile import AnswerTier

# Zero-keyword-hit question: scores 0.0 on all 3 domain whitelists, so
# best_score < _CONFIDENCE_FLOOR -- the only path that reaches Stage 2.
# Already exercised live by tests/infra/test_orchestrator_e2e.py's
# test_refusal_health and by diagnostics/calc_router_stage2.log.
_ZERO_KEYWORD_Q = "What about my health this year?"

# >=2 marriage keyword hits (marriage, ashtakoot, "compatible" -> stems to
# "compatibility") saturates marriage_compatibility's score at 1.0 against
# 0.0 on career/dasha -- clears both _CONFIDENCE_FLOOR and
# _CONFIDENCE_MARGIN via Stage 1 alone, so Stage 2 is never reached.
_KEYWORD_RICH_MARRIAGE_Q = "Are Sulabh and Surbhi compatible for marriage ashtakoot?"


# ─── Fakes ──────────────────────────────────────────────────────────────


class _FakeToolCallFunction:
    def __init__(self, arguments: str):
        self.arguments = arguments


class _FakeToolCall:
    def __init__(self, arguments: str):
        self.function = _FakeToolCallFunction(arguments)


class _FakeMessage:
    def __init__(self, tool_calls):
        self.tool_calls = tool_calls


class _FakeChoice:
    def __init__(self, message):
        self.message = message


class _FakeResponse:
    def __init__(self, tool_calls):
        self.choices = [_FakeChoice(_FakeMessage(tool_calls))]


def _tool_call_response(domain: str, confidence: str) -> _FakeResponse:
    arguments = json.dumps({"domain": domain, "confidence": confidence})
    return _FakeResponse([_FakeToolCall(arguments)])


class _FakeCompletions:
    """Records every call (`.calls`); returns a canned response or raises
    a canned exception, per construction. `.calls` is the actual proof
    used by the "Stage 2 never fires" tests below -- an empty list proves
    non-invocation directly, independent of whether an exception would
    otherwise be swallowed somewhere upstream."""

    def __init__(self, response: _FakeResponse | None = None, exception: Exception | None = None):
        self._response = response
        self._exception = exception
        self.calls: list[dict] = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        if self._exception is not None:
            raise self._exception
        return self._response


class _FakeClient:
    """Minimal stand-in for openai.OpenAI, injected via route_question's
    `_stage2_client` seam."""

    def __init__(
        self,
        *,
        domain: str | None = None,
        confidence: str | None = None,
        response: _FakeResponse | None = None,
        exception: Exception | None = None,
    ):
        if response is None and exception is None:
            response = _tool_call_response(domain, confidence)
        self.completions = _FakeCompletions(response=response, exception=exception)
        self.chat = type("_FakeChat", (), {"completions": self.completions})()


def _explosive_client() -> _FakeClient:
    """A client whose create() raises AssertionError if invoked at all --
    used as an extra (belt-and-suspenders) guard in the "Stage 2 never
    fires" tests. `.completions.calls == []` is the real proof."""
    return _FakeClient(exception=AssertionError("stage2 must not fire"))


# ─── Group A: fail-closed battery (hardest case first, item 4 a-f) ─────

_FAIL_CLOSED_CASES = [
    pytest.param(
        lambda: _FakeClient(exception=ConnectionError("simulated network failure")),
        id="a_network_exception",
    ),
    pytest.param(
        lambda: _FakeClient(exception=TimeoutError("simulated timeout")),
        id="b_timeout_exception",
    ),
    pytest.param(
        lambda: _FakeClient(response=_FakeResponse([])),
        id="c_no_tool_calls",
    ),
    pytest.param(
        lambda: _FakeClient(response=_FakeResponse([_FakeToolCall("not valid json{")])),
        id="d_malformed_json_arguments",
    ),
    pytest.param(
        lambda: _FakeClient(domain="not_a_real_domain", confidence="high"),
        id="e_schema_invalid_domain",
    ),
    pytest.param(
        lambda: _FakeClient(domain="career_strength", confidence="extreme"),
        id="f_schema_invalid_confidence",
    ),
]


@pytest.mark.parametrize("client_factory", _FAIL_CLOSED_CASES)
def test_fails_closed(client_factory):
    """All 6 Stage 2 failure modes must fail CLOSED: REFUSAL, never an
    exception escaping route_question(), never a guessed domain. Mirrors
    calc_router._stage2_fallback's own try/except Exception contract."""
    result = route_question(_ZERO_KEYWORD_Q, _stage2_client=client_factory())
    assert result.tier == AnswerTier.REFUSAL
    assert result.domain is None
    assert result.confidence == 0.0
    assert result.demotion_reason == "question not classifiable with confidence"
    assert result.requires_partner is False


# ─── Group B: routes on high confidence (item 1) ───────────────────────


def test_routes_on_high_confidence():
    client = _FakeClient(domain="career_strength", confidence="high")
    result = route_question(_ZERO_KEYWORD_Q, _stage2_client=client)
    assert result.domain == "career_strength"
    assert result.tier == AnswerTier.TIER_2_RANGE
    assert result.confidence == calc_router._STAGE2_CONFIDENCE_MAP["high"]
    assert result.demotion_reason == calc_router._CAREER_DEMOTION_REASON
    assert result.requires_partner is False


# ─── Group C: refuses on medium/low confidence (item 2) ────────────────


@pytest.mark.parametrize("confidence", ["medium", "low"])
def test_refuses_on_non_high_confidence(confidence):
    client = _FakeClient(domain="career_strength", confidence=confidence)
    result = route_question(_ZERO_KEYWORD_Q, _stage2_client=client)
    assert result.tier == AnswerTier.REFUSAL
    assert result.domain is None
    # See module docstring: RouteResult.demotion_reason is the same
    # generic string for every Stage 2 REFUSAL cause -- the "not high"
    # detail lives only in the diagnostics log (see Group D/H below).
    assert result.demotion_reason == "question not classifiable with confidence"


# ─── Group D: domain=none vs non-high-confidence log distinction (item 3) ─


def test_domain_none_high_confidence_refuses_and_logs_distinctly(tmp_path, monkeypatch):
    log_path = tmp_path / "stage2.log"
    monkeypatch.setattr(calc_router, "_STAGE2_LOG_PATH", log_path)

    client = _FakeClient(domain="none", confidence="high")
    result = route_question(_ZERO_KEYWORD_Q, _stage2_client=client)

    assert result.tier == AnswerTier.REFUSAL
    assert result.domain is None
    assert result.demotion_reason == "question not classifiable with confidence"

    lines = log_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    record = json.loads(lines[0])
    assert record["stage2_domain"] is None
    assert record["stage2_confidence"] == "high"
    # P7.1's post-run log-message fix: "domain=none" must read distinctly
    # from a "confidence=... (not high)" refusal.
    assert "stage2 domain=none" in record["outcome"]
    assert "not high" not in record["outcome"]


def test_non_high_confidence_logs_distinctly_from_domain_none(tmp_path, monkeypatch):
    log_path = tmp_path / "stage2.log"
    monkeypatch.setattr(calc_router, "_STAGE2_LOG_PATH", log_path)

    client = _FakeClient(domain="career_strength", confidence="medium")
    route_question(_ZERO_KEYWORD_Q, _stage2_client=client)

    lines = log_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    record = json.loads(lines[0])
    assert record["stage2_domain"] == "career_strength"
    assert "confidence='medium' (not high)" in record["outcome"]
    assert "domain=none" not in record["outcome"]


# ─── Group E: Stage 2 never fires when Stage 1 already resolves (items 5-6) ─


def test_stage2_never_fires_when_stage1_routes():
    client = _explosive_client()
    result = route_question(
        _KEYWORD_RICH_MARRIAGE_Q, has_partner_data=True, _stage2_client=client
    )
    assert client.completions.calls == []
    assert result.domain == "marriage_compatibility"
    assert result.tier == AnswerTier.TIER_1_EXACT
    assert result.demotion_reason is None
    assert result.requires_partner is True


def test_stage2_never_fires_on_unbuilt_module_refusal():
    # "ashtakavarga" retired from this test Session 55 when the av_transit
    # domain went live (router carry-forward closure) -- it is no longer
    # in _UNBUILT_MODULE_KEYWORDS. Substituted "yogini" (Yogini dasha) at
    # that point; Session 72 retired THAT substitution in turn -- "yogini"
    # is now BUILT (agent/calculations/dashas/yogini.py + router wiring),
    # so it no longer belongs in this REFUSAL test at all (see the
    # dedicated test_yogini_keyword_routes()/test_yogini_yogini_name_
    # routes() coverage in tests/test_yogini_routing.py instead). Re-
    # substituted "ashtottari" (Ashtottari dasha): still present in
    # _UNBUILT_MODULE_KEYWORDS, genuinely unbuilt (no dasha submodule for
    # it, per CLAUDE.md's own P2-order lock), and unrelated to any
    # _DOMAIN_KEYWORDS list (marriage/career/current_dasha/av_transit/
    # arudha_lagna/upapada_lagna/muhurta_window/yogini_dasha) or any of
    # those domains' own keywords, so the substitution can't accidentally
    # collide with a different routing path.
    client = _explosive_client()
    result = route_question("Tell me about my ashtottari dasha", _stage2_client=client)
    assert client.completions.calls == []
    assert result.tier == AnswerTier.REFUSAL
    assert result.domain is None
    assert "Ashtottari" in result.demotion_reason


# ─── Group F: Stage 2 marriage routing respects has_partner_data (item 7) ──


def test_stage2_marriage_route_still_requires_partner_data():
    client = _FakeClient(domain="marriage_compatibility", confidence="high")
    result = route_question(_ZERO_KEYWORD_Q, has_partner_data=False, _stage2_client=client)
    assert result.tier == AnswerTier.REFUSAL
    assert result.domain is None
    assert result.demotion_reason == "marriage_compatibility requires partner birth data"
    assert result.requires_partner is True


def test_stage2_marriage_route_succeeds_with_partner_data():
    client = _FakeClient(domain="marriage_compatibility", confidence="high")
    result = route_question(_ZERO_KEYWORD_Q, has_partner_data=True, _stage2_client=client)
    assert result.domain == "marriage_compatibility"
    assert result.tier == AnswerTier.TIER_1_EXACT
    assert result.confidence == calc_router._STAGE2_CONFIDENCE_MAP["high"]
    assert result.demotion_reason is None
    assert result.requires_partner is True


# ─── Group G: log side-effect, one JSONL line per invocation (item 8) ─────


def test_log_records_one_line_per_invocation_with_distinguishing_outcomes(
    tmp_path, monkeypatch
):
    log_path = tmp_path / "stage2.log"
    monkeypatch.setattr(calc_router, "_STAGE2_LOG_PATH", log_path)

    route_question(
        _ZERO_KEYWORD_Q,
        _stage2_client=_FakeClient(domain="career_strength", confidence="high"),
    )
    route_question(
        _ZERO_KEYWORD_Q,
        _stage2_client=_FakeClient(domain="career_strength", confidence="low"),
    )
    route_question(
        _ZERO_KEYWORD_Q,
        _stage2_client=_FakeClient(exception=ConnectionError("simulated failure")),
    )

    lines = log_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 3

    records = [json.loads(line) for line in lines]
    assert records[0]["outcome"].startswith("ROUTED:career_strength")
    assert "REFUSAL" in records[1]["outcome"] and "not high" in records[1]["outcome"]
    assert "REFUSAL" in records[2]["outcome"] and "ConnectionError" in records[2]["outcome"]
