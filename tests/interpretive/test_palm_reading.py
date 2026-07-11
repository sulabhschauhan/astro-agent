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
    (`.calls`) and returns a fixed, configurable chunk list."""

    def __init__(self, results: list[dict]):
        self._results = results
        self.calls: list[dict] = []

    def __call__(self, question, n_results=None, **filters):
        self.calls.append({"question": question, "n_results": n_results, **filters})
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
    adapted for palm_reading.py's plain-content (not tool-call) response."""

    def __init__(self, content: str | None = None, exception: Exception | None = None):
        self._content = content
        self._exception = exception
        self.calls: list[dict] = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        if self._exception is not None:
            raise self._exception
        return _FakeResponse(self._content)


class _FakeClient:
    """Minimal stand-in for openai.OpenAI, injected via
    generate_palm_reading's `client` seam."""

    def __init__(self, *, content: str | None = None, exception: Exception | None = None):
        self.completions = _FakeCompletions(content=content, exception=exception)
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

_JARGON_STUB_TEXT = (
    "Your LAGNA reveals strong ambition, while a favorable Antardasha this "
    "season brings real opportunity. A gentle yoga forming across your "
    "palm suggests balance and steady growth, and anyone with a bold "
    "yogart mark on their hand should feel encouraged. It is a warm, "
    "positive outlook for the months ahead, with room to deepen important "
    "relationships and explore new creative directions along the way."
)


def test_jargon_injection_case_insensitive_and_word_boundary(monkeypatch):
    monkeypatch.setattr(palm_reading, "search", _FakeSearch([_chunk()]))
    client = _FakeClient(content=_JARGON_STUB_TEXT)

    result = generate_palm_reading(
        palm_left="A long life line with a gentle curve.", palm_right=None, client=client
    )

    assert result.validation.passed is False
    assert len(result.validation.failures) == 1
    failure = result.validation.failures[0]
    assert failure.startswith("jargon_blacklist: found ")
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

    result = generate_palm_reading(
        palm_left="A steady, long life line -- no dates mentioned.",
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

    result = generate_palm_reading(
        palm_left="A steady, long life line.", palm_right=None, client=client
    )

    assert not any("unsupported_dates" in f for f in result.validation.failures)
    assert result.validation.passed is True


# ─── Item 5: length rail ────────────────────────────────────────────────


def test_length_over_700_words_fails(monkeypatch):
    monkeypatch.setattr(palm_reading, "search", _FakeSearch([]))
    long_text = " ".join(["word"] * 701)
    client = _FakeClient(content=long_text)

    result = generate_palm_reading(
        palm_left="A long life line.", palm_right=None, client=client
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
        palm_left="A long, deep life line.", palm_right=None, client=client
    )

    # search WAS called (not refused) and returned an empty list.
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
        palm_left="A long, deep life line with a gentle curve.",
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
        generate_palm_reading(palm_left="A long life line.", palm_right=None, client=client)

    assert len(client.completions.calls) == 1


# ─── Item 9: exactly-one-call invariant on the happy path ─────────────


def test_exactly_one_llm_call_on_happy_path(monkeypatch):
    monkeypatch.setattr(palm_reading, "search", _FakeSearch([_chunk()]))
    client = _FakeClient(content=_CLEAN_STUB_TEXT)

    generate_palm_reading(
        palm_left="A long life line.", palm_right="A curved heart line.", client=client
    )

    assert len(client.completions.calls) == 1


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

    generate_palm_reading(palm_left="A long life line.", palm_right=None, client=client)

    assert len(fake_search.calls) == 1
    assert fake_search.calls[0]["book_name"] == palm_reading._CHEIRO_BOOK


# ─── Item 11: sources propagation ───────────────────────────────────────


def test_sources_propagate_book_page_score(monkeypatch):
    chunk1 = _chunk(text="Chunk one text.", page_ref=12, score=0.81, chunk_id="c1")
    chunk2 = _chunk(text="Chunk two text.", page_ref=57, score=0.66, chunk_id="c2")
    monkeypatch.setattr(palm_reading, "search", _FakeSearch([chunk1, chunk2]))
    client = _FakeClient(content=_CLEAN_STUB_TEXT)

    result = generate_palm_reading(palm_left="A long life line.", palm_right=None, client=client)

    assert result.sources == (
        {"book": "cheiroslanguageo00chei_1", "page": 12, "score": 0.81},
        {"book": "cheiroslanguageo00chei_1", "page": 57, "score": 0.66},
    )
