"""S168: palm TEXT modules migrated off gpt-4o/gpt-4o-mini to gpt-6-luna.

Guards the migration deterministically (no network, no OpenAI): the model
string, reasoning_effort wiring, the DROPPED temperature, and the TypeError
fallback that keeps the call working on an SDK build that rejects the kwarg.

SCOPE (S168, ratified): only the TEXT path migrated -- claim_extraction,
claim_voicing, contact_llm_fallback (+ palm_reading's vestigial constant). The
VISION modules (palm_processor, vlm_arm) are DELIBERATELY still on gpt-4o,
pending the gpt-6.1-terra A/B; they are NOT asserted here. gpt-4o retires
2027-01-14, so the terra A/B is the hard-deadline gate for palm vision.
"""
import types

import pytest

from agent.interpretive import (claim_extraction, claim_voicing,
                                contact_llm_fallback, palm_reading)

_TEXT_MODULES = [claim_extraction, claim_voicing, contact_llm_fallback]
_MODEL_ATTR = {
    claim_extraction: "_EXTRACTION_MODEL",
    claim_voicing: "_VOICE_MODEL",
    contact_llm_fallback: "_FALLBACK_MODEL",
}


def test_text_models_are_gpt6_luna():
    for mod, attr in _MODEL_ATTR.items():
        assert getattr(mod, attr) == "gpt-6-luna", f"{mod.__name__}.{attr}"
    assert palm_reading._READING_MODEL == "gpt-6-luna"


def test_reasoning_effort_is_minimal():
    for mod in _TEXT_MODULES:
        assert mod._REASONING_EFFORT == "minimal", mod.__name__


class _FakeResp:
    def __init__(self):
        self.choices = [types.SimpleNamespace(
            message=types.SimpleNamespace(content="{}"))]


class _CaptureClient:
    """Stand-in OpenAI client: records create() kwargs; can reject the
    reasoning_effort kwarg to exercise the TypeError fallback branch."""
    def __init__(self, reject_reasoning_effort: bool = False):
        self._reject = reject_reasoning_effort
        self.calls: list[dict] = []
        self.chat = types.SimpleNamespace(
            completions=types.SimpleNamespace(create=self._create))

    def _create(self, **kwargs):
        if self._reject and "reasoning_effort" in kwargs:
            raise TypeError("unexpected keyword argument 'reasoning_effort'")
        self.calls.append(kwargs)
        return _FakeResp()


@pytest.mark.parametrize("mod", _TEXT_MODULES, ids=lambda m: m.__name__)
def test_call_uses_luna_minimal_and_no_temperature(mod):
    client = _CaptureClient()
    mod._call_llm(client, [{"role": "user", "content": "x"}])
    kw = client.calls[-1]
    assert kw["model"] == "gpt-6-luna"
    assert "temperature" not in kw            # gpt-6 rejects it
    assert kw.get("reasoning_effort") == "minimal"


@pytest.mark.parametrize("mod", _TEXT_MODULES, ids=lambda m: m.__name__)
def test_typeerror_fallback_still_calls_without_reasoning_effort(mod):
    client = _CaptureClient(reject_reasoning_effort=True)
    # Must not raise: the fallback re-issues the call without reasoning_effort.
    mod._call_llm(client, [{"role": "user", "content": "x"}])
    kw = client.calls[-1]
    assert "reasoning_effort" not in kw
    assert "temperature" not in kw
    assert kw["model"] == "gpt-6-luna"
