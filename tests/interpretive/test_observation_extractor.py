"""
tests/interpretive/test_observation_extractor.py
Tests for agent/interpretive/observation_extractor.py's extract_observation().
MOCKS the LLM throughout -- no live API call. Fake OpenAI client classes
transplanted from tests/interpretive/test_claim_extraction.py (same
client.chat.completions.create(...) surface, same responses=[(content,
exception), ...] call-order convention, simplified here since this module
makes at most ONE call, never a retry).

Hardest case first, per project convention: a mocked LLM response that
VIOLATES its own closed-vocabulary instruction (emits a token that is not
in the registry at all) -- proves the Python-side fail-closed guard, not
just the prompt wording, is what actually protects the output. See
observation_extractor.py's own module docstring point 2 for why this test
does NOT use the task prompt's own suggested example ("faintly wavy") --
"wavy" is a real registry value token, verified directly against
data/ontology_registry.json, so it cannot demonstrate the no-valid-token
path; "shimmery" (confirmed absent) is used instead.
"""

from __future__ import annotations

import json

import pytest

from agent.interpretive.observation_extractor import (
    _CLOSED_VOCAB,
    _FEATURE_ALIAS,
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
    def __init__(self, content: str | None = None):
        self._content = content
        self.calls: list[dict] = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return _FakeResponse(self._content)


class _FakeClient:
    def __init__(self, content: str | None = None):
        self.completions = _FakeCompletions(content=content)
        self.chat = type("_FakeChat", (), {"completions": self.completions})()


def _obs_response(observations: dict) -> str:
    return json.dumps({"observations": observations})


# ─── Sanity: registry-derived constants sane before relying on them ──────


def test_alias_table_has_ten_keys_eight_mapped_two_none():
    assert len(_FEATURE_ALIAS) == 10
    mapped = {k: v for k, v in _FEATURE_ALIAS.items() if v is not None}
    unmapped = {k: v for k, v in _FEATURE_ALIAS.items() if v is None}
    assert len(mapped) == 8
    assert set(unmapped) == {"fingers", "markings/other features"}
    # every mapped ontology feature must actually exist in the closed vocab
    for ontology_feature in mapped.values():
        assert ontology_feature in _CLOSED_VOCAB


# ─── HARDEST CASE FIRST ────────────────────────────────────────────────


def test_hardest_case_llm_emits_out_of_vocabulary_token_is_dropped():
    # "shimmery" is confirmed absent from the full 214-value flattened
    # registry pool -- if the LLM ignores its own closed-vocabulary
    # instruction and emits it anyway, the Python-side guard (not prompt
    # wording) must still drop it.
    fake = _FakeClient(content=_obs_response({
        "Line of Head": {"Direction": {"value": "shimmery"}},  # "Direction" IS valid for
        # this feature -- isolates the test to the VALUE-vocabulary guard specifically,
        # not the attribute-validity guard.
    }))
    result = extract_observation(
        {"head line": ["the head line looks faintly wavy and shimmery"]},
        client=fake,
    )
    assert result == {}
    assert len(fake.completions.calls) == 1  # exactly one call, no retry mechanism here


# ─── Valid compound prose -> all tokens emitted ──────────────────────────


def test_valid_compound_prose_all_tokens_emitted():
    fake = _FakeClient(content=_obs_response({
        "Line of Life": {
            "Length": {"value": "long"},
            "Width": {"value": "narrow"},
            "Depth": {"value": "deep"},
        },
    }))
    result = extract_observation(
        {"life line": ["life line long, narrow, deep"]},
        client=fake,
    )
    assert result == {
        "Line of Life": {
            "Length": {"value": "long", "confidence": 1.0},
            "Width": {"value": "narrow", "confidence": 1.0},
            "Depth": {"value": "deep", "confidence": 1.0},
        },
    }


# ─── Unmapped prose feature -> skipped, not raised ───────────────────────


def test_unmapped_prose_feature_skipped_not_raised():
    fake = _FakeClient(content=_obs_response({
        "Line of Life": {"Length": {"value": "long"}},
    }))
    result = extract_observation(
        {
            "fingers": ["long and slender"],  # no ontology counterpart
            "life line": ["long"],
        },
        client=fake,
    )
    assert result == {"Line of Life": {"Length": {"value": "long", "confidence": 1.0}}}
    # only Line of Life was ever sent to the LLM -- "fingers" never reached the prompt
    sent_prompt = fake.completions.calls[0]["messages"][1]["content"]
    assert "Line of Life" in sent_prompt
    assert "Finger" not in sent_prompt


def test_completely_unknown_prose_key_also_skipped_not_raised():
    # A prose key not even present in _FEATURE_ALIAS at all (not one of
    # the 10 registered labels) -- .get() returns None the same way an
    # explicitly-None-mapped key does, so it takes the identical skip path.
    fake = _FakeClient(content=_obs_response({
        "Line of Life": {"Length": {"value": "long"}},
    }))
    result = extract_observation(
        {"aura": ["glowing brightly"], "life line": ["long"]},
        client=fake,
    )
    assert result == {"Line of Life": {"Length": {"value": "long", "confidence": 1.0}}}


# ─── JSON parse failure -> ValueError with snippet ───────────────────────


def test_json_parse_failure_raises_value_error_with_snippet():
    fake = _FakeClient(content="this is not valid json at all")
    with pytest.raises(ValueError, match="not valid json"):
        extract_observation({"life line": ["long"]}, client=fake)


def test_missing_observations_key_raises_value_error_with_snippet():
    fake = _FakeClient(content=json.dumps({"wrong_key": {}}))
    with pytest.raises(ValueError, match="observations"):
        extract_observation({"life line": ["long"]}, client=fake)


# ─── Empty feature_texts -> empty payload, no raise ──────────────────────


def test_empty_feature_texts_returns_empty_payload_no_llm_call():
    fake = _FakeClient(content="should never be read")
    result = extract_observation({}, client=fake)
    assert result == {}
    assert len(fake.completions.calls) == 0  # no call made at all -- nothing to attempt


def test_feature_texts_with_only_blank_strings_returns_empty_payload_no_llm_call():
    fake = _FakeClient(content="should never be read")
    result = extract_observation({"life line": ["", "   "]}, client=fake)
    assert result == {}
    assert len(fake.completions.calls) == 0


# ─── Confidence: prose hedging lowers it, else defaults to 1.0 ──────────


def test_hedged_prose_lowers_confidence():
    fake = _FakeClient(content=_obs_response({
        "Line of Head": {"Direction": {"value": "straight"}},
    }))
    result = extract_observation(
        {"head line": ["the head line is possibly straight"]},
        client=fake,
    )
    assert result["Line of Head"]["Direction"]["confidence"] == 0.6


def test_non_hedged_prose_defaults_confidence_to_one():
    fake = _FakeClient(content=_obs_response({
        "Line of Head": {"Direction": {"value": "straight"}},
    }))
    result = extract_observation(
        {"head line": ["the head line is straight"]},
        client=fake,
    )
    assert result["Line of Head"]["Direction"]["confidence"] == 1.0


# ─── LLM emits a feature outside the requested batch -> dropped ─────────


def test_llm_emitted_feature_outside_requested_batch_is_dropped():
    fake = _FakeClient(content=_obs_response({
        "Line of Life": {"Length": {"value": "long"}},
        "Line of Heart": {"Position": {"value": "high"}},  # never requested this call
    }))
    result = extract_observation({"life line": ["long"]}, client=fake)
    assert result == {"Line of Life": {"Length": {"value": "long", "confidence": 1.0}}}
