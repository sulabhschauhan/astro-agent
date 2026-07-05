"""
tests/conftest.py
Session-scoped autouse fixture making geocoding deterministic for the
whole pytest run. ~26 live Nominatim calls/full-suite-run (calculate_chart()
-> geocode_place() with no caching) were producing cumulative HTTP 429s
(geopy.exc.GeocoderRateLimited) on repeated runs -- see SESSION_LOG.md
Session 26.

Patches the Nominatim name inside agent.chart_calculator's own namespace
(not geopy globally) for the duration of the pytest session only; restored
after the session ends. No agent/ files are touched and production runs
of frontend/app.py outside pytest are unaffected.

Fixture values come from tests/fixtures/geocoded_locations.json, captured
live one-at-a-time with 2s delays (see project history). No fall-through to
live geocoding on a cache miss -- a KeyError means the query needs capturing
before it can be used in a test.

Session 50 (P7.1b) adds a second, independent autouse fixture below:
_patch_stage2_openai, making calc_router.py's Stage 2 LLM-classification
fallback specifically deterministic and key-independent. Scope note: other
pre-existing @pytest.mark.integration tests (test_palm_quality.py,
test_nudge_endtoend.py) still make real OpenAI calls through
palm_processor.py/context_classifier.py, untouched by and out of scope for
this fixture -- confirmed by re-running the suite with a deliberately
invalid OPENAI_API_KEY: those 6 tests failed on a real auth error while
every calc_router-Stage-2-touching test still passed via the stub. See
_patch_stage2_openai's own docstring for the patch-seam rationale.
"""
import json
from pathlib import Path

import openai
import pytest
from geopy.location import Location

import agent.chart_calculator as chart_calculator
from agent.infra import calc_router

_FIXTURE_PATH = Path(__file__).parent / "fixtures" / "geocoded_locations.json"
_GEOCODED_LOCATIONS = json.loads(_FIXTURE_PATH.read_text(encoding="utf-8"))


class _FakeNominatim:
    """Drop-in replacement for geopy.geocoders.Nominatim, backed by the
    captured fixture instead of a live HTTP call."""

    def __init__(self, *args, **kwargs):
        pass

    def geocode(self, query, *, exactly_one=True, timeout=None, **kwargs):
        try:
            data = _GEOCODED_LOCATIONS[query]
        except KeyError:
            raise KeyError(
                f"'{query}' is not in tests/fixtures/geocoded_locations.json. "
                "Capture it with a live, 2s-delayed query and add it to the "
                "fixture before using it in a test -- no fall-through to "
                "live Nominatim is permitted here."
            ) from None
        location = Location(
            data["address"], (data["latitude"], data["longitude"], 0), data["raw"]
        )
        return location if exactly_one else [location]


@pytest.fixture(autouse=True, scope="session")
def _patch_geocoder():
    original = chart_calculator.Nominatim
    chart_calculator.Nominatim = _FakeNominatim
    yield
    chart_calculator.Nominatim = original


# ─── Stage 2 (calc_router.py) deterministic OpenAI stub (Session 50/P7.1b) ─
#
# PATCH SEAM: calc_router._stage2_classify does `from openai import OpenAI`
# INSIDE the function body (only when client=None), not at calc_router's
# module level -- there is no `calc_router.OpenAI` name to patch. But because
# that import statement re-executes on every call, it always re-reads the
# CURRENT `OpenAI` attribute off the real `openai` module at call time. So
# patching `openai.OpenAI` itself (this fixture) is the correct seam --
# confirmed by reading _stage2_classify (agent/infra/calc_router.py) before
# choosing it, not assumed.
#
# Reproduces today's live-call outcome for the 5 existing zero-keyword-hit
# e2e refusal tests (test_refusal_health/travel/lottery/gemstone,
# test_error_empty_question): domain="none", confidence="high" -> REFUSAL.
# No network, no OPENAI_API_KEY required.

_STAGE2_STUB_CALL_COUNT = [0]  # mutable box; module-level int would need `global`
_STAGE2_CONTRACT_VIOLATIONS: list[str] = []


def _stage2_check(condition: bool, message: str) -> None:
    """Record + raise immediately on any Stage 2 call-shape drift.

    Raising here is caught by calc_router._stage2_fallback's own
    except-Exception (by design -- Stage 2 fails closed to REFUSAL on ANY
    exception), so the immediate raise alone would NOT surface as a pytest
    failure. The `_STAGE2_CONTRACT_VIOLATIONS` list is what actually makes
    this loud: `_patch_stage2_openai`'s teardown asserts it's empty after
    every test, attributing the failure to the test that triggered it.
    """
    if not condition:
        _STAGE2_CONTRACT_VIOLATIONS.append(message)
        raise AssertionError(message)


class _FakeStage2ToolCall:
    def __init__(self, arguments: str):
        self.function = type("_FakeFunctionCall", (), {"arguments": arguments})()


class _FakeStage2Message:
    def __init__(self, tool_calls):
        self.tool_calls = tool_calls


class _FakeStage2Choice:
    def __init__(self, message):
        self.message = message


class _FakeStage2Response:
    def __init__(self, domain: str, confidence: str):
        arguments = json.dumps({"domain": domain, "confidence": confidence})
        tool_call = _FakeStage2ToolCall(arguments)
        self.choices = [_FakeStage2Choice(_FakeStage2Message([tool_call]))]


class _FakeStage2Completions:
    """Stub for client.chat.completions -- always returns domain="none",
    confidence="high" (today's real GPT-4o-mini outcome for every existing
    zero-keyword-hit refusal question). Asserts the call shape matches
    calc_router._stage2_classify's actual contract; a silently permissive
    stub would mask contract drift instead of catching it."""

    def create(self, *, model, messages, tools, tool_choice, temperature, **kwargs):
        _stage2_check(
            model == calc_router._STAGE2_MODEL,
            f"OpenAI stub: expected model={calc_router._STAGE2_MODEL!r}, got {model!r}",
        )
        _stage2_check(
            isinstance(tool_choice, dict)
            and tool_choice.get("type") == "function"
            and tool_choice.get("function", {}).get("name") == "classify_domain",
            f"OpenAI stub: unexpected tool_choice shape: {tool_choice!r}",
        )
        _stage2_check(
            bool(tools)
            and tools[0].get("function", {}).get("name") == "classify_domain",
            f"OpenAI stub: unexpected tools shape: {tools!r}",
        )
        _stage2_check(
            temperature == 0,
            f"OpenAI stub: expected temperature=0, got {temperature!r}",
        )
        _STAGE2_STUB_CALL_COUNT[0] += 1
        return _FakeStage2Response(domain="none", confidence="high")


class _FakeStage2Chat:
    def __init__(self):
        self.completions = _FakeStage2Completions()


class _FakeStage2OpenAI:
    """Drop-in replacement for openai.OpenAI (patched onto the `openai`
    module itself, not onto calc_router -- see PATCH SEAM note above)."""

    def __init__(self, *args, **kwargs):
        self.chat = _FakeStage2Chat()


@pytest.fixture(autouse=True)
def _patch_stage2_openai(request, monkeypatch):
    """Function-scoped (not session-scoped, unlike _patch_geocoder above):
    needs per-test marker inspection for the opt-out below, which a single
    session-wide patch can't do cleanly.

    OPT-OUT: tests marked @pytest.mark.integration (the existing marker
    already used by test_palm_quality.py/test_palm_endtoend.py for
    real-GPT-call tests -- no new marker invented) skip this patch entirely
    and get the real openai.OpenAI, for a genuine future live-integration
    test of Stage 2 itself.

    NOTE this opt-out is for tests that call route_question() with NO
    `_stage2_client` argument and want the real network path. It is NOT
    needed for the next prompt's dedicated Stage 2 test file, which will
    inject its own fake clients via route_question(..., _stage2_client=...)
    -- confirmed by reading calc_router._stage2_classify: `if client is
    None` short-circuits construction entirely when a client is passed, so
    an explicit _stage2_client argument always takes precedence over
    whatever this fixture has patched onto openai.OpenAI, autouse or not.
    """
    if request.node.get_closest_marker("integration"):
        yield
        return

    monkeypatch.setattr(openai, "OpenAI", _FakeStage2OpenAI)
    violations_before = len(_STAGE2_CONTRACT_VIOLATIONS)
    yield
    new_violations = _STAGE2_CONTRACT_VIOLATIONS[violations_before:]
    assert not new_violations, (
        f"calc_router Stage 2 OpenAI stub contract violation(s) in "
        f"{request.node.nodeid}: {new_violations}"
    )


def pytest_terminal_summary(terminalreporter):
    """Visibility only -- reports how many times the Stage 2 stub above
    was actually invoked this run, so a suite run can be checked for the
    expected count without grepping diagnostics output."""
    terminalreporter.write_line(
        f"[_patch_stage2_openai] stub invocation count: {_STAGE2_STUB_CALL_COUNT[0]}"
    )
