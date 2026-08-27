"""
tests/interpretive/test_contact_llm_fallback.py

Tests for agent/interpretive/contact_llm_fallback.py (S108) -- standalone,
hardest-case-first, STUBBED client only (no network, no live LLM call
anywhere in this file). This module is not wired into the pipeline yet
(S109); these tests exercise resolve_unresolved_contacts() directly.
"""

from __future__ import annotations

import json

import pytest

from agent.interpretive import contact_llm_fallback as clf
from agent.interpretive.contact_mapper import _DISTINCT_VERB_TABLE, _JOIN_FAMILY_VERBS


# ─── Stub client -- mirrors the OpenAI client.chat.completions.create shape ──

class _StubMessage:
    def __init__(self, content: str):
        self.content = content


class _StubChoice:
    def __init__(self, content: str):
        self.message = _StubMessage(content)


class _StubResponse:
    def __init__(self, content: str):
        self.choices = [_StubChoice(content)]


class _StubClient:
    """Records every call for assertion; `resolutions` is what the stub
    returns as the JSON `resolutions` list for THIS batch (assumes one
    call per test, since that's this module's own contract)."""

    def __init__(self, resolutions=None, *, raw_content: str | None = None, raises: Exception | None = None):
        self._resolutions = resolutions
        self._raw_content = raw_content
        self._raises = raises
        self.call_count = 0
        self.last_kwargs: dict | None = None
        self.chat = self
        self.completions = self

    def create(self, **kwargs):
        self.call_count += 1
        self.last_kwargs = kwargs
        if self._raises is not None:
            raise self._raises
        if self._raw_content is not None:
            return _StubResponse(self._raw_content)
        return _StubResponse(json.dumps({"resolutions": self._resolutions}))


def _contact(verb, position="at start", target="Line of Life", clarity="clear"):
    return {"target": target, "verb": verb, "position": position, "clarity": clarity}


# ─── Known synonym -- the primary rescue case ──────────────────────────────


def test_known_synonym_fuses_to_merges_at_start_resolves_joins_at_origin():
    # HARDEST CASE FIRST: the exact rescue scenario this module exists for.
    client = _StubClient(resolutions=["merges"])
    results, audits = clf.resolve_unresolved_contacts(
        [_contact("fuses", position="at start")], client
    )
    assert client.call_count == 1
    assert results[0]["token"] == "joins_at_origin"
    assert results[0]["raw_verb"] == "fuses"  # verbatim ORIGINAL, not the LLM's canonical
    assert "fuses" in results[0]["reason"] and "merges" in results[0]["reason"]
    assert audits[0]["raw_verb"] == "fuses"
    assert audits[0]["llm_canonical_choice"] == "merges"
    assert audits[0]["final_token"] == "joins_at_origin"
    assert audits[0]["disposition"] == "resolved"


def test_known_synonym_fuses_to_merges_mid_course_resolves_meets():
    # Proves the deterministic position-split still governs the LLM's
    # canonical choice -- same LLM answer, different position, different
    # token.
    client = _StubClient(resolutions=["merges"])
    results, _ = clf.resolve_unresolved_contacts(
        [_contact("fuses", position="mid-course")], client
    )
    assert results[0]["token"] == "meets"


def test_distinct_verb_synonym_severs_to_cuts_position_independent():
    client = _StubClient(resolutions=["cuts"])
    results, audits = clf.resolve_unresolved_contacts(
        [_contact("severs", position="unknown", target="Line of Head")], client
    )
    assert results[0]["token"] == "cuts"
    assert audits[0]["disposition"] == "resolved"
    # Position-independent: a different position must not change the outcome.
    client2 = _StubClient(resolutions=["cuts"])
    results2, _ = clf.resolve_unresolved_contacts(
        [_contact("severs", position="at start", target="Line of Head")], client2
    )
    assert results2[0]["token"] == "cuts"


# ─── Unclear / hallucination -- fail-closed per item ───────────────────────


def test_llm_says_unclear_token_stays_none_with_reason_no_guess():
    client = _StubClient(resolutions=["unclear"])
    results, audits = clf.resolve_unresolved_contacts([_contact("wobbles")], client)
    assert results[0]["token"] is None
    assert results[0]["confidence"] is None
    assert isinstance(results[0]["reason"], str) and results[0]["reason"].strip()
    assert audits[0]["disposition"] == "llm_unclear"
    assert audits[0]["final_token"] is None


def test_hallucinated_canonical_not_in_closed_set_treated_unclear_logged(caplog):
    # "obliterates" is not a declared verb -- must never leak through as a
    # token, must be treated exactly like "unclear".
    client = _StubClient(resolutions=["obliterates"])
    with caplog.at_level("WARNING"):
        results, audits = clf.resolve_unresolved_contacts([_contact("destroys")], client)
    assert results[0]["token"] is None
    assert "obliterates" in results[0]["reason"]
    assert audits[0]["disposition"] == "hallucination"
    assert audits[0]["llm_canonical_choice"] == "obliterates"
    assert any("obliterates" in rec.message for rec in caplog.records)


# ─── Structural batch failures -- whole batch fails to unclear, never raises ─


def test_malformed_json_whole_batch_unclear_no_raise():
    client = _StubClient(raw_content="not valid json{{{")
    contacts = [_contact("fuses"), _contact("severs"), _contact("wobbles")]
    results, audits = clf.resolve_unresolved_contacts(contacts, client)  # must not raise
    assert len(results) == 3
    assert all(r["token"] is None for r in results)
    assert all(a["disposition"] == "batch_malformed_response" for a in audits)


def test_missing_resolutions_key_whole_batch_unclear_no_raise():
    client = _StubClient(raw_content=json.dumps({"not_resolutions": ["merges"]}))
    results, audits = clf.resolve_unresolved_contacts([_contact("fuses")], client)
    assert results[0]["token"] is None
    assert audits[0]["disposition"] == "batch_malformed_response"


def test_wrong_length_resolutions_list_whole_batch_unclear_no_raise():
    client = _StubClient(resolutions=["merges"])  # 1 answer for 2 contacts
    contacts = [_contact("fuses"), _contact("severs")]
    results, audits = clf.resolve_unresolved_contacts(contacts, client)  # must not raise
    assert len(results) == 2
    assert all(r["token"] is None for r in results)
    assert all(a["disposition"] == "batch_malformed_response" for a in audits)


def test_client_raises_whole_batch_unclear_no_raise():
    client = _StubClient(raises=RuntimeError("connection reset"))
    contacts = [_contact("fuses"), _contact("severs")]
    results, audits = clf.resolve_unresolved_contacts(contacts, client)  # must not raise
    assert len(results) == 2
    assert all(r["token"] is None for r in results)
    assert all(a["disposition"] == "batch_call_failed" for a in audits)
    assert all("connection reset" in r["reason"] for r in results)


def test_client_timeout_exception_whole_batch_unclear_no_raise():
    client = _StubClient(raises=TimeoutError("timed out"))
    results, audits = clf.resolve_unresolved_contacts([_contact("fuses")], client)
    assert results[0]["token"] is None
    assert audits[0]["disposition"] == "batch_call_failed"


# ─── Empty input / batching ────────────────────────────────────────────────


def test_empty_input_list_returns_empty_makes_zero_calls():
    client = _StubClient(resolutions=[])
    results, audits = clf.resolve_unresolved_contacts([], client)
    assert results == []
    assert audits == []
    assert client.call_count == 0


def test_batch_of_three_unresolved_makes_exactly_one_call():
    client = _StubClient(resolutions=["merges", "cuts", "unclear"])
    contacts = [_contact("fuses"), _contact("severs"), _contact("wobbles")]
    results, audits = clf.resolve_unresolved_contacts(contacts, client)
    assert client.call_count == 1
    assert len(results) == 3
    assert len(audits) == 3
    assert results[0]["token"] == "joins_at_origin"  # fuses->merges, at start
    assert results[1]["token"] == "cuts"              # severs->cuts
    assert results[2]["token"] is None                 # wobbles->unclear


# ─── Already-resolved contacts: zero LLM involvement, still re-validated ───


def test_already_resolved_contact_makes_zero_calls_and_is_not_blindly_trusted():
    """Per contract, this module should only ever RECEIVE token=None
    contacts -- but it does not blindly trust that. A resolvable verb
    ("joins") passed in anyway must still go through map_contact
    re-validation (deterministically resolving it), NOT a blind LLM call
    that would otherwise burn a call on something the deterministic layer
    already handles."""
    client = _StubClient(resolutions=["SHOULD_NEVER_BE_USED"])
    results, audits = clf.resolve_unresolved_contacts([_contact("joins", position="at start")], client)
    assert client.call_count == 0
    assert results[0]["token"] == "joins_at_origin"
    assert audits[0]["disposition"] == "already_resolved_no_llm_needed"
    assert audits[0]["llm_canonical_choice"] is None


def test_mixed_batch_already_resolved_and_unresolved_only_calls_for_unresolved():
    # 2 already-resolved (joins, cuts) + 1 genuinely unresolved (fuses) --
    # the LLM call must cover ONLY the unresolved one.
    client = _StubClient(resolutions=["merges"])
    contacts = [
        _contact("joins", position="at start"),
        _contact("crosses", position="unknown", target="Line of Head"),
        _contact("fuses", position="at start"),
    ]
    results, audits = clf.resolve_unresolved_contacts(contacts, client)
    assert client.call_count == 1
    assert results[0]["token"] == "joins_at_origin"  # joins, already resolved
    assert results[1]["token"] == "cuts"              # crosses, already resolved
    assert results[2]["token"] == "joins_at_origin"  # fuses -> merges -> joins_at_origin, via LLM
    assert audits[0]["disposition"] == "already_resolved_no_llm_needed"
    assert audits[1]["disposition"] == "already_resolved_no_llm_needed"
    assert audits[2]["disposition"] == "resolved"
    # The user prompt sent to the LLM must have covered exactly 1 verb.
    sent_messages = client.last_kwargs["messages"]
    user_content = sent_messages[1]["content"]
    assert "Match each of the following 1 verb(s)" in user_content
    assert "fuses" in user_content
    assert "joins" not in user_content.split("Match")[1]  # already-resolved verbs never sent


# ─── Closed choice set: derived, never hardcoded ───────────────────────────


def test_closed_choice_set_is_derived_from_contact_mapper_tables():
    expected = set(_DISTINCT_VERB_TABLE) | set(_JOIN_FAMILY_VERBS)
    assert set(clf._CLOSED_CHOICE_SET) == expected
    assert len(clf._CLOSED_CHOICE_SET) == len(expected)  # no duplicates


def test_closed_choice_set_derivation_picks_up_a_hypothetical_new_verb():
    # Proves the derivation is genuinely computed, not a frozen snapshot:
    # re-running the SAME derivation function against a synthetic copy of
    # the tables with an extra verb added must include that verb.
    import agent.interpretive.contact_llm_fallback as clf_module

    fake_distinct = dict(_DISTINCT_VERB_TABLE)
    fake_distinct["obliterates"] = "cuts"

    original_distinct = clf_module._DISTINCT_VERB_TABLE
    try:
        clf_module._DISTINCT_VERB_TABLE = fake_distinct
        recomputed = clf_module._derive_closed_choice_set()
        assert "obliterates" in recomputed
    finally:
        clf_module._DISTINCT_VERB_TABLE = original_distinct


def test_every_choice_set_verb_has_a_gloss_and_no_stale_glosses():
    for verb in clf._CLOSED_CHOICE_SET:
        assert verb in clf._VERB_GLOSSES, f"{verb!r} missing a gloss"
        assert isinstance(clf._VERB_GLOSSES[verb], str) and clf._VERB_GLOSSES[verb].strip()
    for verb in clf._VERB_GLOSSES:
        assert verb in clf._CLOSED_CHOICE_SET, f"{verb!r} is a stale gloss"


# ─── Prompt content sanity (not full-string snapshot -- structural checks) ─


def test_system_prompt_contains_every_choice_set_verb_and_its_gloss():
    prompt = clf._build_system_prompt()
    for verb in clf._CLOSED_CHOICE_SET:
        assert f'"{verb}"' in prompt
        assert clf._VERB_GLOSSES[verb] in prompt
    assert "unclear" in prompt.lower()
    assert "resolutions" in prompt


def test_user_prompt_lists_each_contact_verb_numbered():
    contacts = [_contact("fuses"), _contact("severs")]
    prompt = clf._build_user_prompt(contacts)
    assert '1. "fuses"' in prompt
    assert '2. "severs"' in prompt
