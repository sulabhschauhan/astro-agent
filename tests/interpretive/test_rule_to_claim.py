"""
tests/interpretive/test_rule_to_claim.py
Tests for agent/interpretive/rule_to_claim.py -- resolve_chunk_id() and
claims_from_rules(), plus a real call into claim_voicing.voice_claims()
proving the bridged Claim is accepted unchanged.

Fake OpenAI client classes are TRANSPLANTED from
tests/interpretive/test_claim_voicing.py (same shapes/lineage those
tests themselves transplanted from test_palm_reading.py) -- cited, not
reinvented, since voice_claims' `client` seam takes the identical
client.chat.completions.create(...) surface.
"""

from __future__ import annotations

from dataclasses import replace

import pytest

from agent.interpretive.claim_voicing import voice_claims
from agent.interpretive.palm_rules_table import Antecedent, PalmRule, load_rules
from agent.interpretive.rule_to_claim import claims_from_rules, resolve_chunk_id

RULES = load_rules()
BY_ID = {r.rule_id: r for r in RULES}


# ─── Fake OpenAI client -- transplanted from test_claim_voicing.py ───────


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
    def __init__(self, *, content: str | None = None, exception: Exception | None = None):
        self.completions = _FakeCompletions(content=content, exception=exception)
        self.chat = type("_FakeChat", (), {"completions": self.completions})()


# ─── resolve_chunk_id ─────────────────────────────────────────────────────


def test_resolve_chunk_id_hl006_page_160_real_corpus_format():
    chunk_id = resolve_chunk_id(160)
    assert chunk_id == "cheiroslanguageo00chei_1_p160_c0"


def test_resolve_chunk_id_fails_closed_on_unresolvable_page():
    assert resolve_chunk_id(999999) is None


# ─── claims_from_rules: fail-closed drop + stable ordering ───────────────


def test_unresolvable_page_rule_is_dropped_not_crashed():
    bogus = replace(BY_ID["HL_006"], rule_id="BOGUS_PAGE", source_page=999999)
    claims, diagnostics = claims_from_rules([bogus])
    assert claims == ()
    assert diagnostics["dropped_rule_ids"] == ["BOGUS_PAGE"]


def test_claim_id_ordering_stable_across_multi_rule_set_no_gaps():
    bogus = replace(BY_ID["HL_006"], rule_id="BOGUS_PAGE", source_page=999999)
    surfaced = [BY_ID["HL_006"], bogus, BY_ID["HL_011"], BY_ID["H_002"]]
    claims, diagnostics = claims_from_rules(surfaced)
    # BOGUS_PAGE drops without consuming a number -- C1,C2,C3, no gap.
    assert [c.claim_id for c in claims] == ["C1", "C2", "C3"]
    assert [diagnostics["citations"][c.claim_id]["rule_id"] for c in claims] == [
        "HL_006", "HL_011", "H_002",
    ]
    assert diagnostics["dropped_rule_ids"] == ["BOGUS_PAGE"]


def test_hl006_claim_object_fields():
    claims, diagnostics = claims_from_rules([BY_ID["HL_006"]])
    assert len(claims) == 1
    claim = claims[0]
    assert claim.claim_id == "C1"
    assert claim.chunk_id == "cheiroslanguageo00chei_1_p160_c0"
    assert claim.claim_text == BY_ID["HL_006"].claim
    assert claim.valence == "supports"
    assert claim.condition_text is None
    assert claim.excluded_from_voice is False
    assert claim.exclusion_reason is None
    # source_quote is NOT on the Claim object at all (see module
    # docstring) -- it lives in the side-channel citations dict instead.
    assert not hasattr(claim, "source_quote")
    assert diagnostics["citations"]["C1"]["source_quote"] == BY_ID["HL_006"].source_quote


# ─── voice_claims() accepts the bridged Claim unchanged ──────────────────


def test_hl006_claim_accepted_by_voice_claims_without_modifying_it():
    claims, _ = claims_from_rules([BY_ID["HL_006"]])
    good_draft = (
        "When your heart line lies high and the space narrows because "
        "the head line sits close, the head takes command of the "
        "affections, giving a hard, cold, envious nature.[C1]"
    )
    client = _FakeClient(content=good_draft)
    result = voice_claims(claims, texts_by_feature={}, client=client)
    assert result.validation_failures == ()
    assert result.reading_text_tagged != ""
    assert "[C1]" in result.reading_text_tagged
