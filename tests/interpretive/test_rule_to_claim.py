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
from agent.interpretive.palm_reading import _FEATURE_REGISTRY
from agent.interpretive.palm_rules_table import Antecedent, PalmRule, load_rule_set, load_rules
from agent.interpretive.rule_to_claim import (
    _assert_topic_groups_mapped,
    _TOPIC_GROUP_TO_FEATURE,
    claims_from_rules,
    resolve_chunk_id,
)

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
    # HL_006's topic_group is "line_heart" -- Claim.feature must be the
    # MAPPED palm_reading._FEATURE_REGISTRY token, not that raw label
    # (this is the bug this task fixes: see _TOPIC_GROUP_TO_FEATURE).
    assert BY_ID["HL_006"].topic_group == "line_heart"
    assert claim.feature == "heart line"
    # topic_group itself survives in the citations side-channel for the
    # suppression audit -- not lost, just no longer on Claim.feature.
    assert diagnostics["citations"]["C1"]["topic_group"] == "line_heart"


# ─── topic_group -> _FEATURE_REGISTRY mapping (this task's own fix) ──────


def test_every_real_topic_group_maps_to_a_registry_feature():
    """HARDEST-ADJACENT CASE: exhaustively scans BOTH live rule files
    (data/palm_rules/*.json via load_rule_set(), not just the single-file
    default load_rules() the rest of this test module uses) and asserts
    every distinct topic_group present is mapped, and every mapped value
    is itself a real palm_reading._FEATURE_REGISTRY token -- proving the
    mapping is exhaustive against the real corpus, not just against the
    hand-picked ids this test module happens to reference elsewhere."""
    real_topic_groups = {r.topic_group for r in load_rule_set()}
    assert real_topic_groups  # sanity: the rule files actually loaded something
    assert real_topic_groups <= _TOPIC_GROUP_TO_FEATURE.keys()
    for topic_group in real_topic_groups:
        assert _TOPIC_GROUP_TO_FEATURE[topic_group] in _FEATURE_REGISTRY


def test_fired_line_head_rule_maps_to_head_line_not_raw_topic_group():
    assert BY_ID["H_002"].topic_group == "line_head"
    claims, _ = claims_from_rules([BY_ID["H_002"]])
    assert len(claims) == 1
    assert claims[0].feature == "head line"
    assert claims[0].feature != "line_head"


def test_unmapped_topic_group_raises_valueerror_naming_the_group():
    """HARDEST CASE: a synthetic rule carrying a topic_group this module
    has never seen must fail loud at the same fail-closed guard the real
    module-load call above uses -- not silently pass an unrecognized
    label through as Claim.feature (the exact defect this task fixes)."""
    bogus = replace(BY_ID["H_002"], rule_id="BOGUS_GROUP", topic_group="line_pinky_toe")
    with pytest.raises(ValueError, match="line_pinky_toe"):
        _assert_topic_groups_mapped([bogus])
    # claims_from_rules' own per-rule lookup fails the same way, not with
    # a bare KeyError -- exercised on the actual call path, not just the
    # module-load guard in isolation.
    with pytest.raises(ValueError, match="line_pinky_toe"):
        claims_from_rules([bogus])


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


# ─── evidence_confidence: weakest-link across antecedents (this task) ────
#
# HL_006's antecedents are (Line of Heart, Position) and (Quadrangle,
# Breadth) -- a real two-feature compound rule, deliberately reused here
# rather than a synthetic one, since it already exercises the
# cross-feature magnitudes lookup this plumbing needs.


def test_evidence_confidence_hardest_case_mixed_confidence_weakest_link():
    """HARDEST CASE: one antecedent's observation is deterministic-grade
    (confidence 1.0), the other is vision-grade and hedged (0.6) -- the
    weakest-link min must pick the SOFTER value, not average or take the
    stronger one."""
    magnitudes = {
        "Line of Heart": {"Position": 1.0},
        "Quadrangle": {"Breadth": 0.6},
    }
    claims, diagnostics = claims_from_rules([BY_ID["HL_006"]], magnitudes=magnitudes)
    assert len(claims) == 1
    assert diagnostics["citations"]["C1"]["evidence_confidence"] == 0.6


def test_evidence_confidence_missing_antecedent_key_excluded_not_crashed():
    """An antecedent whose (feature, attribute) key is absent from
    magnitudes contributes NO confidence value and is silently excluded
    from the min -- not a crash, not treated as 0.0. Here only
    "Quadrangle" is missing entirely, so evidence_confidence must equal
    the sole remaining antecedent's value."""
    magnitudes = {"Line of Heart": {"Position": 0.75}}
    claims, diagnostics = claims_from_rules([BY_ID["HL_006"]], magnitudes=magnitudes)
    assert len(claims) == 1
    assert diagnostics["citations"]["C1"]["evidence_confidence"] == 0.75


def test_evidence_confidence_all_antecedent_keys_missing_yields_none():
    """Every antecedent key absent from magnitudes -> evidence_confidence
    is None, not a crash and not 0.0 -- an empty weakest-link pool is
    "no signal", not "worst possible signal"."""
    magnitudes = {"Some Other Feature": {"Some Attribute": 0.9}}
    claims, diagnostics = claims_from_rules([BY_ID["HL_006"]], magnitudes=magnitudes)
    assert len(claims) == 1
    assert diagnostics["citations"]["C1"]["evidence_confidence"] is None


def test_evidence_confidence_legacy_call_magnitudes_none_key_present_value_none():
    """A caller that doesn't pass magnitudes at all (legacy/default) still
    gets the "evidence_confidence" key in the citation, always None --
    the key's PRESENCE never depends on whether the caller opted in."""
    claims, diagnostics = claims_from_rules([BY_ID["HL_006"]])
    assert len(claims) == 1
    assert "evidence_confidence" in diagnostics["citations"]["C1"]
    assert diagnostics["citations"]["C1"]["evidence_confidence"] is None


def test_evidence_confidence_multi_antecedent_same_feature_hl010():
    """HL_010's two antecedents are BOTH on "Line of Heart"
    (Starting_Point, Continuity) -- proves the lookup is keyed on
    (feature, attribute) pairs, not just feature, since both antecedents
    share a feature but need independent attribute lookups."""
    magnitudes = {"Line of Heart": {"Starting_Point": 0.9, "Continuity": 0.4}}
    claims, diagnostics = claims_from_rules([BY_ID["HL_010"]], magnitudes=magnitudes)
    assert len(claims) == 1
    assert diagnostics["citations"]["C1"]["evidence_confidence"] == 0.4


def test_evidence_confidence_never_placed_on_claim_object():
    """Provenance metadata only -- must never leak onto the Claim
    dataclass itself (same side-channel discipline as source_quote)."""
    magnitudes = {"Line of Heart": {"Position": 1.0}, "Quadrangle": {"Breadth": 0.6}}
    claims, _ = claims_from_rules([BY_ID["HL_006"]], magnitudes=magnitudes)
    assert not hasattr(claims[0], "evidence_confidence")
