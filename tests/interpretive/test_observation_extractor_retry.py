"""
tests/interpretive/test_observation_extractor_retry.py
Tests for agent/interpretive/observation_extractor.py's incompleteness
guard -- the batched-call retry added to catch a partial JSON response
that silently drops a feature with substantive input prose (dogfood
2026-08-05T22:09, Athira: head/heart/venus/thumb came back empty despite
full descriptions). MOCKS the LLM throughout -- no live API call.

Fake OpenAI client transplanted from test_claim_extraction.py's
`responses=[(content, exception), ...]` call-order convention, which is
exactly what a multi-attempt retry test needs (first attempt drops a
feature, later attempt doesn't).
"""

from __future__ import annotations

import json
import logging

from agent.interpretive.observation_extractor import (
    ObservationRecord,
    extract_observation,
)

# ─── Fake OpenAI client -- transplanted from test_claim_extraction.py ────


class _FakeMessage:
    def __init__(self, content: str):
        self.content = content


class _FakeChoice:
    def __init__(self, content: str):
        self.message = _FakeMessage(content)


class _FakeResponse:
    def __init__(self, content: str):
        self.choices = [_FakeChoice(content)]


class _FakeCompletions:
    """Records every call (`.calls`); `responses` is a list of content
    strings consumed in call order. Past the end of `responses`, the
    LAST entry is reused (clamped index) -- tests proving "never a 3rd
    call" must assert `len(.calls)` explicitly, not rely on clamping."""

    def __init__(self, responses: list[str]):
        self._responses = responses
        self.calls: list[dict] = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        idx = min(len(self.calls) - 1, len(self._responses) - 1)
        return _FakeResponse(self._responses[idx])


class _FakeClient:
    def __init__(self, responses: list[str]):
        self.completions = _FakeCompletions(responses=responses)
        self.chat = type("_FakeChat", (), {"completions": self.completions})()


def _response(observations: dict, unmapped: dict | None = None) -> str:
    return json.dumps({"observations": observations, "unmapped": unmapped or {}})


# ─── Fixture prose -- substantive enough (>15 chars, no trivial marker) ──

_HEAD_PROSE = "long, deep, curved head line crossing the palm"
_HEART_PROSE = "deep, chained heart line ending under the index finger"
_LIFE_PROSE = "deep, long life line curving around the base of the thumb"

_HEAD_FULL_OBS = {"Line of Head": {"Length": {"value": "long"}, "Depth": {"value": "deep"}}}
_HEART_FULL_OBS = {"Line of Heart": {"Depth": {"value": "deep"}}}


# ─── Test 1: partial first, full on retry -> feature recovered, logged ───


def test_partial_first_response_recovers_on_retry(caplog):
    """First attempt's JSON silently omits "Line of Head" entirely
    despite substantive input prose (the dogfood-observed failure mode);
    the retry's response includes it. Final record must have the
    feature's tokens, and the retry must be logged."""
    partial_resp = _response(observations={})  # drops both features
    full_resp = _response(observations={**_HEAD_FULL_OBS, **_HEART_FULL_OBS})
    fake = _FakeClient(responses=[partial_resp, full_resp])

    with caplog.at_level(logging.INFO):
        record = extract_observation(
            {"head line": [_HEAD_PROSE], "heart line": [_HEART_PROSE]},
            client=fake,
        )

    assert isinstance(record, ObservationRecord)
    assert record.features["Line of Head"].tokens == {
        "Length": {"value": "long", "confidence": 1.0},
        "Depth": {"value": "deep", "confidence": 1.0},
    }
    assert record.features["Line of Heart"].tokens == {
        "Depth": {"value": "deep", "confidence": 1.0},
    }
    assert len(fake.completions.calls) == 2

    assert record.extraction_retries["attempts_made"] == 2
    assert record.extraction_retries["retried"] is True
    assert record.extraction_retries["final_dropped"] == []
    first_attempt = record.extraction_retries["dropped_per_attempt"][0]
    assert first_attempt["attempt"] == 1
    assert set(first_attempt["dropped"]) == {"Line of Head", "Line of Heart"}

    assert any(
        "retrying whole batch" in msg and "Line of Head" in msg
        for msg in caplog.messages
    )

    # Prove the retry RE-ASKS (temperature=0 means an identical request
    # would just return the identical partial response again) rather than
    # re-sending the exact same messages and hoping for a different roll.
    first_call_messages = fake.completions.calls[0]["messages"]
    second_call_messages = fake.completions.calls[1]["messages"]
    assert second_call_messages != first_call_messages
    # Original messages preserved untouched, one corrective message appended.
    assert second_call_messages[: len(first_call_messages)] == first_call_messages
    assert len(second_call_messages) == len(first_call_messages) + 1
    correction = second_call_messages[-1]
    assert correction["role"] == "user"
    assert "Line of Head" in correction["content"]
    assert "Line of Heart" in correction["content"]
    assert "omitted" in correction["content"]


# ─── Test 2: always partial -> best-effort result, no raise ──────────────


def test_always_partial_returns_best_effort_after_exhausting_retries():
    """Every attempt drops "Line of Head" but attempt 2 additionally
    recovers "Line of Heart" -- the best (fewest-dropped) attempt must
    win, retries must exhaust at the configured cap, and nothing raises."""
    resp_drops_both = _response(observations={})
    resp_drops_head_only = _response(observations=_HEART_FULL_OBS)
    fake = _FakeClient(responses=[resp_drops_both, resp_drops_head_only, resp_drops_head_only])

    record = extract_observation(
        {"head line": [_HEAD_PROSE], "heart line": [_HEART_PROSE]},
        client=fake,
        model="gpt-4o-mini",
    )

    # default ASTRO_EXTRACT_INCOMPLETE_RETRIES=2 -> 3 total attempts, capped.
    assert len(fake.completions.calls) == 3
    assert record.extraction_retries["attempts_made"] == 3
    assert record.extraction_retries["retried"] is True
    assert record.extraction_retries["final_dropped"] == ["Line of Head"]

    # Best-effort result kept: "Line of Head" stays empty (honest silence,
    # never fabricated), "Line of Heart" recovered from the better attempt.
    assert record.features["Line of Head"].tokens == {}
    assert record.features["Line of Head"].unmapped == []
    assert record.features["Line of Heart"].tokens == {
        "Depth": {"value": "deep", "confidence": 1.0},
    }


# ─── Test 3: legitimately empty (barely visible) -> no retry ─────────────


def test_barely_visible_prose_empty_result_does_not_trigger_retry():
    """A feature whose prose is a stock "nothing here" phrasing legitimately
    comes back with zero tokens and zero unmapped -- this must NOT be
    treated as a drop, so exactly one call is made."""
    resp = _response(observations={}, unmapped={})
    fake = _FakeClient(responses=[resp])

    record = extract_observation(
        {"fate line": ["Fate line is barely visible."]},
        client=fake,
    )

    assert len(fake.completions.calls) == 1
    assert record.extraction_retries["attempts_made"] == 1
    assert record.extraction_retries["retried"] is False
    assert record.extraction_retries["final_dropped"] == []
    assert record.features["Line of Fate"].tokens == {}
    assert record.features["Line of Fate"].unmapped == []


# ─── Test 4: fully complete first response -> zero retries ───────────────


def test_fully_complete_first_response_makes_zero_retries():
    resp = _response(observations={**_HEAD_FULL_OBS, **_HEART_FULL_OBS})
    fake = _FakeClient(responses=[resp])

    record = extract_observation(
        {"head line": [_HEAD_PROSE], "heart line": [_HEART_PROSE]},
        client=fake,
    )

    assert len(fake.completions.calls) == 1
    assert record.extraction_retries["attempts_made"] == 1
    assert record.extraction_retries["retried"] is False
    assert record.extraction_retries["final_dropped"] == []
    assert record.extraction_retries["dropped_per_attempt"] == [{"attempt": 1, "dropped": []}]
    assert record.features["Line of Head"].tokens == {
        "Length": {"value": "long", "confidence": 1.0},
        "Depth": {"value": "deep", "confidence": 1.0},
    }
    assert record.features["Line of Heart"].tokens == {
        "Depth": {"value": "deep", "confidence": 1.0},
    }
