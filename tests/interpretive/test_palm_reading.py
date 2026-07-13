"""
tests/interpretive/test_palm_reading.py

Ring 2 file for agent/interpretive/palm_reading.py (CLAUDE.md Session 65
"T4 golden semantics" lock -- three-ring model: Ring 1 is the module's own
pure-Python ValidationReport, Ring 2 is this file's stubbed-LLM tests, Ring
3 is a human-rubric ratification artifact). Zero live API calls, zero live
ChromaDB -- CI never asserts live prose here, only the deterministic
plumbing around it.

STUB PATTERN mirrors tests/infra/test_calc_router_stage2.py's Stage 2
conftest-stub precedent: a fake OpenAI client is injected via
generate_palm_reading's `client` seam, recording every call
(`.completions.calls`) and returning canned content per test. Retrieval is
stubbed independently -- palm_reading.py imports `search` from
ingestion.query_engine at module import time (`from ingestion.query_engine
import search`), so the correct monkeypatch site is the name bound inside
the palm_reading module's own namespace (`palm_reading.search`), not
`ingestion.query_engine.search` itself (confirmed by reading palm_reading.py
before writing these tests, not assumed).

NOTE on the autouse `_patch_stage2_openai` fixture in tests/conftest.py:
that fixture patches `openai.OpenAI` (the attribute on the `openai` module),
which is the correct seam for calc_router.py because
calc_router._stage2_classify does `from openai import OpenAI` INSIDE the
function body, re-reading the current attribute on every call. palm_reading.py
instead does `from openai import OpenAI` at MODULE level (import time) --
its own `OpenAI` name is bound once, at import, to the real class, and is
NOT affected by the conftest fixture patching `openai.OpenAI` afterwards.
This is a real difference from the calc_router pattern (flagged in this
run's report, not fixed here per the no-source-edit constraint). It does
not affect these tests: every test below injects an explicit `client=`
argument, so `generate_palm_reading` never reaches its own
`OpenAI()`-construction fallback at all.

Hardest cases first (CLAUDE.md Working Style #3): the fail-closed
ValueError battery (items 1-2) comes before anything that reaches the
network-shaped stubs.

S67 R1 UPDATE: search() is now called once PER OBSERVED canonical hand
feature (life line, head line, ..., see palm_reading._FEATURE_REGISTRY),
not once per whole description -- the monkeypatch site
(`palm_reading.search`) is unchanged, but every expected call count
below now derives from how many features the test's synthetic
palm_left/palm_right/hand_detail text actually observes, not a fixed
"1 call always" assumption. Synthetic descriptions below use F4's flat
"LABEL: text" field format (e.g. "LIFE LINE: ...") rather than free
prose, since that is what feature-extraction parses -- a description
with zero recognizable "LABEL:" fields observes zero features and
never calls search() at all (see the absence-rule test).
"""
from __future__ import annotations

import inspect

import pytest

from agent.interpretive import palm_reading
from agent.interpretive.palm_reading import (
    PalmReadingResult,
    ValidationReport,
    generate_palm_reading,
)
from agent.prompt_builder import DISCLAIMER
from ingestion.query_engine import multi_source_search


# ─── Fakes ──────────────────────────────────────────────────────────────


class _FakeSearch:
    """Drop-in replacement for query_engine.search, injected via
    monkeypatch.setattr(palm_reading, "search", ...). Records every call
    (`.calls`) and returns a fixed, configurable chunk list.

    S67 R1: search() is now called once PER OBSERVED FEATURE, not once
    per whole description -- `raise_for`, if given, is a predicate on
    the query text letting a single fake answer some feature queries
    normally and raise for others (per-feature failure isolation test)."""

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
    """Records every call (`.calls`); returns canned content or raises a
    canned exception, per construction -- mirrors
    tests/infra/test_calc_router_stage2.py's _FakeCompletions shape,
    adapted for palm_reading.py's plain-content (not tool-call) response.

    S66 F2c: `responses`, if given, is a list of (content, exception)
    tuples consumed in call order (one per `.create()` invocation) --
    lets a single fake client answer the first-draft call and the
    retry call differently, for the retry-loop tests below. `content`/
    `exception` (single-shot) stay supported unchanged for every
    pre-existing test that doesn't care about a second call."""

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
    belt-and-suspenders proof for the fail-closed ValueError tests, where
    `.completions.calls == []` is the real proof."""
    return _FakeClient(exception=AssertionError("LLM call must not fire for a fail-closed ValueError case"))


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


_CLEAN_STUB_TEXT = (
    "Your hand shows a long, unbroken life line, suggesting steady vitality "
    "and resilience. The heart line curves gently upward, pointing to warmth "
    "and openness in close relationships. A well-defined head line reflects "
    "clear, practical thinking, while a faint fate line hints at a path you "
    "are still shaping through your own choices rather than one laid out for "
    "you. Overall, this is a hand that reflects balance -- steady energy, "
    "genuine warmth, and a thoughtful approach to the years ahead."
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

# Stub neutralized S66 -- "favorable" joined the self-help blacklist (Ring
# 3 pass 1); swapped for "promising" (not on the 9-term list) so this test
# isolates the jargon validator alone.
_JARGON_STUB_TEXT = (
    "Your LAGNA reveals strong ambition, while a promising Antardasha this "
    "season brings real opportunity. A gentle yoga forming across your "
    "palm suggests balance and steady growth, and anyone with a bold "
    "yogart mark on their hand should feel encouraged. It is a warm, "
    "positive outlook for the months ahead, with room to deepen important "
    "relationships and explore new creative directions along the way."
)


def test_jargon_injection_case_insensitive_and_word_boundary(monkeypatch):
    # 1 observed feature (life line) -> 1 search call.
    monkeypatch.setattr(palm_reading, "search", _FakeSearch([_chunk()]))
    client = _FakeClient(content=_JARGON_STUB_TEXT)

    result = generate_palm_reading(
        palm_left="LIFE LINE: A long life line with a gentle curve.", palm_right=None, client=client
    )

    assert result.validation.passed is False
    assert len(result.validation.failures) == 1
    failure = result.validation.failures[0]
    assert failure.startswith("jargon_blacklist")
    assert failure.startswith("jargon_blacklist: found ")
    assert not any("self_help_blacklist" in f for f in result.validation.failures)
    hits = {h.strip() for h in failure.removeprefix("jargon_blacklist: found ").split(",")}
    # "LAGNA" and "Antardasha" hit despite mixed case; "yoga" hits once from
    # "yoga forming" -- NOT from "yogart" (word-boundary must not trip on a
    # substring match).
    assert hits == {"lagna", "antardasha", "yoga"}

    # Direct boundary proof against the module's own compiled pattern: only
    # ONE "yoga" match in the stub text, from "yoga forming" -- if the
    # word-boundary logic were broken, "yogart" would contribute a second.
    raw_matches = palm_reading._JARGON_PATTERN.findall(_JARGON_STUB_TEXT)
    assert raw_matches.count("yoga") == 1


# ─── Item 4: fabricated year vs. supported year (boundary pair) ────────

_YEAR_STUB_TEXT = (
    "A period of expansion opens around 2031, bringing new opportunities "
    "for growth and travel. Your hand shows steady resilience through "
    "life's changes, with a natural warmth that draws others close. Trust "
    "your instincts during this stretch and lean into new connections -- "
    "they carry real long-term value."
)


def test_fabricated_year_absent_from_context_fails(monkeypatch):
    monkeypatch.setattr(
        palm_reading,
        "search",
        _FakeSearch([_chunk(text="A steady life line with no numeric markers.")]),
    )
    client = _FakeClient(content=_YEAR_STUB_TEXT)

    # 1 observed feature (life line) -> 1 search call.
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
    client = _FakeClient(content=_YEAR_STUB_TEXT)

    # 1 observed feature (life line) -> 1 search call.
    result = generate_palm_reading(
        palm_left="LIFE LINE: A steady, long life line.", palm_right=None, client=client
    )

    assert not any("unsupported_dates" in f for f in result.validation.failures)
    assert result.validation.passed is True


# ─── Item 5: length rail ────────────────────────────────────────────────


def test_length_over_700_words_fails(monkeypatch):
    monkeypatch.setattr(palm_reading, "search", _FakeSearch([]))
    long_text = " ".join(["word"] * 701)
    client = _FakeClient(content=long_text)

    result = generate_palm_reading(
        palm_left="LIFE LINE: A long life line.", palm_right=None, client=client
    )

    assert result.validation.passed is False
    assert any(f.startswith("length_guard:") for f in result.validation.failures)
    assert any("701" in f for f in result.validation.failures)


# ─── Item 6: empty retrieval proceeds with low-confidence caveat ───────


def test_empty_retrieval_proceeds_with_low_confidence_caveat(monkeypatch):
    fake_search = _FakeSearch([])
    monkeypatch.setattr(palm_reading, "search", fake_search)
    client = _FakeClient(content=_CLEAN_STUB_TEXT)

    result = generate_palm_reading(
        palm_left="LIFE LINE: A long, deep life line.", palm_right=None, client=client
    )

    # search WAS called (not refused) and returned an empty list.
    # 1 observed feature (life line) -> 1 search call.
    assert len(fake_search.calls) == 1
    assert len(client.completions.calls) == 1
    system_prompt_sent = client.completions.calls[0]["messages"][0]["content"]
    assert "weak match" in system_prompt_sent.lower()
    assert result.validation.passed is True
    assert result.sources == ()


# ─── Item 7: happy path, left-only ──────────────────────────────────────


def test_happy_path_left_only(monkeypatch):
    monkeypatch.setattr(palm_reading, "search", _FakeSearch([_chunk()]))
    client = _FakeClient(content=_CLEAN_STUB_TEXT)

    result = generate_palm_reading(
        palm_left="LIFE LINE: A long, deep life line with a gentle curve.",
        palm_right=None,
        client=client,
    )

    assert result.validation.passed is True
    assert result.validation.failures == ()
    # DISCLAIMER appears exactly once, at the end.
    assert result.reading_text.endswith(DISCLAIMER)
    assert result.reading_text.count(DISCLAIMER) == 1
    # No pre-append seam is exposed by palm_reading.py (confirmed by
    # reading the module) -- fallback per the task spec: prove the
    # disclaimer text was never part of what the stub returned, so it
    # could not have been part of what the Ring 1 validators inspected.
    assert DISCLAIMER not in _CLEAN_STUB_TEXT


# ─── Item 8: client failure -> RuntimeError, no retry ──────────────────


def test_client_raises_becomes_runtime_error_no_retry(monkeypatch):
    monkeypatch.setattr(palm_reading, "search", _FakeSearch([]))
    client = _FakeClient(exception=ConnectionError("simulated network failure"))

    with pytest.raises(RuntimeError, match="GPT-4o reading-generation call failed"):
        generate_palm_reading(palm_left="LIFE LINE: A long life line.", palm_right=None, client=client)

    assert len(client.completions.calls) == 1


# ─── Item 9: exactly-one-call invariant when the first draft passes ────
# NOTE (S67 R1): this invariant is about the LLM call count (the F2c
# retry mechanism), which R1 does not touch -- it is NOT the old
# "exactly one search() call" invariant, which R1 makes false by design
# (search() is now called once per observed feature). This test's fixture
# below deliberately observes 2 features (life line, heart line) to prove
# the LLM-call invariant holds even when multiple search() calls happen.


def test_exactly_one_llm_call_when_first_draft_passes(monkeypatch):
    # 2 observed features (life line from palm_left, heart line from
    # palm_right) -> 2 search calls; this test asserts the SEPARATE LLM
    # call count only (unaffected by how many search() calls occurred).
    fake_search = _FakeSearch([_chunk()])
    monkeypatch.setattr(palm_reading, "search", fake_search)
    client = _FakeClient(content=_CLEAN_STUB_TEXT)

    result = generate_palm_reading(
        palm_left="LIFE LINE: A long life line.",
        palm_right="HEART LINE: A curved heart line.",
        client=client,
    )

    assert len(fake_search.calls) == 2
    assert len(client.completions.calls) == 1
    assert result.validation.passed is True
    assert result.retry_used is False


# ─── Item 9b: S66 F2c validator-fed single retry ────────────────────────

_RETRY_FIRST_DRAFT_STUB_TEXT = (
    "This hand promises stability through disciplined effort, with a firm "
    "grip on practical matters and steady, deliberate choices in every "
    "undertaking that comes before it."
)

_RETRY_SECOND_DRAFT_STILL_FAILS_STUB_TEXT = (
    "This calm hand still speaks of quiet empowerment gained through "
    "disciplined practice and patient, steady effort across many years."
)


def test_retry_after_failed_first_draft_then_clean_retry_passes(monkeypatch):
    """(a) First draft trips the validator; the retry draft is clean ->
    exactly 2 calls, passed=True, retry_used=True, and the retry's user
    turn carries the exact failure string back to the model."""
    monkeypatch.setattr(palm_reading, "search", _FakeSearch([_chunk()]))
    client = _FakeClient(
        responses=[
            (_RETRY_FIRST_DRAFT_STUB_TEXT, None),
            (_CLEAN_STUB_TEXT, None),
        ]
    )

    result = generate_palm_reading(
        palm_left="LIFE LINE: A long life line with a gentle curve.", palm_right=None, client=client,
    )

    assert len(client.completions.calls) == 2
    assert result.validation.passed is True
    assert result.validation.failures == ()
    assert result.retry_used is True

    retry_messages = client.completions.calls[1]["messages"]
    # system, user (original), assistant (failed draft), user (feedback).
    assert len(retry_messages) == 4
    assert retry_messages[0]["role"] == "system"
    assert retry_messages[1]["role"] == "user"
    assert retry_messages[2] == {"role": "assistant", "content": _RETRY_FIRST_DRAFT_STUB_TEXT}
    assert retry_messages[3]["role"] == "user"
    assert "self_help_blacklist: found stability" in retry_messages[3]["content"]


def test_retry_after_failed_first_draft_still_fails_stays_failed(monkeypatch):
    """(b) Both drafts trip the validator -> exactly 2 calls (no third
    attempt), fail-closed: passed=False, retry_used=True, and the
    SECOND draft's failure is what's reported (not the first's)."""
    monkeypatch.setattr(palm_reading, "search", _FakeSearch([_chunk()]))
    client = _FakeClient(
        responses=[
            (_RETRY_FIRST_DRAFT_STUB_TEXT, None),
            (_RETRY_SECOND_DRAFT_STILL_FAILS_STUB_TEXT, None),
        ]
    )

    result = generate_palm_reading(
        palm_left="LIFE LINE: A long life line with a gentle curve.", palm_right=None, client=client,
    )

    assert len(client.completions.calls) == 2
    assert result.validation.passed is False
    assert result.retry_used is True
    assert any("empowerment" in f for f in result.validation.failures)
    assert not any("stability" in f for f in result.validation.failures)


def test_retry_call_raises_becomes_runtime_error_no_third_call(monkeypatch):
    """(c) The first draft trips the validator, but the retry call
    itself raises -> RuntimeError propagates (same as item 8's
    single-call case), and no third call is ever attempted."""
    monkeypatch.setattr(palm_reading, "search", _FakeSearch([_chunk()]))
    client = _FakeClient(
        responses=[
            (_RETRY_FIRST_DRAFT_STUB_TEXT, None),
            (None, ConnectionError("simulated network failure on retry")),
        ]
    )

    with pytest.raises(RuntimeError, match="GPT-4o reading-generation call failed"):
        generate_palm_reading(
            palm_left="LIFE LINE: A long life line with a gentle curve.", palm_right=None, client=client,
        )

    assert len(client.completions.calls) == 2


# ─── Item 10: Cheiro book filter ────────────────────────────────────────


def test_search_filters_to_canonical_cheiro_book(monkeypatch):
    # Independent verification: the canonical Cheiro string is read directly
    # from ingestion/query_engine.py's own source (its multi_source_search()
    # default 14-book list, S12 fixed-exact-string convention) rather than
    # hardcoded from memory, then cross-checked against the constant
    # palm_reading.py itself exposes.
    source = inspect.getsource(multi_source_search)
    assert "cheiroslanguageo00chei_1" in source
    assert palm_reading._CHEIRO_BOOK == "cheiroslanguageo00chei_1"

    fake_search = _FakeSearch([_chunk()])
    monkeypatch.setattr(palm_reading, "search", fake_search)
    client = _FakeClient(content=_CLEAN_STUB_TEXT)

    generate_palm_reading(palm_left="LIFE LINE: A long life line.", palm_right=None, client=client)

    # 1 observed feature (life line) -> 1 search call.
    assert len(fake_search.calls) == 1
    assert fake_search.calls[0]["book_name"] == palm_reading._CHEIRO_BOOK
    # S67 R1 threshold: n_results is now per-feature (3), not the old
    # whole-description 6.
    assert fake_search.calls[0]["n_results"] == palm_reading._N_RESULTS_PER_FEATURE == 3


# ─── Item 11: sources propagation ───────────────────────────────────────


def test_sources_propagate_book_page_score(monkeypatch):
    # 1 observed feature (life line) -> 1 search call, returning 2 chunks.
    chunk1 = _chunk(text="Chunk one text.", page_ref=12, score=0.81, chunk_id="c1")
    chunk2 = _chunk(text="Chunk two text.", page_ref=57, score=0.66, chunk_id="c2")
    monkeypatch.setattr(palm_reading, "search", _FakeSearch([chunk1, chunk2]))
    client = _FakeClient(content=_CLEAN_STUB_TEXT)

    result = generate_palm_reading(palm_left="LIFE LINE: A long life line.", palm_right=None, client=client)

    # S67 R1: sources now carry a "feature" tag (both chunks came from
    # the single "life line" query).
    assert result.sources == (
        {"book": "cheiroslanguageo00chei_1", "page": 12, "score": 0.81, "feature": "life line"},
        {"book": "cheiroslanguageo00chei_1", "page": 57, "score": 0.66, "feature": "life line"},
    )


# ─── Item 12: self-help register validator (S66 F2b) ───────────────────

_STABILITY_STUB_TEXT = (
    "This hand promises STABILITY through disciplined effort, with a firm "
    "grip on practical matters and a steady, deliberate approach to every "
    "undertaking that comes before it."
)


def test_self_help_case_insensitive(monkeypatch):
    monkeypatch.setattr(palm_reading, "search", _FakeSearch([_chunk()]))
    client = _FakeClient(content=_STABILITY_STUB_TEXT)

    result = generate_palm_reading(
        palm_left="LIFE LINE: A long life line with a gentle curve.", palm_right=None, client=client
    )

    assert result.validation.passed is False
    assert len(result.validation.failures) == 1
    failure = result.validation.failures[0]
    assert failure == "self_help_blacklist: found stability"


# Word-boundary positive/negative pair: "instability" and "journeyman" both
# contain a blacklisted term as a substring but not as a standalone word --
# the literal 9-term list is deliberate (THRESHOLD DISCIPLINE, see
# _SELF_HELP_BLACKLIST's comment in palm_reading.py); this test proves the
# word-boundary regex does not over-match on these substrings.
_WORD_BOUNDARY_STUB_TEXT = (
    "A hand marked by inner instability at times still moves toward calm "
    "judgment, and this journeyman spirit for craft rewards patient hands "
    "with quiet mastery over many years."
)


def test_self_help_word_boundary_excludes_substrings(monkeypatch):
    monkeypatch.setattr(palm_reading, "search", _FakeSearch([_chunk()]))
    client = _FakeClient(content=_WORD_BOUNDARY_STUB_TEXT)

    result = generate_palm_reading(
        palm_left="LIFE LINE: A long life line with a gentle curve.", palm_right=None, client=client
    )

    assert not any("self_help_blacklist" in f for f in result.validation.failures)
    assert result.validation.passed is True


# Non-listed conjugation "navigated" does NOT trip -- documents the
# narrowness of the 9-term list as a deliberate choice (THRESHOLD
# DISCIPLINE revisit trigger: pass-2 evidence that a conjugation like this
# is itself an observed offender, not a preemptive widening here).
_NAVIGATED_STUB_TEXT = (
    "The head line, once navigated with hesitation in youth, now runs firm "
    "and true across the palm, showing settled judgment and clear resolve."
)


def test_self_help_unlisted_conjugation_does_not_trip(monkeypatch):
    monkeypatch.setattr(palm_reading, "search", _FakeSearch([_chunk()]))
    client = _FakeClient(content=_NAVIGATED_STUB_TEXT)

    result = generate_palm_reading(
        palm_left="LIFE LINE: A long life line with a gentle curve.", palm_right=None, client=client
    )

    assert not any("self_help_blacklist" in f for f in result.validation.failures)
    assert result.validation.passed is True


_MULTI_TERM_STUB_TEXT = (
    "The heart line points to fulfilling bonds forged through effort, "
    "while the head line traces a long journey of independent judgment; a "
    "second look at the fate line confirms this journey continues on firm "
    "ground for fulfilling work ahead."
)


def test_self_help_multi_term_single_sorted_deduped_failure(monkeypatch):
    """Mirrors the jargon validator's format assertions (item 3): two
    distinct terms, each appearing twice, collapse to one failure string
    listing both terms once, sorted."""
    monkeypatch.setattr(palm_reading, "search", _FakeSearch([_chunk()]))
    client = _FakeClient(content=_MULTI_TERM_STUB_TEXT)

    result = generate_palm_reading(
        palm_left="LIFE LINE: A long life line with a gentle curve.", palm_right=None, client=client
    )

    assert result.validation.passed is False
    assert len(result.validation.failures) == 1
    assert result.validation.failures[0] == "self_help_blacklist: found fulfilling, journey"


_CHEIRO_VOICE_STUB_TEXT = (
    "The life line runs long and unbroken around the base of the thumb, "
    "marking sound constitution and vigor that will carry through many "
    "years. A deep, steady heart line shows warmth given freely but never "
    "wasted, while a firm head line reveals judgment sharpened by direct "
    "experience rather than idle theory. The fate line, clear and "
    "undivided, promises success won through personal exertion rather "
    "than chance."
)


def test_self_help_clean_cheiro_register_passes(monkeypatch):
    monkeypatch.setattr(palm_reading, "search", _FakeSearch([_chunk()]))
    client = _FakeClient(content=_CHEIRO_VOICE_STUB_TEXT)

    result = generate_palm_reading(
        palm_left="LIFE LINE: A long life line with a gentle curve.", palm_right=None, client=client
    )

    assert result.validation.passed is True
    assert result.validation.failures == ()


_EMPOWERMENT_STUB_TEXT = (
    "This hand speaks of quiet empowerment gained through steady effort, "
    "with practical instincts and calm resolve carrying you through each "
    "new challenge that life presents along the way."
)


def test_self_help_integration_empowerment_fails_and_propagates(monkeypatch):
    """Full generate_palm_reading() integration: a stub reading containing
    a blacklisted term must produce a failed, propagated ValidationReport
    inside the returned PalmReadingResult -- not just a bare validator
    function result."""
    monkeypatch.setattr(palm_reading, "search", _FakeSearch([_chunk()]))
    client = _FakeClient(content=_EMPOWERMENT_STUB_TEXT)

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


# ─── Item 13: S67 R1 per-feature retrieval -- hardest new cases first ──

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


def test_absence_rule_all_features_absent_yields_zero_search_calls_and_low_confidence(monkeypatch):
    """(13a) Hardest new case: all 10 registry features resolve to "no
    query" -- the 7 plain fields (life/head/heart/fate/thumb/fingers/
    marks) are each absence-phrased on their only mentioning source
    (this single hand), and sun line / mount of venus / mount of jupiter
    are never NAMED at all (OTHER LINES / MOUNTS present but don't say
    "sun"/"venus"/"jupiter") -> not observed. Derivation: 0 of 10
    features query -> 0 search calls, and the empty-retrieval
    low-confidence path fires exactly as it does for a genuinely empty
    ChromaDB result."""
    # Configured to return a chunk if ever called -- a call here would
    # be a strong, visible test failure (sources would be non-empty),
    # not a silent pass.
    fake_search = _FakeSearch([_chunk()])
    monkeypatch.setattr(palm_reading, "search", fake_search)
    client = _FakeClient(content=_CLEAN_STUB_TEXT)

    result = generate_palm_reading(palm_left=_ALL_ABSENT_LEFT, palm_right=None, client=client)

    assert fake_search.calls == []
    assert result.sources == ()
    system_prompt_sent = client.completions.calls[0]["messages"][0]["content"]
    assert "weak match" in system_prompt_sent.lower()


_DEGENERATE_QUALITY_LEFT = "LIFE LINE: Present."


def test_fail_open_degenerate_quality_still_queries_and_logs(monkeypatch, caplog):
    """(13b) LIFE LINE's text is just "Present." -- not absence-phrased,
    but quality extraction degenerates to the bare word "present" (no
    second clause to fall back to, unlike the real "Present, deep,
    long..." fields). FAIL OPEN: the feature is still queried, using
    its own raw field text as the quality, and a warning is logged --
    silent feature-dropping is the S23 failure mode this guards
    against, junk retrieval is recoverable."""
    fake_search = _FakeSearch([_chunk()])
    monkeypatch.setattr(palm_reading, "search", fake_search)
    client = _FakeClient(content=_CLEAN_STUB_TEXT)

    with caplog.at_level("WARNING"):
        generate_palm_reading(palm_left=_DEGENERATE_QUALITY_LEFT, palm_right=None, client=client)

    # 1 observed feature (life line, fail-open path) -> 1 search call.
    assert len(fake_search.calls) == 1
    assert "present" in fake_search.calls[0]["question"].lower()
    assert "fail-open" in caplog.text.lower()


def test_one_feature_search_failure_does_not_kill_reading_other_feature_succeeds(monkeypatch, caplog):
    """(13c) 2 observed features (life line, heart line); the life-line
    query raises, the heart-line query succeeds -> the reading still
    proceeds (no exception propagates), the failure is logged, and
    sources reflect only the surviving feature's chunk."""
    heart_chunk = _chunk(text="Heart line chunk.", page_ref=57, score=0.7, chunk_id="heart1")

    def _raise_for(question: str) -> bool:
        return "life line" in question

    fake_search = _FakeSearch([heart_chunk], raise_for=_raise_for)
    monkeypatch.setattr(palm_reading, "search", fake_search)
    client = _FakeClient(content=_CLEAN_STUB_TEXT)

    with caplog.at_level("WARNING"):
        result = generate_palm_reading(
            palm_left="LIFE LINE: A long life line.",
            palm_right="HEART LINE: A curved heart line.",
            client=client,
        )

    # 2 observed features (life line, heart line) -> 2 search calls
    # attempted (both, regardless of the first one raising).
    assert len(fake_search.calls) == 2
    assert result.sources == (
        {"book": "cheiroslanguageo00chei_1", "page": 57, "score": 0.7, "feature": "heart line"},
    )
    assert "life line" in caplog.text.lower()


def test_query_template_two_hand_merged_quality_literal_shape(monkeypatch):
    """(13d) Two-hand differing fate-line qualities (barely visible vs.
    moderately deep -- the real Ring 3 pass-2 fixture pair,
    diagnostics/ring3_palm_rubric_S66_pass2.md) merge into exactly the
    ratified variant-iii template shape."""
    fake_search = _FakeSearch([_chunk()])
    monkeypatch.setattr(palm_reading, "search", fake_search)
    client = _FakeClient(content=_CLEAN_STUB_TEXT)

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
    assert fake_search.calls[0]["n_results"] == palm_reading._N_RESULTS_PER_FEATURE == 3


def test_per_feature_map_ordering_and_dedupe_for_display(monkeypatch):
    """(13e) Life line (registry position 1) and head line (position 2)
    both retrieve the SAME chunk_id (corpus overlap) -- the assembled
    user-message prompt shows it once, under life line's heading only
    (first-feature-wins for display, registry order); sources still
    carries BOTH assignments (the per-feature map keeps every
    assignment -- the future R3 evidence structure)."""
    dupe_chunk = _chunk(text="Shared passage.", page_ref=99, score=0.5, chunk_id="dupe1")
    # Same chunk returned for every call, regardless of query.
    fake_search = _FakeSearch([dupe_chunk])
    monkeypatch.setattr(palm_reading, "search", fake_search)
    client = _FakeClient(content=_CLEAN_STUB_TEXT)

    result = generate_palm_reading(
        palm_left="LIFE LINE: A long life line.\nHEAD LINE: A slightly curved head line.",
        palm_right=None,
        client=client,
    )

    # 2 observed features (life line, head line) -> 2 search calls, same
    # chunk_id both times.
    assert len(fake_search.calls) == 2
    user_message = client.completions.calls[0]["messages"][1]["content"]
    assert user_message.count("Shared passage.") == 1
    assert "### life line" in user_message
    assert "### head line" not in user_message  # suppressed: chunk already shown

    assert result.sources == (
        {"book": "cheiroslanguageo00chei_1", "page": 99, "score": 0.5, "feature": "life line"},
        {"book": "cheiroslanguageo00chei_1", "page": 99, "score": 0.5, "feature": "head line"},
    )


def test_sources_carry_distinct_feature_tags(monkeypatch):
    """(13f) Two observed features, each returning its OWN distinct
    chunk -- sources must tag each with the feature that actually
    produced it, not a shared/default value."""
    life_chunk = _chunk(text="Life line passage.", page_ref=134, score=0.6, chunk_id="life1")
    heart_chunk = _chunk(text="Heart line passage.", page_ref=88, score=0.55, chunk_id="heart1")

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
    client = _FakeClient(content=_CLEAN_STUB_TEXT)

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
