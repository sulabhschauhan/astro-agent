"""
tests/interpretive/test_palm_reading.py

Ring 2 file for agent/interpretive/palm_reading.py (CLAUDE.md Session 65
"T4 golden semantics" lock). Zero live API calls, zero live ChromaDB.

S69 F-H P5b UPDATE: palm_reading.py's single-call generation is retired,
replaced by a two-stage pipeline (claim_extraction.extract_claims ->
claim_voicing.voice_claims). The stub pattern changes accordingly: a
_FakeClient's `responses=[...]` queue must now answer ONE valid Stage-1
JSON extraction call PER ATTEMPTED FEATURE (registry order), followed by
ONE Stage-2 tagged-voice-text call -- see `_two_stage_setup`/
`_single_feature_client` below, the shared helpers built for this
alignment pass (one helper, not 34 hand-edited stubs, per the instructing
prompt). Stage 2's tag vocabulary is `{[C<n>], [OBS], [FLOW]}` -- NOT the
old `{[OBS], [<chunk_id>]}` vocabulary; V-5 (claim_voicing's own doctrine
guard) fails any [FLOW]/[OBS] sentence naming a palm-feature noun, so
every stub below keeps feature-noun mentions ("life", "heart", etc.)
confined to [C<n>]-tagged sentences.

Retrieval stubbing (_FakeSearch, monkeypatched at `palm_reading.search`)
is UNCHANGED -- retrieval and the support gate are untouched by F-H.

Retired-validator tests: V-1 (_check_tag_completeness) / V-2
(_check_anchor_legality) / _check_feature_coverage / _run_ring1_checks
are no longer CALLED by generate_palm_reading (see palm_reading.py's own
module docstring, S69 F-H P5 section) but remain DEFINED -- direct unit
tests of those functions (item 16/17 below) stay passing unmodified.
INTEGRATION tests that exercised them THROUGH generate_palm_reading are
marked skip (reason references this retirement), not deleted, so
close-out sees the full inventory. One additional integration test
(per-feature prompt-assembly dedupe/display) is ALSO skipped -- discovered
during this alignment pass, not previously flagged in P5's own report:
_assemble_retrieved_passages (the old single-prompt assembler) is no
longer called either, for the same reason; flagged in this prompt's own
report, not silently expanded scope.
"""
from __future__ import annotations

import inspect
import json

import pytest

from agent.interpretive import palm_reading
from agent.interpretive.palm_reading import (
    PalmReadingResult,
    ValidationReport,
    generate_palm_reading,
)
from agent.interpretive.claim_extraction import Claim
from agent.prompt_builder import DISCLAIMER
from ingestion.query_engine import multi_source_search


# ─── Fakes (unchanged from pre-P5) ──────────────────────────────────────


class _FakeSearch:
    """Drop-in replacement for query_engine.search, injected via
    monkeypatch.setattr(palm_reading, "search", ...). Records every call
    (`.calls`) and returns a fixed, configurable chunk list."""

    def __init__(
        self,
        results: list[dict],
        raise_for=None,
        exception: Exception | None = None,
    ):
        self._results = results
        self._raise_for = raise_for
        self._exception = exception or RuntimeError("simulated search failure")
        self.calls: list[dict] = []

    def __call__(self, question, n_results=None, **filters):
        self.calls.append({"question": question, "n_results": n_results, **filters})
        if self._raise_for is not None and self._raise_for(question):
            raise self._exception
        return self._results


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
    (content, exception) tuples consumed in call order -- lets a single
    fake answer every Stage-1/Stage-2 call differently."""

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
    """Minimal stand-in for openai.OpenAI, injected via
    generate_palm_reading's `client` seam."""

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
    belt-and-suspenders proof for fail-closed/zero-call cases, where
    `.completions.calls == []` is the real proof."""
    return _FakeClient(exception=AssertionError("LLM call must not fire for this case"))


def _chunk(
    text: str = "A long, unbroken life line indicates steady vitality.",
    book_name: str = "cheiroslanguageo00chei_1",
    page_ref: int = 42,
    score: float = 0.71,
    chunk_id: str = "c1",
) -> dict:
    """9-field dict shape matching query_engine.search()'s real return type."""
    return {
        "chunk_id": chunk_id,
        "text": text,
        "score": score,
        "book_name": book_name,
        "topic": "life_line",
        "page_type": "body",
        "language": "en",
        "page_ref": page_ref,
        "image_path": "",
    }


# ─── S69 F-H P5b: two-stage response builders ──────────────────────────
#
# Stage 1 (claim_extraction.extract_claims) makes one call per ATTEMPTED
# feature (registry order, only features with >=1 gated chunk); Stage 2
# (claim_voicing.voice_claims) makes exactly one whole-reading call after
# that. These helpers build the `responses=[...]` sequence _FakeClient
# needs to answer BOTH stages cleanly, so each test can focus on its own
# actual target (a display-check failure, a sources shape, etc.) instead
# of hand-rolling the two-stage shape 30+ times.


def _stage1_claim(chunk: dict, claim_id: str) -> dict:
    """One Stage-1 claim dict citing `chunk`. claim_text defaults to the
    chunk's own text verbatim -- trivially satisfies claim_extraction's
    E-3 paraphrase-overlap floor (overlap of identical text is 1.0)."""
    return {
        "claim_id": claim_id,
        "chunk_id": chunk["chunk_id"],
        "claim_text": chunk["text"],
        "valence": "supports",
        "condition_text": None,
        "observation_basis": "observed",
    }


def _two_stage_setup(
    feature_chunks: dict[str, list[dict]],
    voice_text_builder,
) -> tuple[_FakeClient, dict[str, list[str]]]:
    """feature_chunks: {feature: [chunk, ...]} -- the chunks this test's
    _FakeSearch/support-gate setup is expected to leave GATED for each
    feature (the test author already knows this, same as this file's
    pre-P5 "N observed features -> N search calls" comments). Builds one
    valid Stage-1 JSON response per feature (registry order, one claim
    per chunk), then calls voice_text_builder(claim_ids) -- claim_ids is
    {feature: ["C1", "C2", ...]} in the SAME global numbering order
    extract_claims itself assigns -- to get the Stage-2 response text.
    Returns (client, claim_ids)."""
    ordered_features = [f for f in palm_reading._FEATURE_REGISTRY if f in feature_chunks]
    claim_ids: dict[str, list[str]] = {}
    counter = 1
    stage1_responses: list[tuple[str, None]] = []
    for feature in ordered_features:
        chunks = feature_chunks[feature]
        ids = []
        claims = []
        for chunk in chunks:
            cid = f"C{counter}"
            counter += 1
            ids.append(cid)
            claims.append(_stage1_claim(chunk, cid))
        claim_ids[feature] = ids
        stage1_responses.append((json.dumps({"feature": feature, "claims": claims}), None))

    voice_text = voice_text_builder(claim_ids)
    client = _FakeClient(responses=stage1_responses + [(voice_text, None)])
    return client, claim_ids


def _single_feature_client(feature: str, chunk: dict, voice_text: str) -> _FakeClient:
    """Convenience for the common single-feature, single-chunk case.
    `voice_text` should cite the sole claim as "[C1]" (always C1 in this
    shape -- the only claim, first and only attempted feature)."""
    client, _ = _two_stage_setup({feature: [chunk]}, lambda ids: voice_text)
    return client


# S67 R3: LIFE-LINE-ONLY stub -- most consuming tests observe exactly one
# feature (life line). Feature-noun content ("life line") is confined to
# the [C1]-tagged sentence; the [FLOW] sentence carries no needle words
# (V-5 in claim_voicing.py fails any [FLOW]/[OBS] sentence naming a
# feature noun).
_CLEAN_STUB_TEXT = (
    "This is a hand that reflects genuine physical staying power, "
    "carried forward with quiet, steady confidence, meeting every "
    "demand without being easily worn down.[FLOW] "
    "A long, unbroken life line indicates steady vitality and "
    "resilience.[C1]"
)


# ─── Items 1-2: fail-closed ValueError battery (hardest case first) ────


def test_both_none_with_hand_detail_still_raises_value_error(monkeypatch):
    """Hardest fail-closed case: partial input (hand_detail alone) must
    not slip through the both-None guard."""
    fake_search = _FakeSearch([])
    monkeypatch.setattr(palm_reading, "search", fake_search)
    client = _explosive_client()

    with pytest.raises(ValueError, match="palm_left/palm_right"):
        generate_palm_reading(
            None, None, hand_detail="Long fingers, square palm.", client=client
        )

    assert fake_search.calls == []
    assert client.completions.calls == []


def test_both_none_no_hand_detail_raises_value_error(monkeypatch):
    fake_search = _FakeSearch([])
    monkeypatch.setattr(palm_reading, "search", fake_search)
    client = _explosive_client()

    with pytest.raises(ValueError, match="palm_left/palm_right"):
        generate_palm_reading(None, None, client=client)

    assert fake_search.calls == []
    assert client.completions.calls == []


# ─── Item 3: jargon injection, case-insensitivity + word boundary ──────

_JARGON_STUB_TEXT = (
    "Your LAGNA reveals strong ambition, while a promising Antardasha this "
    "season brings real opportunity. A gentle yoga forming across your "
    "palm suggests balance and steady growth, and anyone with a bold "
    "yogart sign on their hand should feel encouraged. It is a warm, "
    "positive outlook for the months ahead, with room to deepen important "
    "relationships and explore new creative directions along the "
    "way.[FLOW] "
    "A long, unbroken life line indicates steady vitality.[C1]"
)


def test_jargon_injection_case_insensitive_and_word_boundary(monkeypatch):
    """S70 F-G2: jargon_blacklist now feeds Stage 2's own retry via the
    extra_validators seam. This fixture supplies only ONE Stage-2
    response (`_single_feature_client`), so the retry reuses the SAME
    still-failing draft -- the failure string appears TWICE (once per
    attempt) rather than once, and stage2_retry_used flips True. This is
    the intended behavior change (CLAUDE.md F-G residual, closed by
    F-G1/F-G2), not a regression."""
    chunk = _chunk()
    monkeypatch.setattr(palm_reading, "search", _FakeSearch([chunk]))
    client = _single_feature_client("life line", chunk, _JARGON_STUB_TEXT)

    result = generate_palm_reading(
        palm_left="LIFE LINE: A long life line with a gentle curve.", palm_right=None, client=client
    )

    assert result.validation.passed is False
    assert result.stage2_retry_used is True
    assert all(f.startswith("jargon_blacklist: found ") for f in result.validation.failures)
    assert not any("self_help_blacklist" in f for f in result.validation.failures)
    failure = result.validation.failures[0]
    hits = {h.strip() for h in failure.removeprefix("jargon_blacklist: found ").split(",")}
    assert hits == {"lagna", "antardasha", "yoga"}

    raw_matches = palm_reading._JARGON_PATTERN.findall(_JARGON_STUB_TEXT)
    assert raw_matches.count("yoga") == 1


# ─── Item 4: fabricated year vs. supported year (boundary pair) ────────

_YEAR_STUB_TEXT = (
    "A period of expansion opens around 2031, bringing new opportunities "
    "for growth and travel. Steady resilience carries through the "
    "changes ahead, with a natural warmth that draws others close. Trust "
    "your instincts during this stretch and lean into new connections -- "
    "they carry real long-term value.[FLOW] "
    "A steady life line with no numeric markers.[C1]"
)


def test_fabricated_year_absent_from_context_fails(monkeypatch):
    chunk = _chunk(text="A steady life line with no numeric markers.")
    monkeypatch.setattr(palm_reading, "search", _FakeSearch([chunk]))
    client = _single_feature_client("life line", chunk, _YEAR_STUB_TEXT)

    result = generate_palm_reading(
        palm_left="LIFE LINE: A steady, long life line -- no dates mentioned.",
        palm_right=None,
        client=client,
    )

    assert result.validation.passed is False
    assert any(
        "unsupported_dates" in f and "2031" in f for f in result.validation.failures
    )


def test_year_supported_by_retrieved_chunk_does_not_fail(monkeypatch):
    """Companion/boundary case: the SAME cited year, but now present in a
    retrieved Cheiro chunk -- must NOT trip the date validator."""
    chunk = _chunk(text="Cheiro documented a comparable case in 2031 involving a strong life line.")
    monkeypatch.setattr(palm_reading, "search", _FakeSearch([chunk]))
    voice_text = "Cheiro documented a comparable case in 2031 involving a strong life line.[C1]"
    client = _single_feature_client("life line", chunk, voice_text)

    result = generate_palm_reading(
        palm_left="LIFE LINE: A steady, long life line.", palm_right=None, client=client
    )

    assert not any("unsupported_dates" in f for f in result.validation.failures)
    assert result.validation.passed is True


# ─── Item 5: length rail ────────────────────────────────────────────────

# 700 "word" tokens + "Noted." = exactly 701 words after tag-stripping.
_LONG_STUB_TEXT = " ".join(["word"] * 700) + ".[FLOW] Noted.[C1]"


def test_length_over_700_words_fails(monkeypatch):
    chunk = _chunk()
    monkeypatch.setattr(palm_reading, "search", _FakeSearch([chunk]))
    client = _single_feature_client("life line", chunk, _LONG_STUB_TEXT)

    result = generate_palm_reading(
        palm_left="LIFE LINE: A long life line.", palm_right=None, client=client
    )

    assert result.validation.passed is False
    assert any(f.startswith("length_guard:") for f in result.validation.failures)
    assert any("701" in f for f in result.validation.failures)


# ─── Item 6: empty retrieval -- S69 F-H P5 NEW CONTRACT ────────────────
#
# The OLD "_LOW_CONFIDENCE_ADDENDUM, still makes exactly 1 LLM call" path
# is RETIRED (palm_reading.py's own module docstring, S69 F-H P5's NOTED
# BEHAVIOR CHANGE): zero gated chunks -> Stage 1 has nothing to attempt
# (empty, non-raising) -> Stage 2 has nothing to voice (empty,
# non-raising) -> ZERO LLM calls anywhere, decline-block-plus-disclaimer
# only.

_ALL_ABSENT_LEFT = (
    "HAND SHAPE: Square palm.\n"
    "FINGERS: Not clearly visible.\n"
    "THUMB: Not visible.\n"
    "LIFE LINE: Not clearly visible.\n"
    "HEAD LINE: Not clearly visible.\n"
    "HEART LINE: Not clearly visible.\n"
    "FATE LINE: Not clearly visible.\n"
    "OTHER LINES: Not clearly visible.\n"
    "MOUNTS: Unremarkable.\n"
    "MARKS: No clear marks visible."
)


def test_empty_retrieval_yields_zero_llm_calls_and_full_decline(monkeypatch):
    fake_search = _FakeSearch([])
    monkeypatch.setattr(palm_reading, "search", fake_search)
    client = _explosive_client()

    result = generate_palm_reading(
        palm_left="LIFE LINE: A long, deep life line.", palm_right=None, client=client
    )

    # 1 observed feature (life line) -> 1 search call, even though it
    # returns nothing; Stage 1/Stage 2 never call the LLM at all.
    assert len(fake_search.calls) == 1
    assert client.completions.calls == []
    assert result.validation.passed is True
    assert result.sources == ()
    assert DISCLAIMER in result.reading_text
    # life line: observed with a real (non-absence) quality but zero
    # surviving chunks -> gate-unsupported. The other 9 registry
    # features: never mentioned at all -> also gate-unsupported (not
    # genuine-negative-absence, which requires >=1 mentioning source).
    # All 10 land in the decline block.
    expected_decline = palm_reading._build_decline_block(palm_reading._FEATURE_REGISTRY)
    assert expected_decline in result.reading_text


def test_absence_rule_all_features_absent_yields_zero_search_and_llm_calls(monkeypatch):
    """(13a) 0 search calls, 0 LLM calls. Of the 16 registry features: 7
    (life/head/heart/fate/thumb/fingers/marks) are genuine negative
    absence (each is absence-phrased on its own mentioning source) --
    exempt from the decline block, nothing to support, nothing to
    decline. The other 9 (sun line + all 8 mounts) are sub-features
    NEVER NAMED at all (OTHER LINES/MOUNTS present but say neither
    "sun" nor any individual mount name) -- NOT genuine absence (that
    requires an actual mentioning source), so they land in unsupported_
    features and the decline block, same as before P5's wiring."""
    fake_search = _FakeSearch([_chunk()])
    monkeypatch.setattr(palm_reading, "search", fake_search)
    client = _explosive_client()

    result = generate_palm_reading(palm_left=_ALL_ABSENT_LEFT, palm_right=None, client=client)

    assert fake_search.calls == []
    assert client.completions.calls == []
    assert result.sources == ()
    assert result.validation.passed is True
    assert DISCLAIMER in result.reading_text
    expected_unsupported = tuple(
        f for f in palm_reading._FEATURE_REGISTRY
        if f == "sun line" or f.startswith("mount of")
    )
    assert result.unsupported_features == expected_unsupported
    expected_decline = palm_reading._build_decline_block(result.unsupported_features)
    assert expected_decline in result.reading_text


def test_zero_support_path_routes_to_zero_calls_with_full_decline(monkeypatch):
    """(14e) Search DOES return a chunk (not empty), but it fails the
    needle check -- routes to the SAME zero-call path as genuinely empty
    retrieval, with the full decline block (every registry feature,
    since none survived and none were absence-phrased)."""
    off_topic_chunk = _chunk(
        text="Chapter II lists the seven principal lines of the hand.",
        page_ref=120, score=0.65, chunk_id="offtopic",
    )
    monkeypatch.setattr(palm_reading, "search", _FakeSearch([off_topic_chunk]))
    client = _explosive_client()

    result = generate_palm_reading(
        palm_left="LIFE LINE: A long life line.", palm_right=None, client=client
    )

    assert client.completions.calls == []
    assert result.supported_features == ()
    assert result.unsupported_features == palm_reading._FEATURE_REGISTRY
    assert "A note on what I have not interpreted" in result.reading_text
    assert result.validation.passed is True
    assert result.sources == ()


# ─── Item 7: happy path, left-only ──────────────────────────────────────


def test_happy_path_left_only(monkeypatch):
    chunk = _chunk()
    monkeypatch.setattr(palm_reading, "search", _FakeSearch([chunk]))
    client = _single_feature_client("life line", chunk, _CLEAN_STUB_TEXT)

    result = generate_palm_reading(
        palm_left="LIFE LINE: A long, deep life line with a gentle curve.",
        palm_right=None,
        client=client,
    )

    assert result.validation.passed is True
    assert result.validation.failures == ()
    assert result.reading_text.endswith(DISCLAIMER)
    assert result.reading_text.count(DISCLAIMER) == 1
    assert DISCLAIMER not in _CLEAN_STUB_TEXT


# ─── Item 8: Stage-1 client failure -> RuntimeError propagates ─────────


def test_stage1_client_raises_becomes_runtime_error(monkeypatch):
    """S69 F-H P5: with a real (non-empty) retrieval, a client that
    always raises causes Stage 1's OWN all-features-failed RuntimeError
    to propagate uncaught -- the OLD single-call wrapper's "GPT-4o
    reading-generation call failed" message no longer exists; this is
    claim_extraction's own message now."""
    chunk = _chunk()
    monkeypatch.setattr(palm_reading, "search", _FakeSearch([chunk]))
    client = _FakeClient(exception=ConnectionError("simulated network failure"))

    with pytest.raises(RuntimeError, match="claim_extraction.extract_claims"):
        generate_palm_reading(palm_left="LIFE LINE: A long life line.", palm_right=None, client=client)

    # 1 attempted feature (life line) -> first call raises; no retry is
    # attempted (an API exception on the FIRST call skips Stage 1's own
    # retry entirely, per claim_extraction.py's own contract).
    assert len(client.completions.calls) == 1


# ─── Item 9: LLM-call-count invariant when everything is clean ────────
# NOTE (S69 F-H P5): the OLD "exactly 1 LLM call" invariant was about the
# single-call architecture's own F2c retry. The NEW invariant is "exactly
# N+1 calls, no extra retries" (N = attempted Stage-1 features, +1 for
# Stage 2) -- this test's fixture observes 2 features (life line, heart
# line) to prove the invariant holds across multiple Stage-1 calls.

_TWO_FEATURE_CHUNK = _chunk(
    text=(
        "A long, unbroken life line paired with a well-formed heart line "
        "together suggest steady character."
    ),
    chunk_id="cheiroslanguageo00chei_1_p42_c1",
)

_CLEAN_TWO_FEATURE_STUB_TEXT = (
    "This is a hand that carries itself with calm, quiet confidence.[FLOW] "
    "A long, unbroken life line paired with a well-formed heart line "
    "together suggest steady character.[C1] "
    "This same quality of steady character carries through "
    "consistently.[C2]"
)


def test_exactly_n_plus_one_llm_calls_when_first_draft_passes(monkeypatch):
    # 2 observed features (life line from palm_left, heart line from
    # palm_right) -> 2 search calls, 2 Stage-1 calls, 1 Stage-2 call.
    fake_search = _FakeSearch([_TWO_FEATURE_CHUNK])
    monkeypatch.setattr(palm_reading, "search", fake_search)
    client, _ = _two_stage_setup(
        {"life line": [_TWO_FEATURE_CHUNK], "heart line": [_TWO_FEATURE_CHUNK]},
        lambda ids: _CLEAN_TWO_FEATURE_STUB_TEXT,
    )

    result = generate_palm_reading(
        palm_left="LIFE LINE: A long life line.",
        palm_right="HEART LINE: A curved heart line.",
        client=client,
    )

    assert len(fake_search.calls) == 2
    assert len(client.completions.calls) == 3
    assert result.validation.passed is True
    assert result.validation.warnings == ()
    assert result.retry_used is False


# ─── Item 9b: retry_used compat -- OR-composition across both stages ───
# S69 F-H P5: `retry_used` (compat) = stage1 retry OR stage2 retry.
# These tests prove the OR-composition from EITHER side, plus the
# persistent-failure and retry-call-exception paths -- Stage 2's OWN
# validator logic (V-3/V-4/V-5) is already exhaustively tested in
# tests/interpretive/test_claim_voicing.py; these are INTEGRATION proofs
# that palm_reading.py surfaces the retry correctly, not re-derivations
# of claim_voicing's own internal logic.


def test_retry_used_true_when_stage1_retries(monkeypatch):
    """An E-1-illegal first Stage-1 response, corrected on retry ->
    stage1_retry_features names the feature, stage2_retry_used stays
    False, retry_used (compat) is True."""
    chunk = _chunk()
    monkeypatch.setattr(palm_reading, "search", _FakeSearch([chunk]))

    bad_stage1 = json.dumps({"feature": "life line", "claims": [
        {"claim_id": "x", "chunk_id": "not-a-real-chunk", "claim_text": chunk["text"],
         "valence": "supports", "condition_text": None, "observation_basis": "observed"},
    ]})
    good_stage1 = json.dumps({"feature": "life line", "claims": [
        {"claim_id": "x", "chunk_id": chunk["chunk_id"], "claim_text": chunk["text"],
         "valence": "supports", "condition_text": None, "observation_basis": "observed"},
    ]})
    voice_text = "A long, unbroken life line indicates steady vitality.[C1]"
    client = _FakeClient(responses=[(bad_stage1, None), (good_stage1, None), (voice_text, None)])

    result = generate_palm_reading(
        palm_left="LIFE LINE: A long life line.", palm_right=None, client=client
    )

    assert len(client.completions.calls) == 3  # Stage-1 first + retry, Stage-2 once
    assert result.stage1_retry_features == ("life line",)
    assert result.stage2_retry_used is False
    assert result.retry_used is True
    assert result.validation.passed is True


def test_retry_used_true_when_stage2_retries(monkeypatch):
    """A V-4 claim-coverage miss on the first voice draft, corrected on
    retry -> stage1_retry_features stays empty, stage2_retry_used is
    True, retry_used (compat) is True."""
    chunk = _chunk()
    monkeypatch.setattr(palm_reading, "search", _FakeSearch([chunk]))
    stage1 = json.dumps({"feature": "life line", "claims": [
        {"claim_id": "x", "chunk_id": chunk["chunk_id"], "claim_text": chunk["text"],
         "valence": "supports", "condition_text": None, "observation_basis": "observed"},
    ]})
    voice_miss = "An opening thought.[FLOW] A closing thought.[FLOW]"  # never cites C1
    voice_clean = "A long, unbroken life line indicates steady vitality.[C1]"
    client = _FakeClient(responses=[(stage1, None), (voice_miss, None), (voice_clean, None)])

    result = generate_palm_reading(
        palm_left="LIFE LINE: A long life line.", palm_right=None, client=client
    )

    assert len(client.completions.calls) == 3  # Stage-1 once, Stage-2 first + retry
    assert result.stage1_retry_features == ()
    assert result.stage2_retry_used is True
    assert result.retry_used is True
    assert result.validation.passed is True


def test_stage2_persistent_failure_stays_failed_no_third_stage2_call(monkeypatch):
    """Stage 2's own hard 2-call retry cap: both voice drafts miss claim
    coverage -> validation.passed=False (fail-closed, not raised),
    retry_used/stage2_retry_used both True, no third Stage-2 call is
    ever attempted."""
    chunk = _chunk()
    monkeypatch.setattr(palm_reading, "search", _FakeSearch([chunk]))
    stage1 = json.dumps({"feature": "life line", "claims": [
        {"claim_id": "x", "chunk_id": chunk["chunk_id"], "claim_text": chunk["text"],
         "valence": "supports", "condition_text": None, "observation_basis": "observed"},
    ]})
    voice_miss = "An opening thought.[FLOW] A closing thought.[FLOW]"
    client = _FakeClient(responses=[(stage1, None), (voice_miss, None), (voice_miss, None)])

    result = generate_palm_reading(
        palm_left="LIFE LINE: A long life line.", palm_right=None, client=client
    )

    # Stage-1 once + Stage-2 first + Stage-2 retry = 3 calls; a 4th
    # (third Stage-2 attempt) must never happen -- only 3 responses were
    # queued, and the fake would silently reuse the last one if a 4th
    # call occurred, so the real proof is the call COUNT.
    assert len(client.completions.calls) == 3
    assert result.validation.passed is False
    assert result.stage2_retry_used is True
    assert result.retry_used is True


def test_stage2_retry_call_raises_becomes_runtime_error(monkeypatch):
    """Stage 2's retry call itself raising propagates as claim_voicing's
    own RuntimeError, uncaught -- no third call is ever attempted."""
    chunk = _chunk()
    monkeypatch.setattr(palm_reading, "search", _FakeSearch([chunk]))
    stage1 = json.dumps({"feature": "life line", "claims": [
        {"claim_id": "x", "chunk_id": chunk["chunk_id"], "claim_text": chunk["text"],
         "valence": "supports", "condition_text": None, "observation_basis": "observed"},
    ]})
    voice_miss = "An opening thought.[FLOW] A closing thought.[FLOW]"
    client = _FakeClient(responses=[
        (stage1, None), (voice_miss, None), (None, ConnectionError("simulated network failure on retry")),
    ])

    with pytest.raises(RuntimeError, match="claim_voicing: API retry call failed"):
        generate_palm_reading(palm_left="LIFE LINE: A long life line.", palm_right=None, client=client)

    assert len(client.completions.calls) == 3


# ─── Item 10: Cheiro book filter ────────────────────────────────────────


def test_search_filters_to_canonical_cheiro_book(monkeypatch):
    source = inspect.getsource(multi_source_search)
    assert "cheiroslanguageo00chei_1" in source
    assert palm_reading._CHEIRO_BOOK == "cheiroslanguageo00chei_1"

    chunk = _chunk()
    fake_search = _FakeSearch([chunk])
    monkeypatch.setattr(palm_reading, "search", fake_search)
    client = _single_feature_client("life line", chunk, _CLEAN_STUB_TEXT)

    generate_palm_reading(palm_left="LIFE LINE: A long life line.", palm_right=None, client=client)

    assert len(fake_search.calls) == 1
    assert fake_search.calls[0]["book_name"] == palm_reading._CHEIRO_BOOK
    assert fake_search.calls[0]["n_results"] == 3  # production default, dogfood flag off


def test_search_fetches_30_when_dogfood_capture_flag_on(monkeypatch):
    """(S84) ASTRO_DOGFOOD_CAPTURE=1 restores the wider 30-candidate fetch
    for the near-miss margin log. _DOGFOOD_CAPTURE is computed once at
    import time, so monkeypatch.setenv alone (after import) would not
    retroactively flip it -- the module attribute itself is monkeypatched
    directly, same pattern _FEATURE_PAGE_FILTER_ENABLED tests already use
    elsewhere in this file. setenv is included anyway for readers, even
    though it's the attribute patch doing the actual work."""
    monkeypatch.setenv("ASTRO_DOGFOOD_CAPTURE", "1")
    monkeypatch.setattr(palm_reading, "_DOGFOOD_CAPTURE", True)
    chunk = _chunk()
    fake_search = _FakeSearch([chunk])
    monkeypatch.setattr(palm_reading, "search", fake_search)
    client = _single_feature_client("life line", chunk, _CLEAN_STUB_TEXT)

    generate_palm_reading(palm_left="LIFE LINE: A long life line.", palm_right=None, client=client)

    assert len(fake_search.calls) == 1
    assert fake_search.calls[0]["n_results"] == 30


# ─── S82: page-range gate rewired to one Chroma-level call ─────────────


def test_page_range_gate_zero_match_yields_one_call_no_retry_and_decline(monkeypatch):
    """(S82a) HARDEST CASE: a feature WITH a verified range (life line)
    whose single page_ref-filtered search returns nothing must NOT retry
    or fall back to a second unfiltered call -- this is exactly the case
    the old post-filter's fallback used to cover, and it's the whole
    point of the one-call rewire."""
    monkeypatch.setattr(palm_reading, "_FEATURE_PAGE_FILTER_ENABLED", True)
    fake_search = _FakeSearch([])
    monkeypatch.setattr(palm_reading, "search", fake_search)
    client = _explosive_client()

    result = generate_palm_reading(
        palm_left="LIFE LINE: A long, deep life line.", palm_right=None, client=client
    )

    assert len(fake_search.calls) == 1
    assert fake_search.calls[0]["page_ref"] == palm_reading._FEATURE_PAGE_RANGES["life line"]
    assert client.completions.calls == []
    assert result.validation.passed is True
    expected_decline = palm_reading._build_decline_block(palm_reading._FEATURE_REGISTRY)
    assert expected_decline in result.reading_text


def test_page_range_gate_pushes_verified_range_into_single_call(monkeypatch):
    """(S82b) A feature with a verified range -> exactly 1 call whose
    recorded page_ref is asserted against the loaded map itself, not a
    hardcoded pair."""
    monkeypatch.setattr(palm_reading, "_FEATURE_PAGE_FILTER_ENABLED", True)
    chunk = _chunk()
    fake_search = _FakeSearch([chunk])
    monkeypatch.setattr(palm_reading, "search", fake_search)
    client = _single_feature_client("life line", chunk, _CLEAN_STUB_TEXT)

    generate_palm_reading(palm_left="LIFE LINE: A long life line.", palm_right=None, client=client)

    assert len(fake_search.calls) == 1
    assert fake_search.calls[0]["page_ref"] == palm_reading._FEATURE_PAGE_RANGES["life line"]
    assert fake_search.calls[0]["book_name"] == palm_reading._CHEIRO_BOOK
    assert fake_search.calls[0]["n_results"] == 3  # production default, dogfood flag off


def test_page_range_gate_null_range_feature_omits_page_ref_key(monkeypatch):
    """(S82c) markings/other features has a verified-null range in
    data/cheiro_feature_pages.json -- its single call must carry no
    page_ref key at all."""
    monkeypatch.setattr(palm_reading, "_FEATURE_PAGE_FILTER_ENABLED", True)
    assert palm_reading._FEATURE_PAGE_RANGES.get("markings/other features") is None
    chunk = _chunk(text="A cross clearly visible near the base of the palm.")
    fake_search = _FakeSearch([chunk])
    monkeypatch.setattr(palm_reading, "search", fake_search)
    voice_text = (
        "A cross near the base suggests an unusual turning point.[FLOW] "
        "A cross clearly visible near the base of the palm.[C1]"
    )
    client = _single_feature_client("markings/other features", chunk, voice_text)

    generate_palm_reading(
        palm_left="MARKS: A cross clearly visible near the base of the palm.",
        palm_right=None,
        client=client,
    )

    assert len(fake_search.calls) == 1
    assert "page_ref" not in fake_search.calls[0]


def test_page_range_gate_candidate_pool_constant_removed():
    """(S82d) Regression guard: the widened-pool constant is fully
    removed, not merely unused."""
    assert not hasattr(palm_reading, "_PAGE_FILTER_CANDIDATE_N")


def test_page_range_gate_off_by_default_omits_page_ref_key(monkeypatch):
    """(S82e) Flag OFF (explicit, since S82f flips the module default to
    True) -> the OFF path is unchanged: no page_ref key on the recorded
    call even for a feature with a verified range."""
    monkeypatch.setattr(palm_reading, "_FEATURE_PAGE_FILTER_ENABLED", False)
    chunk = _chunk()
    fake_search = _FakeSearch([chunk])
    monkeypatch.setattr(palm_reading, "search", fake_search)
    client = _single_feature_client("life line", chunk, _CLEAN_STUB_TEXT)

    generate_palm_reading(palm_left="LIFE LINE: A long life line.", palm_right=None, client=client)

    assert len(fake_search.calls) == 1
    assert "page_ref" not in fake_search.calls[0]


# ─── Item 11: sources propagation ───────────────────────────────────────


def test_sources_propagate_book_page_score(monkeypatch):
    chunk1 = _chunk(text="Chunk one text about the life line.", page_ref=12, score=0.81, chunk_id="c1")
    chunk2 = _chunk(text="Chunk two text about the life line.", page_ref=57, score=0.66, chunk_id="c2")
    monkeypatch.setattr(palm_reading, "search", _FakeSearch([chunk1, chunk2]))
    voice_text = (
        "This hand shows steady character throughout.[FLOW] "
        "Chunk one text about the life line.[C1] "
        "Chunk two text about the life line.[C2]"
    )
    client, _ = _two_stage_setup({"life line": [chunk1, chunk2]}, lambda ids: voice_text)

    result = generate_palm_reading(palm_left="LIFE LINE: A long life line.", palm_right=None, client=client)

    assert result.sources == (
        {"book": "cheiroslanguageo00chei_1", "page": 12, "score": 0.81, "feature": "life line"},
        {"book": "cheiroslanguageo00chei_1", "page": 57, "score": 0.66, "feature": "life line"},
    )


# ─── Item 12: self-help register validator (S66 F2b) ───────────────────
# Display checks no longer retry (S69 F-H P5's "NO retry at this layer"
# rule) -- each of these is now a single-shot failure/pass, not a
# retry-then-clean scenario.

_STABILITY_STUB_TEXT = (
    "This hand promises STABILITY through disciplined effort, with a "
    "firm grip on practical matters and a steady, deliberate approach "
    "to every undertaking that comes before it.[FLOW] "
    "A long, unbroken life line indicates steady vitality.[C1]"
)


def test_self_help_case_insensitive(monkeypatch):
    """S70 F-G2: see test_jargon_injection_case_insensitive_and_word_
    boundary's own note -- this fixture's single Stage-2 response is
    reused on Stage 2's now-firing retry, so the same failure string
    appears twice, not once."""
    chunk = _chunk()
    monkeypatch.setattr(palm_reading, "search", _FakeSearch([chunk]))
    client = _single_feature_client("life line", chunk, _STABILITY_STUB_TEXT)

    result = generate_palm_reading(
        palm_left="LIFE LINE: A long life line with a gentle curve.", palm_right=None, client=client
    )

    assert result.validation.passed is False
    assert result.stage2_retry_used is True
    assert set(result.validation.failures) == {"self_help_blacklist: found stability"}


_WORD_BOUNDARY_STUB_TEXT = (
    "A hand marked by inner instability at times still moves toward calm "
    "judgment, and this journeyman spirit for craft rewards patient hands "
    "with quiet mastery over many years.[FLOW] "
    "A long, unbroken life line indicates steady vitality.[C1]"
)


def test_self_help_word_boundary_excludes_substrings(monkeypatch):
    chunk = _chunk()
    monkeypatch.setattr(palm_reading, "search", _FakeSearch([chunk]))
    client = _single_feature_client("life line", chunk, _WORD_BOUNDARY_STUB_TEXT)

    result = generate_palm_reading(
        palm_left="LIFE LINE: A long life line with a gentle curve.", palm_right=None, client=client
    )

    assert not any("self_help_blacklist" in f for f in result.validation.failures)
    assert result.validation.passed is True


_NAVIGATED_STUB_TEXT = (
    "Once navigated with hesitation in youth, this quality now runs firm "
    "and true, showing settled judgment and clear resolve.[FLOW] "
    "A long, unbroken life line indicates steady vitality.[C1]"
)


def test_self_help_unlisted_conjugation_does_not_trip(monkeypatch):
    chunk = _chunk()
    monkeypatch.setattr(palm_reading, "search", _FakeSearch([chunk]))
    client = _single_feature_client("life line", chunk, _NAVIGATED_STUB_TEXT)

    result = generate_palm_reading(
        palm_left="LIFE LINE: A long life line with a gentle curve.", palm_right=None, client=client
    )

    assert not any("self_help_blacklist" in f for f in result.validation.failures)
    assert result.validation.passed is True


_MULTI_TERM_STUB_TEXT = (
    "This quality points to fulfilling achievements forged through "
    "effort, while its steady course traces a long journey of "
    "independent judgment; a second look confirms the journey continues "
    "on firm ground for fulfilling work ahead.[FLOW] "
    "A long, unbroken life line indicates steady vitality.[C1]"
)


def test_self_help_multi_term_single_sorted_deduped_failure(monkeypatch):
    """Two distinct terms, each appearing twice, collapse to one failure
    string per attempt, listing both terms once, sorted. S70 F-G2: this
    fixture's single Stage-2 response is reused on Stage 2's now-firing
    retry, so the same failure string appears twice, not once (see
    test_jargon_injection_case_insensitive_and_word_boundary's own
    note)."""
    chunk = _chunk()
    monkeypatch.setattr(palm_reading, "search", _FakeSearch([chunk]))
    client = _single_feature_client("life line", chunk, _MULTI_TERM_STUB_TEXT)

    result = generate_palm_reading(
        palm_left="LIFE LINE: A long life line with a gentle curve.", palm_right=None, client=client
    )

    assert result.validation.passed is False
    assert result.stage2_retry_used is True
    assert set(result.validation.failures) == {"self_help_blacklist: found fulfilling, journey"}


_CHEIRO_VOICE_STUB_TEXT = (
    "This quality runs long and unbroken, promising sound constitution "
    "and vigor that will carry through many years. Its depth and "
    "continuity reveal a nature built for endurance, sharpened by direct "
    "experience rather than idle theory. Such a quality, clear and "
    "undivided, promises success won through personal exertion rather "
    "than chance.[FLOW] "
    "A long, unbroken life line indicates steady vitality.[C1]"
)


def test_self_help_clean_cheiro_register_passes(monkeypatch):
    chunk = _chunk()
    monkeypatch.setattr(palm_reading, "search", _FakeSearch([chunk]))
    client = _single_feature_client("life line", chunk, _CHEIRO_VOICE_STUB_TEXT)

    result = generate_palm_reading(
        palm_left="LIFE LINE: A long life line with a gentle curve.", palm_right=None, client=client
    )

    assert result.validation.passed is True
    assert result.validation.failures == ()


_EMPOWERMENT_STUB_TEXT = (
    "This hand speaks of quiet empowerment gained through steady effort, "
    "with practical instincts and calm resolve carrying you through each "
    "new challenge that comes your way.[FLOW] "
    "A long, unbroken life line indicates steady vitality.[C1]"
)


def test_self_help_integration_empowerment_fails_and_propagates(monkeypatch):
    """Full generate_palm_reading() integration: a Stage-2 draft
    containing a blacklisted term must produce a failed, propagated
    ValidationReport inside the returned PalmReadingResult."""
    chunk = _chunk()
    monkeypatch.setattr(palm_reading, "search", _FakeSearch([chunk]))
    client = _single_feature_client("life line", chunk, _EMPOWERMENT_STUB_TEXT)

    result = generate_palm_reading(
        palm_left="LIFE LINE: A long life line with a gentle curve.",
        palm_right="HEART LINE: A curved heart line.",
        client=client,
    )

    assert isinstance(result, PalmReadingResult)
    assert isinstance(result.validation, ValidationReport)
    assert result.validation.passed is False
    assert any(
        f == "self_help_blacklist: found empowerment" for f in result.validation.failures
    )


# ─── Item 13: S67 R1 per-feature retrieval ──────────────────────────────
# (13a, the hardest case -- all features absent -- lives in Item 6 above,
# alongside the other empty-retrieval/zero-call tests it shares a root
# cause with.)

_DEGENERATE_QUALITY_LEFT = "LIFE LINE: Present."


def test_fail_open_degenerate_quality_still_queries_and_logs(monkeypatch, caplog):
    """(13b) LIFE LINE's text is just "Present." -- not absence-phrased,
    but quality extraction degenerates to the bare word "present". FAIL
    OPEN: the feature is still queried, using its own raw field text as
    the quality, and a warning is logged."""
    chunk = _chunk()
    fake_search = _FakeSearch([chunk])
    monkeypatch.setattr(palm_reading, "search", fake_search)
    client = _single_feature_client("life line", chunk, _CLEAN_STUB_TEXT)

    with caplog.at_level("WARNING"):
        generate_palm_reading(palm_left=_DEGENERATE_QUALITY_LEFT, palm_right=None, client=client)

    assert len(fake_search.calls) == 1
    assert "present" in fake_search.calls[0]["question"].lower()
    assert "fail-open" in caplog.text.lower()


def test_one_feature_search_failure_does_not_kill_reading_other_feature_succeeds(monkeypatch, caplog):
    """(13c) 2 observed features (life line, heart line); the life-line
    query raises, the heart-line query succeeds -> the reading still
    proceeds (no exception propagates), the failure is logged, and
    sources reflect only the surviving feature's chunk."""
    heart_chunk = _chunk(text="A well-formed heart line suggests warmth.", page_ref=57, score=0.7, chunk_id="heart1")

    def _raise_for(question: str) -> bool:
        return "life line" in question

    fake_search = _FakeSearch([heart_chunk], raise_for=_raise_for)
    monkeypatch.setattr(palm_reading, "search", fake_search)
    voice_text = "A well-formed heart line suggests warmth.[C1]"
    client, _ = _two_stage_setup({"heart line": [heart_chunk]}, lambda ids: voice_text)

    with caplog.at_level("WARNING"):
        result = generate_palm_reading(
            palm_left="LIFE LINE: A long life line.",
            palm_right="HEART LINE: A curved heart line.",
            client=client,
        )

    assert len(fake_search.calls) == 2
    assert result.sources == (
        {"book": "cheiroslanguageo00chei_1", "page": 57, "score": 0.7, "feature": "heart line"},
    )
    assert "life line" in caplog.text.lower()


def test_query_template_two_hand_merged_quality_literal_shape(monkeypatch):
    """(13d) Two-hand differing fate-line qualities (barely visible vs.
    moderately deep) merge into exactly the ratified variant-iii template
    shape. Unaffected by the two-stage wiring -- retrieval-only assertion,
    and the default `_chunk()` text never mentions "fate", so nothing
    survives the support gate for fate line here; Stage 1/Stage 2 have
    nothing to attempt, and the (unused) client would raise if ever
    called."""
    fake_search = _FakeSearch([_chunk()])
    monkeypatch.setattr(palm_reading, "search", fake_search)
    client = _explosive_client()

    generate_palm_reading(
        palm_left="FATE LINE: Barely visible.",
        palm_right=(
            "FATE LINE: Present, moderately deep, runs from the base of "
            "the palm towards the middle finger, no clear breaks or forks."
        ),
        client=client,
    )

    # 1 observed feature (fate line -- both hands merge into one query)
    # -> 1 search call.
    assert len(fake_search.calls) == 1
    assert fake_search.calls[0]["question"] == (
        "what does a barely visible / moderately deep fate line signify "
        "— meaning and indications of a barely visible / moderately deep fate line"
    )
    assert fake_search.calls[0]["n_results"] == 3  # production default, dogfood flag off
    assert client.completions.calls == []


@pytest.mark.skip(
    reason="F-H: _assemble_retrieved_passages (the old single-prompt "
    "'### {feature}' assembler) is retired at P5 -- no longer called by "
    "the two-stage pipeline (Stage 1/Stage 2 build their own per-call "
    "prompts). This test asserted on the OLD assembled prompt's dedupe/ "
    "display-order behavior via client.completions.calls[0]'s message "
    "content, which no longer reflects that assembly at all. Deletion "
    "decision at close-out; the function itself is untouched and could "
    "be tested directly (same convention as the V-1/V-2/coverage direct "
    "unit tests below) if its logic is still wanted."
)
def test_per_feature_map_ordering_and_dedupe_for_display(monkeypatch):
    """(13e) Life line (registry position 1) and head line (position 2)
    both retrieve the SAME chunk_id (corpus overlap) -- the assembled
    user-message prompt shows it once, under life line's heading only."""
    shared_text = "Shared passage about the life line and the head line."
    dupe_chunk = _chunk(text=shared_text, page_ref=99, score=0.5, chunk_id="dupe1")
    fake_search = _FakeSearch([dupe_chunk])
    monkeypatch.setattr(palm_reading, "search", fake_search)
    client = _FakeClient(content=_CLEAN_STUB_TEXT)

    result = generate_palm_reading(
        palm_left="LIFE LINE: A long life line.\nHEAD LINE: A slightly curved head line.",
        palm_right=None,
        client=client,
    )

    assert len(fake_search.calls) == 2
    user_message = client.completions.calls[0]["messages"][1]["content"]
    assert user_message.count(shared_text) == 1
    assert "### life line" in user_message
    assert "### head line" not in user_message

    assert result.sources == (
        {"book": "cheiroslanguageo00chei_1", "page": 99, "score": 0.5, "feature": "life line"},
        {"book": "cheiroslanguageo00chei_1", "page": 99, "score": 0.5, "feature": "head line"},
    )


def test_sources_carry_distinct_feature_tags(monkeypatch):
    """(13f) Two observed features, each returning its OWN distinct
    chunk -- sources must tag each with the feature that actually
    produced it, not a shared/default value."""
    life_chunk = _chunk(text="Life line passage about vitality.", page_ref=134, score=0.6, chunk_id="life1")
    heart_chunk = _chunk(text="Heart line passage about warmth.", page_ref=88, score=0.55, chunk_id="heart1")

    class _SequencedSearch:
        def __init__(self):
            self.calls: list[dict] = []

        def __call__(self, question, n_results=None, **filters):
            self.calls.append({"question": question, "n_results": n_results, **filters})
            if "life line" in question:
                return [life_chunk]
            if "heart line" in question:
                return [heart_chunk]
            return []

    fake_search = _SequencedSearch()
    monkeypatch.setattr(palm_reading, "search", fake_search)
    voice_text = (
        "This hand carries itself calmly.[FLOW] "
        "Life line passage about vitality.[C1] "
        "Heart line passage about warmth.[C2]"
    )
    client, _ = _two_stage_setup(
        {"life line": [life_chunk], "heart line": [heart_chunk]}, lambda ids: voice_text
    )

    result = generate_palm_reading(
        palm_left="LIFE LINE: A long life line.",
        palm_right="HEART LINE: A curved heart line.",
        client=client,
    )

    assert len(fake_search.calls) == 2
    assert result.sources == (
        {"book": "cheiroslanguageo00chei_1", "page": 134, "score": 0.6, "feature": "life line"},
        {"book": "cheiroslanguageo00chei_1", "page": 88, "score": 0.55, "feature": "heart line"},
    )


# ─── Item 14: S67 R3 support gate + decline mechanism ──────────────────
# Display checks (including banned-feature-mention) no longer retry --
# each "guard fires" case below is now single-shot, not retry-then-clean.


def test_banned_mention_fires_when_draft_names_unsupported_feature(monkeypatch):
    """(14a) fate line is OBSERVED but its retrieved chunks fail the
    needle check (unsupported); a Stage-2 draft that nonetheless names
    "the fate line" trips the banned-mention display check -- single-shot
    fail (no retry at this layer)."""
    life_chunk = _chunk(text="A long life line promises vitality.", page_ref=134, score=0.6, chunk_id="life1")
    non_doctrine_chunk = _chunk(
        text="Chapter II lists the seven principal lines of the hand.",
        page_ref=120, score=0.62, chunk_id="nd1",
    )

    class _PerFeatureSearch:
        def __init__(self):
            self.calls: list[dict] = []

        def __call__(self, question, n_results=None, **filters):
            self.calls.append({"question": question, "n_results": n_results, **filters})
            if "life line" in question:
                return [life_chunk]
            if "fate line" in question:
                return [non_doctrine_chunk]
            return []

    fake_search = _PerFeatureSearch()
    monkeypatch.setattr(palm_reading, "search", fake_search)
    voice_text = (
        "Your life line shows steady vitality, and the fate line reveals "
        "a path shaped by personal choice.[C1]"
    )
    client, _ = _two_stage_setup({"life line": [life_chunk]}, lambda ids: voice_text)

    result = generate_palm_reading(
        palm_left="LIFE LINE: A long life line.\nFATE LINE: Barely visible.",
        palm_right=None,
        client=client,
    )

    assert len(fake_search.calls) == 2
    assert result.supported_features == ("life line",)
    assert "fate line" in result.unsupported_features
    assert result.validation.passed is False
    assert any("unsupported feature mentioned: fate line" in f for f in result.validation.failures)
    assert "fate line" in result.reading_text.split("A note on")[1]


def test_needle_collision_battery_sunday_sunny_remarkable_marked_do_not_trip(monkeypatch):
    """(14b) sun line and markings/other features are BOTH unsupported
    here (never mentioned at all). A draft containing "sunny", "Sunday",
    "remarkable", and "marked" -- none of them the STANDALONE words
    "sun"/"mark" -- must NOT trip the banned-mention validator."""
    chunk = _chunk()
    monkeypatch.setattr(palm_reading, "search", _FakeSearch([chunk]))
    voice_text = (
        "This reading reflects on a sunny disposition and a remarkable, "
        "marked sense of purpose that carries through every Sunday and "
        "every ordinary day alike.[FLOW] "
        "A long, unbroken life line indicates steady vitality.[C1]"
    )
    client = _single_feature_client("life line", chunk, voice_text)

    result = generate_palm_reading(palm_left="LIFE LINE: A long life line.", palm_right=None, client=client)

    assert result.validation.passed is True
    assert not any("unsupported feature mentioned" in f for f in result.validation.failures)


def test_needle_collision_battery_genuine_sun_line_mention_fires(monkeypatch):
    """(14b, companion) A GENUINE standalone "sun line" mention, with sun
    line unsupported, DOES fire. Placed in the [C1]-tagged sentence (not
    [FLOW]/[OBS]) so it reaches the display text without first tripping
    claim_voicing's own V-5 doctrine guard (which only scans [FLOW]/
    [OBS] segments) -- proving the word-boundary matcher isn't so loose
    it never fires at all."""
    chunk = _chunk()
    monkeypatch.setattr(palm_reading, "search", _FakeSearch([chunk]))
    voice_text = (
        "A long, unbroken life line paired with a faint sun line "
        "suggests hidden creative promise.[C1]"
    )
    client = _single_feature_client("life line", chunk, voice_text)

    result = generate_palm_reading(palm_left="LIFE LINE: A long life line.", palm_right=None, client=client)

    assert result.validation.passed is False
    assert any("unsupported feature mentioned: sun line" in f for f in result.validation.failures)


def test_score_floor_boundary_029_excluded_031_included(monkeypatch):
    """(14c) Needle-passing chunks at the score-floor boundary -- 0.29
    (just under _SUPPORT_SCORE_FLOOR) is gated OUT; 0.31 (just over)
    SURVIVES."""
    below_floor = _chunk(text="A note on the life line's course.", page_ref=1, score=0.29, chunk_id="below")
    above_floor = _chunk(text="A note on the life line's course.", page_ref=2, score=0.31, chunk_id="above")
    monkeypatch.setattr(palm_reading, "search", _FakeSearch([below_floor, above_floor]))
    voice_text = "A note on the life line's course.[C1]"
    client, _ = _two_stage_setup({"life line": [above_floor]}, lambda ids: voice_text)

    result = generate_palm_reading(palm_left="LIFE LINE: A long life line.", palm_right=None, client=client)

    assert result.supported_features == ("life line",)
    assert result.sources == (
        {"book": "cheiroslanguageo00chei_1", "page": 2, "score": 0.31, "feature": "life line"},
    )


def test_decline_block_exact_text_two_feature_list(monkeypatch):
    """(14d) Exact decline-block wording with exactly 2 unsupported
    features (fate line, sun line). Every OTHER registry feature is
    absence-phrased BY NAME (genuine negative absence) so the list is
    exactly these 2. Search returns [] always -> nothing is ever
    attempted at Stage 1/2 -- unaffected by the two-stage wiring, the
    (unused) explosive client proves it."""
    fixture = (
        "HAND SHAPE: Square palm.\n"
        "FINGERS: Not clearly visible.\n"
        "THUMB: Not visible.\n"
        "LIFE LINE: Not clearly visible.\n"
        "HEAD LINE: Not clearly visible.\n"
        "HEART LINE: Not clearly visible.\n"
        "FATE LINE: Barely visible.\n"
        "OTHER LINES: Sun line is faintly visible.\n"
        "MOUNTS: Mount of Venus is unremarkable, Mount of Jupiter is unremarkable, "
        "Mount of Saturn is unremarkable, Mount of the Sun is unremarkable, "
        "Mount of Mercury is unremarkable, Upper Mount of Mars is unremarkable, "
        "Lower Mount of Mars is unremarkable, Mount of the Moon is unremarkable.\n"
        "MARKS: No clear marks visible."
    )
    monkeypatch.setattr(palm_reading, "search", _FakeSearch([]))
    client = _explosive_client()

    result = generate_palm_reading(palm_left=fixture, palm_right=None, client=client)

    assert client.completions.calls == []
    assert result.unsupported_features == ("fate line", "sun line")
    assert result.supported_features == ()
    assert (
        "A note on what I have not interpreted: the classical texts I "
        "work from do not clearly address the following as they appear "
        "in your hands: fate line, sun line. Rather than guess, I have "
        "left these out of your reading."
    ) in result.reading_text


def test_decline_block_absent_when_all_observed_features_supported(monkeypatch):
    """(14d, companion) When every registry feature is either supported
    or a genuine negative-absence finding, the decline block is omitted
    ENTIRELY -- not an empty note, no note at all."""
    fixture = (
        "HAND SHAPE: Square palm.\n"
        "FINGERS: Not clearly visible.\n"
        "THUMB: Not visible.\n"
        "LIFE LINE: A long life line.\n"
        "HEAD LINE: Not clearly visible.\n"
        "HEART LINE: Not clearly visible.\n"
        "FATE LINE: Not clearly visible.\n"
        "OTHER LINES: Sun line not clearly visible.\n"
        "MOUNTS: Mount of Venus is unremarkable, Mount of Jupiter is unremarkable, "
        "Mount of Saturn is unremarkable, Mount of the Sun is unremarkable, "
        "Mount of Mercury is unremarkable, Upper Mount of Mars is unremarkable, "
        "Lower Mount of Mars is unremarkable, Mount of the Moon is unremarkable.\n"
        "MARKS: No clear marks visible."
    )
    chunk = _chunk()
    monkeypatch.setattr(palm_reading, "search", _FakeSearch([chunk]))
    client = _single_feature_client("life line", chunk, _CLEAN_STUB_TEXT)

    result = generate_palm_reading(palm_left=fixture, palm_right=None, client=client)

    assert result.unsupported_features == ()
    assert result.supported_features == ("life line",)
    assert "A note on what I have not interpreted" not in result.reading_text


def test_supported_unsupported_tuples_propagate_in_registry_order(monkeypatch):
    """(14f) 3 observed features given in NON-registry input order (fate,
    heart, life) -- life line and heart line supported, fate line
    unsupported. Output tuples must reflect _FEATURE_REGISTRY order, not
    input order."""
    life_chunk = _chunk(text="A long life line passage.", score=0.6, chunk_id="l1")
    heart_chunk = _chunk(text="A curved heart line passage.", score=0.6, chunk_id="h1")
    fate_chunk = _chunk(text="Unrelated nomenclature passage.", score=0.6, chunk_id="f1")

    class _Search:
        def __init__(self):
            self.calls: list[dict] = []

        def __call__(self, question, n_results=None, **filters):
            self.calls.append({"question": question, "n_results": n_results, **filters})
            if "life line" in question:
                return [life_chunk]
            if "heart line" in question:
                return [heart_chunk]
            if "fate line" in question:
                return [fate_chunk]
            return []

    fake_search = _Search()
    monkeypatch.setattr(palm_reading, "search", fake_search)
    voice_text = (
        "This hand shows steady character.[FLOW] "
        "A long life line passage.[C1] "
        "A curved heart line passage.[C2]"
    )
    client, _ = _two_stage_setup(
        {"life line": [life_chunk], "heart line": [heart_chunk]}, lambda ids: voice_text
    )

    result = generate_palm_reading(
        palm_left=(
            "FATE LINE: Present, moderately deep, runs from the base of "
            "the palm towards the middle finger.\n"
            "HEART LINE: A curved heart line.\n"
            "LIFE LINE: A long life line."
        ),
        palm_right=None,
        client=client,
    )

    assert len(fake_search.calls) == 3
    assert result.supported_features == ("life line", "heart line")
    expected_unsupported = tuple(
        f for f in palm_reading._FEATURE_REGISTRY
        if f not in ("life line", "heart line")
    )
    assert result.unsupported_features == expected_unsupported


def test_banned_mention_failure_now_retries_and_stays_failed(monkeypatch):
    """(14g) S70 F-G2 UPDATE (was test_banned_mention_failure_is_single_
    shot_no_retry, pre-F-G2): display-check failures (banned-mention
    here) now feed Stage 2's own retry via the extra_validators seam --
    formerly single-shot with no retry at this layer. A draft naming an
    unsupported feature still ends up failed (this fixture's single
    Stage-2 response is reused on retry, so the same unsupported-feature
    mention persists into the retry draft too), but the call count is now
    Stage-1 once + Stage-2 TWICE (first + retry), not once."""
    chunk = _chunk()
    monkeypatch.setattr(palm_reading, "search", _FakeSearch([chunk]))
    voice_text = "A faint sun line suggests hidden creative promise.[C1]"
    client, _ = _two_stage_setup({"life line": [chunk]}, lambda ids: voice_text)

    result = generate_palm_reading(
        palm_left="LIFE LINE: A long life line.", palm_right=None, client=client
    )

    assert len(client.completions.calls) == 3  # Stage 1 once, Stage 2 first + retry
    assert result.stage2_retry_used is True
    assert result.validation.passed is False
    assert any("unsupported feature mentioned: sun line" in f for f in result.validation.failures)


# ─── Item 15: S67 R2 exemplar-echo guard ────────────────────────────────
# S70 F-G2 UPDATE: display checks now DO retry, via the F-G1
# extra_validators seam wired into complete_palm_reading() -- this is the
# exact fix for the pass-5 preflight ABORT
# (diagnostics/pass5_preflight_S70.md) where Stage 2 echoed an exemplar
# sentence verbatim and the outer, retry-less display-check layer was the
# only thing that ever saw it.


def test_exemplar_echo_guard_fires_draft1_retries_and_clears_on_clean_draft2(monkeypatch):
    """(a) S70 F-G2: draft 1 verbatim-echoes exemplar 1 ("each one tells
    its own story") -- the seam's exemplar_echo closure catches this on
    Stage 2's FIRST draft and feeds it into Stage 2's own retry; draft 2
    is clean -> stage2_retry_used=True, final validation.passed=True."""
    chunk = _chunk()
    monkeypatch.setattr(palm_reading, "search", _FakeSearch([chunk]))
    stage1 = json.dumps({"feature": "life line", "claims": [
        {"claim_id": "x", "chunk_id": chunk["chunk_id"], "claim_text": chunk["text"],
         "valence": "supports", "condition_text": None, "observation_basis": "observed"},
    ]})
    echo_draft = (
        "Each one tells its own story to those who understand the "
        "craft.[FLOW] "
        "A long, unbroken life line indicates steady vitality.[C1]"
    )
    clean_draft = "A long, unbroken life line indicates steady vitality.[C1]"
    client = _FakeClient(responses=[(stage1, None), (echo_draft, None), (clean_draft, None)])

    result = generate_palm_reading(palm_left="LIFE LINE: A long life line.", palm_right=None, client=client)

    assert len(client.completions.calls) == 3  # Stage 1 once, Stage 2 first + retry
    assert result.stage2_retry_used is True
    assert result.validation.passed is True
    retry_correction = client.completions.calls[2]["messages"][-1]["content"]
    assert "Your draft failed these checks" in retry_correction
    assert "exemplar_echo: each one tells its own story" in retry_correction


def test_exemplar_echo_guard_fires_both_drafts_stays_failed_no_third_call(monkeypatch):
    """(b) S70 F-G2: both drafts echo the SAME exemplar span -> exactly
    Stage-1-once + Stage-2-TWICE = 3 calls total (no third Stage-2 call),
    validation.passed=False, the exemplar failure present in
    validation.failures."""
    chunk = _chunk()
    monkeypatch.setattr(palm_reading, "search", _FakeSearch([chunk]))
    stage1 = json.dumps({"feature": "life line", "claims": [
        {"claim_id": "x", "chunk_id": chunk["chunk_id"], "claim_text": chunk["text"],
         "valence": "supports", "condition_text": None, "observation_basis": "observed"},
    ]})
    echo_draft = (
        "Each one tells its own story to those who understand the "
        "craft.[FLOW] "
        "A long, unbroken life line indicates steady vitality.[C1]"
    )
    client = _FakeClient(responses=[(stage1, None), (echo_draft, None), (echo_draft, None)])

    result = generate_palm_reading(palm_left="LIFE LINE: A long life line.", palm_right=None, client=client)

    assert len(client.completions.calls) == 3  # Stage 1 once, Stage 2 first + retry, no 3rd Stage-2 call
    assert result.stage2_retry_used is True
    assert result.validation.passed is False
    assert any(f == "exemplar_echo: each one tells its own story" for f in result.validation.failures)


def test_exemplar_echo_guard_clean_draft_happy_path_no_behavior_change(monkeypatch):
    """(c) S70 F-G2: a clean draft (no echo, no other display-check
    issue) must be completely unaffected by the new seam -- no retry, no
    behavior change from the pre-F-G2 happy path."""
    chunk = _chunk()
    monkeypatch.setattr(palm_reading, "search", _FakeSearch([chunk]))
    client = _single_feature_client("life line", chunk, _CLEAN_STUB_TEXT)

    result = generate_palm_reading(palm_left="LIFE LINE: A long life line.", palm_right=None, client=client)

    assert len(client.completions.calls) == 2  # Stage 1 once, Stage 2 once -- no retry
    assert result.stage2_retry_used is False
    assert result.validation.passed is True
    assert result.validation.failures == ()


# ─── S70: stage2_first_attempt_failures -- retry attribution ───────────
#
# stage2_retry_used alone answers "did Stage 2 retry"; this field answers
# "what did the FIRST draft fail on", even when the retry fully clears it
# and the final result passes cleanly -- the exact gap pass-5 preflight's
# own addenda flagged (diagnostics/pass5_preflight_S70.md).


def test_stage2_first_attempt_failures_carries_first_draft_failure_verbatim(monkeypatch):
    """(a) Reuses test_exemplar_echo_guard_fires_draft1_retries_and_
    clears_on_clean_draft2's exact fixture shape: draft 1 echoes, draft 2
    is clean -> the final result still passes, but
    stage2_first_attempt_failures records what draft 1 actually failed
    on, verbatim."""
    chunk = _chunk()
    monkeypatch.setattr(palm_reading, "search", _FakeSearch([chunk]))
    stage1 = json.dumps({"feature": "life line", "claims": [
        {"claim_id": "x", "chunk_id": chunk["chunk_id"], "claim_text": chunk["text"],
         "valence": "supports", "condition_text": None, "observation_basis": "observed"},
    ]})
    echo_draft = (
        "Each one tells its own story to those who understand the "
        "craft.[FLOW] "
        "A long, unbroken life line indicates steady vitality.[C1]"
    )
    clean_draft = "A long, unbroken life line indicates steady vitality.[C1]"
    client = _FakeClient(responses=[(stage1, None), (echo_draft, None), (clean_draft, None)])

    result = generate_palm_reading(palm_left="LIFE LINE: A long life line.", palm_right=None, client=client)

    assert result.stage2_retry_used is True
    assert result.validation.passed is True
    assert result.stage2_first_attempt_failures == ("exemplar_echo: each one tells its own story",)


def test_stage2_first_attempt_failures_empty_when_no_retry(monkeypatch):
    """(b) A clean first draft (no retry fires) -> stage2_first_attempt_
    failures is the empty-tuple default, same as stage2_retry_used=False."""
    chunk = _chunk()
    monkeypatch.setattr(palm_reading, "search", _FakeSearch([chunk]))
    client = _single_feature_client("life line", chunk, _CLEAN_STUB_TEXT)

    result = generate_palm_reading(palm_left="LIFE LINE: A long life line.", palm_right=None, client=client)

    assert result.stage2_retry_used is False
    assert result.stage2_first_attempt_failures == ()


def test_exemplar_echo_boundary_5word_no_fire_6word_fires(monkeypatch):
    """Measure-first boundary pair: a 5-word overlap with the exemplar
    does NOT fire; extended by one word to complete the genuine 6-gram
    DOES fire."""
    chunk = _chunk()
    monkeypatch.setattr(palm_reading, "search", _FakeSearch([chunk]))

    five_word_voice = (
        "Each one tells its own tale in every hand I read.[FLOW] "
        "A long, unbroken life line indicates steady vitality.[C1]"
    )
    client5 = _single_feature_client("life line", chunk, five_word_voice)
    result5 = generate_palm_reading(palm_left="LIFE LINE: A long life line.", palm_right=None, client=client5)
    assert not any("exemplar_echo" in f for f in result5.validation.failures)

    six_word_voice = (
        "Each one tells its own story in every hand I read.[FLOW] "
        "A long, unbroken life line indicates steady vitality.[C1]"
    )
    client6 = _single_feature_client("life line", chunk, six_word_voice)
    result6 = generate_palm_reading(palm_left="LIFE LINE: A long life line.", palm_right=None, client=client6)
    assert any(
        f == "exemplar_echo: each one tells its own story"
        for f in result6.validation.failures
    )


def test_exemplar_echo_normalization_case_punctuation_whitespace(monkeypatch):
    """An overlap differing only in case, punctuation, and
    whitespace-run-length still fires -- proves normalized-token
    matching, not exact-string matching."""
    chunk = _chunk()
    monkeypatch.setattr(palm_reading, "search", _FakeSearch([chunk]))
    weird_voice = (
        "EACH,   one   tells; ITS   own   STORY!!! in every hand.[FLOW] "
        "A long, unbroken life line indicates steady vitality.[C1]"
    )
    client = _single_feature_client("life line", chunk, weird_voice)

    result = generate_palm_reading(palm_left="LIFE LINE: A long life line.", palm_right=None, client=client)

    assert any(
        f == "exemplar_echo: each one tells its own story"
        for f in result.validation.failures
    )


def test_exemplar_echo_does_not_fire_on_retrieved_chunk_quote(monkeypatch):
    """Doctrine-quoting immunity: a draft sharing a 6-word span with a
    RETRIEVED CHUNK (not an exemplar) must NOT fire -- the guard compares
    against the 2 exemplar sentences ONLY, never retrieved chunks."""
    doctrine_chunk = _chunk(
        text="The line of life should be long narrow and deep without irregularities",
        score=0.6,
    )
    monkeypatch.setattr(palm_reading, "search", _FakeSearch([doctrine_chunk]))
    voice_text = (
        "The line of life should be long narrow and deep without "
        "irregularities, promising a strong constitution.[C1]"
    )
    client = _single_feature_client("life line", doctrine_chunk, voice_text)

    result = generate_palm_reading(palm_left="LIFE LINE: A long life line.", palm_right=None, client=client)

    assert not any("exemplar_echo" in f for f in result.validation.failures)
    assert result.validation.passed is True


# ─── Item 16: A1 V-1/V-2 chunk-anchor Ring 1 validators (S68 F-C) ───────
#
# palm_reading._check_tag_completeness (V-1) and palm_reading._check_
# anchor_legality (V-2) are RETIRED from generate_palm_reading's own call
# path (S69 F-H P5 -- natively replaced by claim_extraction's E-1 and
# claim_voicing's V-3) but remain DEFINED. Direct unit tests of the
# functions themselves (not through generate_palm_reading) stay passing
# unmodified -- untouched below. The ONE test that exercised them through
# the full generate_palm_reading() integration is marked skip.


def test_tag_completeness_empty_string_reports_anchor_contract_not_exercised():
    """Guards against PalmReadingResult.reading_text_tagged's dataclass
    default of "" ever being fed back through Ring 1."""
    failures = palm_reading._check_tag_completeness("")

    assert failures == [
        "anchor_completeness: anchor contract not exercised "
        "(reading_text_tagged is empty or whitespace-only)"
    ]


def test_tag_completeness_whitespace_only_reports_anchor_contract_not_exercised():
    failures = palm_reading._check_tag_completeness("   \n\t  ")

    assert failures == [
        "anchor_completeness: anchor contract not exercised "
        "(reading_text_tagged is empty or whitespace-only)"
    ]


def test_tag_completeness_wholly_untagged_prose_reports_residue():
    """No recognized tag anywhere in the text -- the whole stripped text
    is reported as the untagged residue."""
    text = "Your life line shows steady vitality."

    failures = palm_reading._check_tag_completeness(text)

    assert failures == [
        "anchor_completeness: sentence-final residue with no tag: "
        "'Your life line shows steady vitality.'"
    ]


def test_tag_completeness_trailing_residue_after_last_tag_quoted_in_message():
    """A valid tag exists, but untagged text follows it -- the residue
    AFTER the last recognized tag is quoted verbatim (repr) in the
    failure message."""
    text = "First sentence.[OBS] Second sentence needs a tag but has none"

    failures = palm_reading._check_tag_completeness(text)

    assert failures == [
        "anchor_completeness: sentence-final residue with no tag: "
        "'Second sentence needs a tag but has none'"
    ]


def test_tag_completeness_clean_pass_mixed_obs_and_anchor_tags():
    """One [OBS] observation sentence followed by one sentence citing a
    chunk_id -- both terminate in a recognized tag, nothing trails the
    last one -> clean pass."""
    text = (
        "Your life line runs long and clear.[OBS] "
        "Classical doctrine holds this promises vitality."
        "[cheiroslanguageo00chei_1_p134_c2]"
    )

    assert palm_reading._check_tag_completeness(text) == []


def test_tag_completeness_multi_anchor_sentence_pass():
    """A single sentence citing two adjacent chunk_id anchors back to
    back -- still a clean pass since nothing trails the last tag."""
    text = (
        "This claim draws on two passages at once."
        "[cheiroslanguageo00chei_1_p134_c1][cheiroslanguageo00chei_1_p163_c3]"
    )

    assert palm_reading._check_tag_completeness(text) == []


def test_anchor_legality_fabricated_chunk_id_hard_fail_listed_verbatim():
    """A chunk_id that was never retrieved for any feature, any run --
    the failure message must list it verbatim, not a generic message."""
    text = "A claim citing a chunk that was never retrieved.[cheiroslanguageo00chei_1_p999_c9]"
    valid_chunk_ids = frozenset({"cheiroslanguageo00chei_1_p134_c2"})

    failures = palm_reading._check_anchor_legality(text, valid_chunk_ids)

    assert failures == [
        "anchor_legality: unknown/malformed chunk_id(s): "
        "cheiroslanguageo00chei_1_p999_c9"
    ]


def test_anchor_legality_stale_id_valid_shape_not_in_gated_set_fails():
    """A chunk_id that is a genuine, valid-shaped corpus id (it could have
    been gated in a PRIOR run) but is not a member of THIS run's valid_
    chunk_ids -- membership, not shape, is the only thing V-2 checks."""
    text = "A claim citing a stale, previously-valid chunk.[cheiroslanguageo00chei_1_p134_c2]"
    valid_chunk_ids = frozenset({"cheiroslanguageo00chei_1_p163_c1"})

    failures = palm_reading._check_anchor_legality(text, valid_chunk_ids)

    assert failures == [
        "anchor_legality: unknown/malformed chunk_id(s): "
        "cheiroslanguageo00chei_1_p134_c2"
    ]


def test_anchor_legality_cited_id_present_in_gated_set_passes():
    text = "A claim citing a genuinely gated chunk.[cheiroslanguageo00chei_1_p134_c2]"
    valid_chunk_ids = frozenset({"cheiroslanguageo00chei_1_p134_c2"})

    assert palm_reading._check_anchor_legality(text, valid_chunk_ids) == []


def test_anchor_legality_obs_only_text_passes_nothing_cited():
    """[OBS] is explicitly excluded from the cited set -- an all-[OBS]
    text cites nothing, so it passes regardless of valid_chunk_ids."""
    text = "First observation.[OBS] Second observation.[OBS]"

    assert palm_reading._check_anchor_legality(text, frozenset()) == []


def test_anchor_legality_empty_valid_chunk_ids_any_citation_fails():
    """The degenerate case where gated_results produced no surviving
    chunks at all (valid_chunk_ids is the empty set) -- any citation at
    all is necessarily unknown."""
    text = "A claim citing a chunk despite nothing being gated.[cheiroslanguageo00chei_1_p134_c2]"

    failures = palm_reading._check_anchor_legality(text, frozenset())

    assert failures == [
        "anchor_legality: unknown/malformed chunk_id(s): "
        "cheiroslanguageo00chei_1_p134_c2"
    ]


def test_v1_before_v2_untagged_text_reports_completeness_without_legality_failure():
    """Ordering proof: text with no tags at all trips V-1 (completeness)
    but cites nothing, so V-2 (legality) contributes no failure of its
    own."""
    text = "This is a wholly untagged sentence with no citation at all."

    completeness_failures = palm_reading._check_tag_completeness(text)
    legality_failures = palm_reading._check_anchor_legality(text, frozenset())

    assert any("anchor_completeness" in f for f in completeness_failures)
    assert legality_failures == []

    assert palm_reading._run_ring1_checks(text, "", (), frozenset()) == [
        "anchor_completeness: sentence-final residue with no tag: "
        "'This is a wholly untagged sentence with no citation at all.'"
    ]


@pytest.mark.skip(reason="F-H: retired at P5, deletion decision at close-out")
def test_end_to_end_tagged_draft_with_cited_chunk_validates_clean_and_strips_tags(monkeypatch):
    """A1 end-to-end: a fully-tagged draft (one [OBS] sentence, one
    sentence citing a chunk_id that IS in this run's gated_results) must
    validate clean through the real generate_palm_reading() path, and the
    DISPLAYED reading_text must carry NO tag tokens at all. RETIRED (S69
    F-H P5): generate_palm_reading no longer produces this tag vocabulary
    (V-1/V-2 are no longer invoked) -- kept for close-out's inventory."""
    cited_chunk = _chunk(
        text="The classical texts describe a long life line as promising vitality.",
        score=0.6,
        chunk_id="cheiroslanguageo00chei_1_p134_c2",
    )
    monkeypatch.setattr(palm_reading, "search", _FakeSearch([cited_chunk]))
    tagged_draft = (
        "Your life line runs long and clear across the palm.[OBS] "
        "Classical doctrine holds that such a line promises vitality and "
        "long life.[cheiroslanguageo00chei_1_p134_c2]"
    )
    client = _FakeClient(content=tagged_draft)

    result = generate_palm_reading(
        palm_left="LIFE LINE: A long, deep life line.", palm_right=None, client=client
    )

    assert result.validation.passed is True
    assert result.validation.failures == ()
    assert result.retry_used is False
    assert result.reading_text_tagged == tagged_draft
    assert palm_reading.CHUNK_ANCHOR_TAG_PATTERN.search(result.reading_text) is None


# ─── Item 17: F-A supported-feature coverage check (S68) ────────────────
#
# palm_reading._check_feature_coverage is RETIRED from generate_palm_
# reading's own call path (S69 F-H P5 -- superseded by claim_voicing's
# V-4) but remains DEFINED. Direct unit tests stay passing unmodified;
# the 2 integration tests that exercised its retry-feed/fail-open wiring
# through generate_palm_reading are marked skip.


def test_coverage_supported_feature_never_cited_produces_verbatim_warning():
    gated_results = {
        "thumb": [
            _chunk(text="A broad, strong thumb.", chunk_id="cheiroslanguageo00chei_1_p200_c1"),
        ],
    }
    tagged_text = "The hand shows a broad thumb.[OBS]"

    warnings = palm_reading._check_feature_coverage(tagged_text, gated_results, ("thumb",))

    assert warnings == ["coverage: thumb supported but never cited"]


def test_coverage_obs_only_mention_of_supported_feature_still_a_miss():
    """Landmark-exclusion enforced BY CONSTRUCTION: [OBS] tags contribute
    nothing to the cited set, so a sentence that NAMES the feature in
    prose but tags itself [OBS] still counts as a miss."""
    gated_results = {
        "thumb": [
            _chunk(text="A broad, strong thumb.", chunk_id="cheiroslanguageo00chei_1_p200_c1"),
        ],
    }
    tagged_text = "The thumb appears broad and strong.[OBS]"

    warnings = palm_reading._check_feature_coverage(tagged_text, gated_results, ("thumb",))

    assert warnings == ["coverage: thumb supported but never cited"]


def test_coverage_cited_chunk_id_marks_feature_addressed_no_warning():
    gated_results = {
        "thumb": [
            _chunk(text="A broad, strong thumb.", chunk_id="cheiroslanguageo00chei_1_p200_c1"),
        ],
    }
    tagged_text = "The thumb is broad and strong.[cheiroslanguageo00chei_1_p200_c1]"

    warnings = palm_reading._check_feature_coverage(tagged_text, gated_results, ("thumb",))

    assert warnings == []


def test_coverage_shared_chunk_id_cited_once_marks_both_features_addressed():
    """ACCEPTED GAP (V1, CLAUDE.md accepted-gap register item (f)): a
    chunk_id gated under TWO features marks BOTH addressed when cited
    once, regardless of which feature the citing sentence is actually
    about."""
    shared_chunk = _chunk(
        text="A broad thumb and long fingers both suggest a practical nature.",
        chunk_id="cheiroslanguageo00chei_1_p210_c3",
    )
    gated_results = {
        "thumb": [shared_chunk],
        "fingers": [shared_chunk],
    }
    tagged_text = "The thumb is broad and strong.[cheiroslanguageo00chei_1_p210_c3]"

    warnings = palm_reading._check_feature_coverage(
        tagged_text, gated_results, ("thumb", "fingers")
    )

    assert warnings == []


_COVERAGE_RETRY_CHUNK = _chunk(
    text="A deep, unbroken life line promises steady vitality.",
    chunk_id="cheiroslanguageo00chei_1_p50_c1",
)
_COVERAGE_CLEAN_RETRY_DRAFT = (
    "Your life line runs long and clear, promising steady vitality and "
    "quiet resolve.[cheiroslanguageo00chei_1_p50_c1]"
)


@pytest.mark.skip(reason="F-H: retired at P5, deletion decision at close-out")
def test_coverage_only_retry_fires_and_clean_retry_clears_warnings(monkeypatch):
    """RETIRED (S69 F-H P5): _check_feature_coverage's retry-feed wiring
    through generate_palm_reading's OLD F2c retry no longer exists --
    coverage is now superseded by claim_voicing's V-4. Kept for
    close-out's inventory."""
    monkeypatch.setattr(palm_reading, "search", _FakeSearch([_COVERAGE_RETRY_CHUNK]))
    client = _FakeClient(
        responses=[
            (_CLEAN_STUB_TEXT, None),
            (_COVERAGE_CLEAN_RETRY_DRAFT, None),
        ]
    )

    result = generate_palm_reading(
        palm_left="LIFE LINE: A long life line with a gentle curve.", palm_right=None, client=client,
    )

    assert len(client.completions.calls) == 2
    assert result.retry_used is True
    assert result.validation.passed is True
    assert result.validation.failures == ()
    assert result.validation.warnings == ()
    retry_messages = client.completions.calls[1]["messages"]
    assert "coverage: life line supported but never cited" in retry_messages[-1]["content"]


@pytest.mark.skip(reason="F-H: retired at P5, deletion decision at close-out")
def test_coverage_fail_open_final_still_missing_warning_present_reading_displays(monkeypatch):
    """RETIRED (S69 F-H P5): same disposition as the retry test above."""
    monkeypatch.setattr(palm_reading, "search", _FakeSearch([_COVERAGE_RETRY_CHUNK]))
    client = _FakeClient(content=_CLEAN_STUB_TEXT)

    result = generate_palm_reading(
        palm_left="LIFE LINE: A long life line with a gentle curve.", palm_right=None, client=client,
    )

    assert len(client.completions.calls) == 2
    assert result.retry_used is True
    assert result.validation.passed is True
    assert result.validation.failures == ()
    assert result.validation.warnings == ("coverage: life line supported but never cited",)
    assert DISCLAIMER in result.reading_text


def test_validation_report_warnings_defaults_to_empty_tuple():
    """Pre-F-A construction sites keep working unmodified -- the additive
    default, not a required third argument."""
    vr = ValidationReport(passed=True, failures=())

    assert vr.warnings == ()


# ─── Item 18: F-E comma-tolerant absence filler groups (S70) ────────────
#
# _ABSENCE_PATTERNS_BY_FEATURE's per-feature noun-anchored regex (built by
# _build_absence_noun_pattern) is exercised directly via _is_absence(text,
# feature) -- same direct-unit-test convention as Items 16/17 above.


def test_absence_comma_list_phrasing_flips_markings_to_absent():
    """F-E target case: a real production MARKS field listing several
    needle nouns comma-separated before "clearly visible". Pre-F-E, the
    filler hops (?:\\s+\\w+) could not cross a comma, so this text was
    NOT classified as absence for markings/other features."""
    text = "No crosses, stars, grilles, squares, or moles clearly visible"

    assert palm_reading._is_absence(text, "markings/other features") is True


def test_absence_semicolon_list_phrasing_also_flips_markings_to_absent():
    text = "No crosses; stars; grilles; squares; or moles clearly visible"

    assert palm_reading._is_absence(text, "markings/other features") is True


@pytest.mark.parametrize("feature", ["life line", "head line", "heart line"])
def test_absence_islands_regression_guard_stays_present_for_line_features(feature):
    """F-B regression guard: real production LIFE/HEAD/HEART LINE text
    reads "...no breaks, chains, forks, or islands visible" -- line-
    QUALITY detail, not feature absence. "islands" contains the
    markings/other features needle "island", but per-feature noun
    anchoring means this must stay classified as PRESENT (not absence)
    for life/head/heart, since none of those features' own nouns
    ("life"/"head"/"heart") appear in the clause. F-E's comma tolerance
    must not accidentally widen this to match."""
    text = "The line shows no breaks, chains, forks, or islands visible."

    assert palm_reading._is_absence(text, feature) is False


# ─── S125: absence-detection / vision-prompt vocabulary contract ────────
#
# Found live on David's hand (S124 probe, diagnostics/latest_run.md S124):
# his FATE LINE is genuinely absent; the vision prompt correctly wrote
# "FATE LINE: absent" (agent/palm_processor.py's own prompt instructs the
# model to "state plainly if absent or barely visible" for this field),
# but "absent" was not in _ABSENCE_PHRASES -- so _is_genuine_negative_
# absence returned False, the feature stayed in the retrieval query pool,
# cleared the score floor on a junk match, landed in supported_features,
# produced zero claims, and _compute_decline_features folded it into the
# same decline sentence as "doctrine doesn't address this feature" (false
# -- FT_003 fires for other hands in the same probe). Root cause: the
# prompt's invited absence vocabulary and this detector's recognised
# vocabulary are maintained in two different files and had drifted apart.
#
# _PROMPT_INVITED_ABSENCE_PHRASES below is the single hand-curated list of
# every literal absence-signaling phrase agent/palm_processor.py's vision
# prompt (_build_description_system_prompt) actually invites the model to
# write, verified by direct inspection of that prompt (S125): "not clearly
# visible" (the general per-attribute fallback, and the SLOPE/CONTACTS
# escape), "none" (CONVERGENCE/CONTACTS "if none clearly visible ... write
# 'none'"), "unremarkable" (the MOUNTS guidance line), and "absent" (FATE
# LINE's own field instruction). The two tests below are a two-way sync
# guard, not a one-off patch: test_prompt_invites_every_listed_absence_
# phrase catches this list going stale if a phrase is ever REMOVED from
# the prompt; test_every_prompt_invited_absence_phrase_is_recognised_by_
# is_absence is the standing regression guard for this whole class of
# drift -- add a new prompt-invited absence phrase to BOTH this list and
# _ABSENCE_PHRASES (or a TIER 2 per-feature pattern) in the SAME change
# that adds it to the prompt, or this test fails.
#
# "barely visible" is DELIBERATELY excluded from this list -- it names the
# SAME prompt sentence as "absent" but is a real, non-absent quality (the
# line IS visible, just faintly, and doctrine-queryable on that basis).
# This is not a new judgment call: _is_genuine_negative_absence's own
# docstring already gives "Barely visible" as an example of a quality that
# must stay unrecognised here. test_barely_visible_is_deliberately_not_
# absence locks that decision down so a future "fix" doesn't undo it.
_PROMPT_INVITED_ABSENCE_PHRASES = (
    "not clearly visible",
    "none",
    "unremarkable",
    "absent",
)


def test_prompt_invites_every_listed_absence_phrase():
    """Sync guard: every phrase this test module claims the vision prompt
    invites must actually be findable in the prompt text -- catches the
    list above going stale if a phrase is ever removed from the prompt."""
    from agent import palm_processor

    prompt = palm_processor._build_description_system_prompt("left")

    for phrase in _PROMPT_INVITED_ABSENCE_PHRASES:
        assert phrase.lower() in prompt.lower(), (
            f"{phrase!r} is no longer present in agent/palm_processor.py's "
            "vision prompt -- update _PROMPT_INVITED_ABSENCE_PHRASES (and "
            "_ABSENCE_PHRASES if it should be retired there too)."
        )


def test_every_prompt_invited_absence_phrase_is_recognised_by_is_absence():
    """THE S125 regression guard: if a future prompt edit invites a NEW
    absence-signaling word, add it to _PROMPT_INVITED_ABSENCE_PHRASES above
    -- this test then fails until palm_reading._ABSENCE_PHRASES (or a
    per-feature TIER 2 pattern) is taught to recognise it too, closing the
    exact drift class the David/fate-line defect was an instance of."""
    for phrase in _PROMPT_INVITED_ABSENCE_PHRASES:
        assert palm_reading._is_absence(phrase), (
            f"agent/palm_processor.py's vision prompt invites {phrase!r} to "
            "signal absence, but palm_reading._is_absence() does not "
            "recognise it -- _ABSENCE_PHRASES has drifted from the prompt's "
            "vocabulary."
        )


def test_bare_word_absent_is_recognised_as_absence():
    """Direct reproduction of the David/fate-line defect's own raw field
    text (diagnostics/s124_david_e2e_raw.json: 'FATE LINE: absent' parses
    to the bare field value 'absent')."""
    assert palm_reading._is_absence("absent") is True
    assert palm_reading._is_absence("absent", "fate line") is True


def test_barely_visible_is_deliberately_not_absence():
    """'barely visible' is real, doctrine-queryable line quality (the line
    IS visible, just faintly) -- _is_genuine_negative_absence's own
    docstring already documents this as intentional. Locks the design
    decision so a future patch doesn't fold it into the absence vocabulary
    by mistake."""
    assert palm_reading._is_absence("barely visible") is False
    assert palm_reading._is_absence("barely visible", "fate line") is False


def test_genuine_negative_absence_true_for_bare_absent_fate_line():
    """The actual downstream flip this defect was about:
    _is_genuine_negative_absence -- not just _is_absence -- must return
    True for David's real raw text, so the feature exits the retrieval
    query pool and cannot land in supported_features."""
    assert palm_reading._is_genuine_negative_absence("fate line", ["absent"]) is True


def test_apply_support_gate_excludes_genuinely_absent_fate_line():
    """End of the fix's effect chain: with the retrieval query never run
    (empty per_feature_results, matching what _retrieve_per_feature now
    produces for a bare "absent" field, since _resolve_feature_quality
    returns None), fate line must land in NEITHER supported_features NOR
    unsupported_features -- nothing to decline, per _apply_support_gate's
    own genuine-negative-absence branch -- so it cannot reach the
    "classical texts do not clearly address" decline sentence at all.
    Every OTHER registry feature is absent from both input dicts here (an
    empty per_feature_results / texts_by_feature entry, same as "never
    mentioned by any hand"), so _apply_support_gate correctly treats them
    as ordinary unsupported features -- this test only asserts about
    'fate line', the one under test."""
    gated, supported, unsupported = palm_reading._apply_support_gate(
        {"fate line": []}, {"fate line": ["absent"]},
    )

    assert "fate line" not in supported
    assert "fate line" not in unsupported
    decline = palm_reading._compute_decline_features(supported, unsupported, (), ())
    assert "fate line" not in decline


# ═══ S119 STEP 5: sources rebuilt from by-rule citations ════════════════
#
# _build_sources_from_claims used to look up
# chunk_lookup[(feature, claim.chunk_id)] for EVERY claim. Since Step 2 a
# rule claim carries chunk_id=None, so that lookup missed and the claim
# contributed no source at all -- the user-facing "Classical sources"
# panel went near-empty (2 of 6 on the S120 David hand) exactly as rule
# claims became the citation-accurate ones.


def _rule_sourced_claim(claim_id="C1", feature="fate line", rule_id="FT_003",
                        source_page=103, source_quote=None, **overrides):
    from agent.interpretive.claim_extraction import Claim

    kwargs = dict(
        claim_id=claim_id, feature=feature, rule_id=rule_id,
        source_page=source_page,
        source_quote=source_quote or (
            "When the line of fate rises from the wrist and proceeds "
            "straight up the hand to its destination on the Mount of Saturn"
        ),
        claim_text="A fate line rising from the wrist is a sign of good fortune.",
        valence="supports", condition_text=None,
        observation_basis="Line of Fate Slope=straight",
        excluded_from_voice=False, exclusion_reason=None,
    )
    kwargs.update(overrides)
    return Claim.by_rule(**kwargs)


# ─── (1) a by-rule claim yields a real, user-facing source ─────────────


def test_by_rule_claim_yields_a_source_with_its_own_page_and_quote():
    """HARDEST CASE: gated_results is EMPTY -- no retrieval chunk exists
    for this claim at all, which is exactly the production shape (a rule
    claim is self-grounded and needs no chunk). It must still produce a
    source."""
    claim = _rule_sourced_claim()
    sources = palm_reading._build_sources_from_claims(
        "A fate line rising from the wrist is a sign of good fortune.[C1]",
        (claim,),
        gated_results={},
    )

    assert len(sources) == 1
    src = sources[0]
    assert src["page"] == 103
    assert src["rule_id"] == "FT_003"
    assert src["source_quote"] == claim.citation.source_quote
    assert src["feature"] == "fate line"
    assert src["book"] == "cheiroslanguageo00chei_1"
    # 4 original keys ALWAYS present, score explicitly None (ratified
    # Conflict-4 shape) -- no consumer has to branch on existence.
    assert {"book", "page", "score", "feature"} <= set(src)
    assert src["score"] is None


def test_every_cited_rule_claim_produces_a_source_david_hand_shape():
    """The S120 David-hand gap, closed. Six cited rule claims across four
    features previously produced 2 sources (only those whose re-derived
    chunk_id happened to also be in that run's gated set); all six must
    now appear, in order of first citation."""
    claims = tuple(
        _rule_sourced_claim(
            claim_id=f"C{i}", feature=feature, rule_id=rule_id, source_page=page,
            source_quote=f"verbatim span for {rule_id}",
        )
        for i, (feature, rule_id, page) in enumerate(
            [
                ("head line", "H_005", 147),
                ("head line", "H_006", 147),
                ("fate line", "FT_003", 103),
                ("life line", "L_001", 134),
                ("heart line", "HL_006", 160),
                ("mount of venus", "M_001", 112),
            ],
            start=1,
        )
    )
    tagged = " ".join(f"Sentence {i}.[C{i}]" for i in range(1, 7))

    sources = palm_reading._build_sources_from_claims(tagged, claims, gated_results={})

    assert len(sources) == 6
    assert [s["rule_id"] for s in sources] == [
        "H_005", "H_006", "FT_003", "L_001", "HL_006", "M_001",
    ]
    assert [s["page"] for s in sources] == [147, 147, 103, 134, 160, 112]
    assert all(s["score"] is None for s in sources)


def test_two_rules_on_the_same_page_and_feature_are_not_deduped_away():
    """Dedup is by (citation identity, feature). Two DIFFERENT rules citing
    the same page of the same feature are two distinct citations and must
    both survive -- the old (chunk_id, feature) key would have collapsed
    them, since both resolved to the same chunk."""
    claims = (
        _rule_sourced_claim(claim_id="C1", feature="head line", rule_id="H_005", source_page=147),
        _rule_sourced_claim(claim_id="C2", feature="head line", rule_id="H_006", source_page=147),
    )
    sources = palm_reading._build_sources_from_claims("A.[C1] B.[C2]", claims, gated_results={})
    assert [s["rule_id"] for s in sources] == ["H_005", "H_006"]


def test_the_same_rule_cited_twice_yields_one_source():
    claims = (_rule_sourced_claim(claim_id="C1"),)
    sources = palm_reading._build_sources_from_claims("A.[C1] B.[C1]", claims, gated_results={})
    assert len(sources) == 1


def test_uncited_rule_claim_contributes_no_source():
    """Unchanged rule: only claims Stage 2 actually cited become sources."""
    claims = (_rule_sourced_claim(claim_id="C1"), _rule_sourced_claim(claim_id="C2", rule_id="FT_004"))
    sources = palm_reading._build_sources_from_claims("Only the first.[C1]", claims, gated_results={})
    assert [s["rule_id"] for s in sources] == ["FT_003"]


# ─── (4) by-chunk retrieval sources unchanged ──────────────────────────


def test_by_chunk_retrieval_source_is_unchanged():
    """PARITY: the retrieval path still reads this run's gated_results and
    still carries the real score, with no rule_id/source_quote keys."""
    claim = Claim(
        claim_id="C1", feature="life line", chunk_id="cheiroslanguageo00chei_1_p134_c2",
        claim_text="A long life line indicates vitality.", valence="supports",
        condition_text=None, observation_basis="long", excluded_from_voice=False,
        exclusion_reason=None,
    )
    gated = {"life line": [_chunk(chunk_id="cheiroslanguageo00chei_1_p134_c2",
                                  page_ref=134, score=0.61)]}
    sources = palm_reading._build_sources_from_claims("Vitality.[C1]", (claim,), gated)

    assert sources == (
        {"book": "cheiroslanguageo00chei_1", "page": 134, "score": 0.61,
         "feature": "life line"},
    )
    assert "rule_id" not in sources[0]
    assert "source_quote" not in sources[0]


def test_by_chunk_claim_with_no_matching_gated_chunk_still_contributes_nothing():
    """Unchanged: a retrieval claim whose chunk is absent from this run's
    gated set is skipped, exactly as before."""
    claim = Claim(
        claim_id="C1", feature="life line", chunk_id="missing_p1_c0",
        claim_text="text", valence="supports", condition_text=None,
        observation_basis="obs", excluded_from_voice=False, exclusion_reason=None,
    )
    assert palm_reading._build_sources_from_claims("A.[C1]", (claim,), {}) == ()


def test_mixed_run_yields_both_source_kinds_in_citation_order():
    by_chunk = Claim(
        claim_id="C1", feature="life line", chunk_id="cheiroslanguageo00chei_1_p134_c2",
        claim_text="text", valence="supports", condition_text=None,
        observation_basis="obs", excluded_from_voice=False, exclusion_reason=None,
    )
    by_rule = _rule_sourced_claim(claim_id="C2")
    gated = {"life line": [_chunk(chunk_id="cheiroslanguageo00chei_1_p134_c2",
                                  page_ref=134, score=0.61)]}

    sources = palm_reading._build_sources_from_claims("A.[C1] B.[C2]", (by_chunk, by_rule), gated)

    assert [s["score"] for s in sources] == [0.61, None]
    assert [s["page"] for s in sources] == [134, 103]


# ─── (6) the quote is display-only, never LLM-facing ───────────────────


def test_source_quote_never_reaches_the_voicer_prompt():
    """CONTAINMENT. The sources list is built AFTER Stage 2 has run and is
    never passed to a generator; claim_voicing reads only claim_id /
    claim_text / valence / observation_basis off the Claim objects. This
    asserts the quote is absent from the real voicer prompt while being
    present in the sources list."""
    from agent.interpretive.claim_voicing import _build_user_prompt

    quote = "ZZQUOTEZZ When the line of fate rises from the wrist"
    claim = _rule_sourced_claim(source_quote=quote)

    sources = palm_reading._build_sources_from_claims("A.[C1]", (claim,), {})
    assert sources[0]["source_quote"] == quote  # displayed...

    prompt = _build_user_prompt([claim], {"fate line": "straight"})
    assert quote not in prompt  # ...but never prompted
    for voicer_field in ("claim_id", "claim_text", "valence", "observation_basis"):
        assert quote not in str(getattr(claim, voicer_field))
