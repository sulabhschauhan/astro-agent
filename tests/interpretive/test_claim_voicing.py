"""
tests/interpretive/test_claim_voicing.py
S69 F-H P4 -- test suite for agent/interpretive/claim_voicing.py.

Fake OpenAI client classes (_FakeMessage/_FakeChoice/_FakeResponse/
_FakeCompletions/_FakeClient) are TRANSPLANTED from
tests/interpretive/test_palm_reading.py (same shapes, same
responses=[(content, exception), ...] call-order-indexed convention),
same lineage tests/interpretive/test_claim_extraction.py already
transplanted them from -- cited, not reinvented, since voice_claims'
`client` seam takes the identical client.chat.completions.create(...)
surface.
"""

from __future__ import annotations

import re

import pytest

from agent.interpretive import claim_voicing
from agent.interpretive.claim_extraction import Claim
from agent.interpretive.claim_voicing import VoiceResult, voice_claims

# ─── S70 F-G3: prompt content -- no verbatim exemplar sentences ─────────
#
# Pass-5 preflight's post-F-G re-run (diagnostics/pass5_preflight_S70.md,
# commit 908d325) found _VOICE_SYSTEM_PROMPT's own "model sentences"
# (verbatim-shared with palm_reading._EXEMPLAR_SENTENCES) were a standing
# echo-gravity source that F-G1/F-G2's retry-feed wiring could detect but
# not eliminate. F-G3 deletes them from the prompt entirely, replacing
# them with descriptive-only voice guidance. This test imports the two
# sentences from palm_reading (still the canonical exemplar-echo guard's
# own source of truth, unchanged by this prompt) rather than pasting them
# inline, so a future edit to either sentence can't silently desync the
# two modules without this test catching it.


def test_voice_system_prompt_contains_no_r2_exemplar_sentences():
    from agent.interpretive.palm_reading import _EXEMPLAR_SENTENCES

    for sentence in _EXEMPLAR_SENTENCES:
        assert sentence not in claim_voicing._VOICE_SYSTEM_PROMPT


# ─── S70 F-G4: adjacent-tag hard rule in the prompt ──────────────────────


def test_voice_system_prompt_has_adjacent_tag_hard_rule():
    prompt = claim_voicing._VOICE_SYSTEM_PROMPT
    assert "## Output format (voice tags)" in prompt
    tag_section = prompt.split("## Output format (voice tags)", 1)[1].split("## Scope", 1)[0]

    assert "Every tag MUST be preceded by a complete sentence of visible text" in tag_section
    assert "Never place two tags back-to-back with nothing between them" in tag_section

    # F-G3 hard constraint carries forward: zero quotable example text
    # anywhere in the tag-format section -- no quote-delimited run of
    # >=4 words (a real example sentence) may appear. Brace placeholders
    # like "{sentence}" / "{next sentence}" in the hard rule's own
    # format template are stripped before counting, since a placeholder
    # token is not quotable echo-source prose the way a real example
    # sentence would be.
    quoted_runs = re.findall(r'"([^"]*)"', tag_section)
    for run in quoted_runs:
        stripped = re.sub(r"\{[^}]*\}", "", run)
        word_count = len(re.findall(r"[A-Za-z']+", stripped))
        assert word_count < 4, f"quoted run reads as an example sentence: {run!r}"


# ─── Fake OpenAI client -- transplanted from test_palm_reading.py ────────


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
    """Records every call (`.calls`); `responses`, if given, is a list of
    (content, exception) tuples consumed in call order. Past the end of
    `responses`, the LAST entry is reused (clamped index) -- tests
    proving "never a 3rd call" must assert `len(.calls)` explicitly, not
    rely on this clamping to crash."""

    def __init__(
        self,
        content: str | None = None,
        exception: Exception | None = None,
        responses: list[tuple[str | None, Exception | None]] | None = None,
    ):
        self._content = content
        self._exception = exception
        self._responses = responses
        self.calls: list[dict] = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        if self._responses is not None:
            idx = min(len(self.calls) - 1, len(self._responses) - 1)
            content, exception = self._responses[idx]
            if exception is not None:
                raise exception
            return _FakeResponse(content)
        if self._exception is not None:
            raise self._exception
        return _FakeResponse(self._content)


class _FakeClient:
    def __init__(
        self,
        *,
        content: str | None = None,
        exception: Exception | None = None,
        responses: list[tuple[str | None, Exception | None]] | None = None,
    ):
        self.completions = _FakeCompletions(content=content, exception=exception, responses=responses)
        self.chat = type("_FakeChat", (), {"completions": self.completions})()


def _explosive_client() -> _FakeClient:
    """A client whose create() raises AssertionError if invoked at all --
    same belt-and-suspenders convention as test_palm_reading.py's own
    _explosive_client, for the "must not call the LLM" proofs below."""
    return _FakeClient(exception=AssertionError("voice_claims must not call the LLM here"))


# ─── Fixture builders ────────────────────────────────────────────────────


def _claim(
    claim_id: str = "C1",
    feature: str = "life line",
    chunk_id: str = "SHOULD_NEVER_APPEAR_CHUNK_ID",
    claim_text: str = "A long deep life line promises vitality.",
    valence: str = "supports",
    condition_text: str | None = None,
    observation_basis: str = "deep, long",
    excluded_from_voice: bool = False,
    exclusion_reason: str | None = None,
) -> Claim:
    return Claim(
        claim_id=claim_id, feature=feature, chunk_id=chunk_id, claim_text=claim_text,
        valence=valence, condition_text=condition_text, observation_basis=observation_basis,
        excluded_from_voice=excluded_from_voice, exclusion_reason=exclusion_reason,
    )


def _all_message_text(client: _FakeClient) -> str:
    """Every message content across every call the fake client received --
    a single haystack string for "must not appear anywhere" assertions."""
    return "\n".join(
        m["content"] for call in client.completions.calls for m in call["messages"]
    )


# ─── Input filter, end to end (messages actually sent) ──────────────────


def test_input_filter_excluded_dropped_corrective_capped_overflow_in_diagnostics_and_absent_from_prompt():
    claims = (
        _claim(claim_id="C1", claim_text="Claim one text.", valence="supports"),
        _claim(claim_id="C2", claim_text="Claim two excluded text.", valence="conditional",
               condition_text="unverified", excluded_from_voice=True, exclusion_reason="precondition unverified"),
        _claim(claim_id="C3", feature="fingers", claim_text="Claim three corrective text.", valence="corrective"),
        _claim(claim_id="C4", feature="thumb", claim_text="Claim four corrective overflow text.", valence="corrective"),
    )
    texts_by_feature = {"life line": "deep, long", "fingers": "long fingers", "thumb": "medium"}

    good_draft = (
        "An opening thought.[FLOW] "
        "Claim one text.[C1] "
        "Claim three corrective text.[C3] "
        "A closing thought.[FLOW]"
    )
    client = _FakeClient(content=good_draft)

    result = voice_claims(claims, texts_by_feature, client=client)

    assert result.diagnostics["excluded_count"] == 1
    assert result.diagnostics["corrective_overflow"] == ["C4"]
    assert result.diagnostics["included_claim_ids"] == ["C1", "C3"]

    sent_text = _all_message_text(client)
    assert "Claim one text." in sent_text
    assert "Claim three corrective text." in sent_text
    # Excluded and overflow claims must never reach the prompt.
    assert "Claim two excluded text." not in sent_text
    assert "Claim four corrective overflow text." not in sent_text
    assert "C2:" not in sent_text
    assert "C4:" not in sent_text


# ─── Prompt construction: no chunk_id / chunk text anywhere ──────────────


def test_prompt_never_contains_chunk_id():
    claims = (_claim(chunk_id="SHOULD_NEVER_APPEAR_CHUNK_ID_XYZ"),)
    texts_by_feature = {"life line": "deep, long"}
    good_draft = "A long deep life line promises vitality.[C1]"
    client = _FakeClient(content=good_draft)

    result = voice_claims(claims, texts_by_feature, client=client)

    assert result.validation_failures == ()
    sent_text = _all_message_text(client)
    assert "SHOULD_NEVER_APPEAR_CHUNK_ID_XYZ" not in sent_text


# ─── V-3: tag legality ────────────────────────────────────────────────────


def test_v3_untagged_text_fails_and_retry_fed_failure_text():
    claim = _claim()
    texts_by_feature = {"life line": "deep, long"}
    untagged = "A long deep life line promises vitality."  # no tag at all
    good = "A long deep life line promises vitality.[C1]"
    client = _FakeClient(responses=[(untagged, None), (good, None)])

    result = voice_claims((claim,), texts_by_feature, client=client)

    assert result.retry_used is True
    assert result.validation_failures == ()
    retry_messages = client.completions.calls[1]["messages"]
    correction = retry_messages[-1]["content"]
    assert "Your draft failed these checks" in correction
    assert "no recognized tag found" in correction


def test_v3_unknown_claim_id_tag_fails_persistent():
    claim = _claim(claim_id="C1")
    texts_by_feature = {"life line": "deep, long"}
    bad = "A long deep life line promises vitality.[C99]"
    client = _FakeClient(responses=[(bad, None), (bad, None)])

    result = voice_claims((claim,), texts_by_feature, client=client)

    assert any("does not resolve to an included claim_id" in f and "C99" in f for f in result.validation_failures)
    retry_messages = client.completions.calls[1]["messages"]
    assert "C99" in retry_messages[-1]["content"]
    assert len(client.completions.calls) == 2


def test_v3_adjacent_double_tag_fails_persistent():
    claim = _claim()
    texts_by_feature = {"life line": "deep, long"}
    # [C1] immediately followed by [OBS] with nothing between -- two tags
    # attached where exactly one is required.
    bad = "A long deep life line promises vitality.[C1][OBS]"
    client = _FakeClient(responses=[(bad, None), (bad, None)])

    result = voice_claims((claim,), texts_by_feature, client=client)

    assert any("adjacent tags with no sentence between them" in f for f in result.validation_failures)
    retry_messages = client.completions.calls[1]["messages"]
    assert "adjacent tags" in retry_messages[-1]["content"]


def test_v3_stray_bracket_token_fails_persistent():
    claim = _claim()
    texts_by_feature = {"life line": "deep, long"}
    bad = "A long deep life line promises vitality.[C1] Something else here.[NOTATAG]"
    client = _FakeClient(responses=[(bad, None), (bad, None)])

    result = voice_claims((claim,), texts_by_feature, client=client)

    assert any(
        "unrecognized bracket token" in f and "NOTATAG" in f for f in result.validation_failures
    )
    retry_messages = client.completions.calls[1]["messages"]
    assert "NOTATAG" in retry_messages[-1]["content"]


# ─── V-4: claim coverage ──────────────────────────────────────────────────


def test_v4_claim_never_cited_fails_then_clean_retry_clears():
    claim = _claim()
    texts_by_feature = {"life line": "deep, long"}
    bad = "An opening thought.[FLOW] A closing thought.[FLOW]"  # C1 never cited
    good = "A long deep life line promises vitality.[C1]"
    client = _FakeClient(responses=[(bad, None), (good, None)])

    result = voice_claims((claim,), texts_by_feature, client=client)

    assert result.retry_used is True
    assert result.validation_failures == ()
    assert result.diagnostics["first_attempt_failures"] == ["claim_coverage: claim_id(s) never cited: ['C1']"]


def test_v4_persistent_failure_populates_validation_failures():
    claim = _claim()
    texts_by_feature = {"life line": "deep, long"}
    bad = "An opening thought.[FLOW] A closing thought.[FLOW]"
    client = _FakeClient(responses=[(bad, None), (bad, None)])

    result = voice_claims((claim,), texts_by_feature, client=client)

    assert result.validation_failures == ("claim_coverage: claim_id(s) never cited: ['C1']",)


# ─── V-5: [FLOW] doctrine guard (S70 F-G4: [OBS] carved out) ────────────


def test_v5_needle_in_flow_sentence_fails():
    claim = _claim()
    texts_by_feature = {"life line": "deep, long"}
    bad = "The life line looks promising today.[FLOW] A long deep life line promises vitality.[C1]"
    client = _FakeClient(responses=[(bad, None), (bad, None)])

    result = voice_claims((claim,), texts_by_feature, client=client)

    assert any("doctrine_guard: [FLOW]" in f and "'life'" in f for f in result.validation_failures)


def test_v5_failures_never_labeled_obs():
    """New in S70 F-G4: when V-5 doctrine_guard failures are populated,
    none of them may be labeled [OBS] -- the carve-out means [OBS] can
    no longer appear in this failure class at all. Combines a
    FLOW-needle failure (still fails) with an OBS-needle sentence (must
    NOT contribute a failure) in the same draft."""
    claim = _claim()
    texts_by_feature = {"life line": "deep, long"}
    bad = (
        "The life line looks promising today.[FLOW] "
        "The life line is deep and long on your hand.[OBS] "
        "A long deep life line promises vitality.[C1]"
    )
    client = _FakeClient(responses=[(bad, None), (bad, None)])

    result = voice_claims((claim,), texts_by_feature, client=client)

    doctrine_failures = [f for f in result.validation_failures if f.startswith("doctrine_guard")]
    assert doctrine_failures
    assert not any("[OBS]" in f for f in doctrine_failures)


def test_v5_needle_in_obs_sentence_passes():
    """S70 F-G4: [OBS] segments are OUT OF SCOPE for the doctrine guard --
    an [OBS] sentence restating a confirmed observation while naming its
    own feature (e.g. "the life line is deep and long") is intended
    behavior, not a leak. This fixture is the SAME needle-in-[OBS]
    fixture the pre-F-G4 test asserted a failure on; it now must pass
    clean on the first draft (no retry)."""
    claim = _claim()
    texts_by_feature = {"life line": "deep, long"}
    good = "The life line is deep and long on your hand.[OBS] A long deep life line promises vitality.[C1]"
    client = _FakeClient(content=good)

    result = voice_claims((claim,), texts_by_feature, client=client)

    assert result.validation_failures == ()
    assert result.retry_used is False


def test_v5_same_needle_inside_claim_sentence_passes():
    claim = _claim()
    texts_by_feature = {"life line": "deep, long"}
    # "life" appears twice, but both occurrences are inside the [C1]
    # sentence itself -- V-5 only scans [FLOW] segments, so this
    # must PASS.
    good = "A long deep life line promises vitality and shapes your whole life path.[C1]"
    client = _FakeClient(content=good)

    result = voice_claims((claim,), texts_by_feature, client=client)

    assert result.validation_failures == ()
    assert result.retry_used is False


# ─── Validator ordering: V-3 gates V-4/V-5 ───────────────────────────────


def test_v3_failure_gates_v4_and_v5():
    claim = _claim()
    texts_by_feature = {"life line": "deep, long"}
    # Simultaneously: a V-3 violation (unknown claim id C99), a would-be
    # V-4 violation (C1 never cited), and a would-be V-5 violation
    # ("life" needle inside an [OBS] sentence) -- if V-4/V-5 were
    # evaluated despite the V-3 failure, their failure strings would
    # appear too. They must NOT.
    bad = "The life line is deep on your hand.[OBS] Some odd note.[C99]"
    client = _FakeClient(responses=[(bad, None), (bad, None)])

    result = voice_claims((claim,), texts_by_feature, client=client)

    assert result.validation_failures
    assert all(f.startswith("tag_legality") for f in result.validation_failures)
    assert not any("claim_coverage" in f for f in result.validation_failures)
    assert not any("doctrine_guard" in f for f in result.validation_failures)


# ─── Retry cap ───────────────────────────────────────────────────────────


def test_retry_cap_exactly_two_calls_never_three_no_raise():
    claim = _claim()
    texts_by_feature = {"life line": "deep, long"}
    bad = "An opening thought.[FLOW] A closing thought.[FLOW]"  # persistent V-4 failure
    # Only 2 responses provided -- if voice_claims ever made a 3rd call,
    # _FakeCompletions would silently reuse the 2nd (clamped index), so
    # the real proof is the call COUNT, not a crash.
    client = _FakeClient(responses=[(bad, None), (bad, None)])

    result = voice_claims((claim,), texts_by_feature, client=client)

    assert len(client.completions.calls) == 2
    assert result.diagnostics["call_count"] == 2
    assert result.retry_used is True
    assert result.validation_failures != ()


# ─── API exceptions ──────────────────────────────────────────────────────


def test_api_exception_on_first_call_raises_runtime_error_with_module_prefix():
    claim = _claim()
    texts_by_feature = {"life line": "deep, long"}
    client = _FakeClient(exception=RuntimeError("network down"))

    with pytest.raises(RuntimeError, match=r"claim_voicing: API call failed: network down"):
        voice_claims((claim,), texts_by_feature, client=client)

    assert len(client.completions.calls) == 1


def test_api_exception_on_retry_call_raises_runtime_error_with_module_prefix():
    claim = _claim()
    texts_by_feature = {"life line": "deep, long"}
    bad = "An opening thought.[FLOW] A closing thought.[FLOW]"  # triggers a retry
    client = _FakeClient(responses=[(bad, None), (None, RuntimeError("timeout"))])

    with pytest.raises(RuntimeError, match=r"claim_voicing: API retry call failed: timeout"):
        voice_claims((claim,), texts_by_feature, client=client)

    assert len(client.completions.calls) == 2


# ─── Empty included set ──────────────────────────────────────────────────


def test_empty_claims_tuple_skips_llm_call():
    client = _explosive_client()

    result = voice_claims((), {}, client=client)

    assert isinstance(result, VoiceResult)
    assert result.reading_text_tagged == ""
    assert result.validation_failures == ()
    assert result.retry_used is False
    assert result.diagnostics["skipped"] == "no included claims to voice"
    assert result.diagnostics["call_count"] == 0
    assert client.completions.calls == []


def test_all_claims_excluded_from_voice_skips_llm_call():
    claims = (
        _claim(claim_id="C1", excluded_from_voice=True, exclusion_reason="precondition unverified"),
    )
    client = _explosive_client()

    result = voice_claims(claims, {"life line": "deep, long"}, client=client)

    assert result.reading_text_tagged == ""
    assert result.diagnostics["skipped"] == "no included claims to voice"
    assert result.diagnostics["excluded_count"] == 1
    assert client.completions.calls == []


# ─── S70 F-G1: extra_validators injection seam ───────────────────────────
#
# extra_validators is a keyword-only tuple of caller-owned
# (tagged_draft: str) -> list[str] callables, run after V-3/V-4/V-5 on
# BOTH the first draft and the retry draft, merged into the same failure
# list that drives the single F2c retry. This is the seam only -- no
# wiring of any real validator (e.g. exemplar-echo) happens here, that is
# F-G2's job in palm_reading.py.


def test_extra_validator_fails_draft1_passes_draft2_retry_fires_and_clears():
    """(a) An extra validator fails the first draft (which otherwise
    passes V-3/V-4/V-5 cleanly) and passes the second -> retry fires, the
    correction message sent on retry contains the extra validator's
    failure string, and the final validation_failures is empty."""
    claim = _claim()
    texts_by_feature = {"life line": "deep, long"}
    draft1 = "A long deep life line promises vitality.[C1]"
    draft2 = "A long deep life line promises vitality once more.[C1]"
    client = _FakeClient(responses=[(draft1, None), (draft2, None)])

    def extra_validator(text: str) -> list[str]:
        return ["extra_check: found something bad"] if text == draft1 else []

    result = voice_claims(
        (claim,), texts_by_feature, client=client, extra_validators=(extra_validator,)
    )

    assert result.retry_used is True
    assert result.validation_failures == ()
    retry_messages = client.completions.calls[1]["messages"]
    correction = retry_messages[-1]["content"]
    assert "Your draft failed these checks" in correction
    assert "extra_check: found something bad" in correction


def test_extra_validator_fails_both_drafts_exactly_two_calls_no_third():
    """(b) An extra validator fails on BOTH drafts -> exactly 2 LLM
    calls (the hard cap, unchanged), non-empty validation_failures, no
    third call attempted."""
    claim = _claim()
    texts_by_feature = {"life line": "deep, long"}
    draft = "A long deep life line promises vitality.[C1]"
    client = _FakeClient(responses=[(draft, None), (draft, None)])

    def extra_validator(text: str) -> list[str]:
        return ["extra_check: always fails"]

    result = voice_claims(
        (claim,), texts_by_feature, client=client, extra_validators=(extra_validator,)
    )

    assert len(client.completions.calls) == 2
    assert result.diagnostics["call_count"] == 2
    assert result.retry_used is True
    assert result.validation_failures == ("extra_check: always fails",)


def test_extra_validator_raising_propagates_uncaught():
    """(c) A raising extra_validator is a CALLER bug, not a voice
    failure -- it must propagate uncaught, never be swallowed into
    validation_failures (a swallowed validator is a silently disabled
    guard)."""
    claim = _claim()
    texts_by_feature = {"life line": "deep, long"}
    draft = "A long deep life line promises vitality.[C1]"
    client = _FakeClient(content=draft)

    def bad_validator(text: str) -> list[str]:
        raise ValueError("caller bug: malformed extra validator")

    with pytest.raises(ValueError, match="caller bug: malformed extra validator"):
        voice_claims(
            (claim,), texts_by_feature, client=client, extra_validators=(bad_validator,)
        )

    # The first call still happened (the raise occurs during validation,
    # AFTER the LLM call) -- no retry was attempted since the exception
    # propagates before the retry branch is ever reached.
    assert len(client.completions.calls) == 1


def test_default_extra_validators_empty_tuple_zero_behavior_change():
    """(d) Omitting extra_validators entirely (the default `()`) must
    reproduce the exact pre-F-G1 happy-path outcome, byte-for-byte --
    same shape as test_v5_same_needle_inside_claim_sentence_passes above,
    with an added guard that no extra_validator_failures diagnostics key
    is ever introduced when nothing was supplied."""
    claim = _claim()
    texts_by_feature = {"life line": "deep, long"}
    good = "A long deep life line promises vitality.[C1]"
    client = _FakeClient(content=good)

    result = voice_claims((claim,), texts_by_feature, client=client)

    assert result.validation_failures == ()
    assert result.retry_used is False
    assert result.diagnostics["call_count"] == 1
    assert "extra_validator_failures" not in result.diagnostics
    assert "first_attempt_failures" not in result.diagnostics


def test_extra_validator_failures_recorded_in_diagnostics_first_attempt_only():
    """(e) A first-draft-only extra-validator failure is recorded under
    its own diagnostics["extra_validator_failures"] key (the first-
    attempt list, not the retry draft's), alongside the existing
    first_attempt_failures key -- both populated with the SAME single
    failure string here since no V-3/V-4/V-5 failure co-occurred."""
    claim = _claim()
    texts_by_feature = {"life line": "deep, long"}
    draft1 = "A long deep life line promises vitality.[C1]"
    draft2 = "A long deep life line promises vitality, restated plainly.[C1]"
    client = _FakeClient(responses=[(draft1, None), (draft2, None)])

    def extra_validator(text: str) -> list[str]:
        return ["extra_check: found echo"] if text == draft1 else []

    result = voice_claims(
        (claim,), texts_by_feature, client=client, extra_validators=(extra_validator,)
    )

    assert result.diagnostics["extra_validator_failures"] == ["extra_check: found echo"]
    assert result.diagnostics["first_attempt_failures"] == ["extra_check: found echo"]
