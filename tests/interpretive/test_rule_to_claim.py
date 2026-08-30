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

from agent.interpretive.claim_extraction import CitationByChunk, CitationByRule
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


def test_unresolvable_page_rule_is_no_longer_dropped_it_cites_itself():
    """CHANGED BY S119 STEP 2 (was: test_unresolvable_page_rule_is_
    dropped_not_crashed, which asserted `claims == ()` and
    `dropped_rule_ids == ["BOGUS_PAGE"]`).

    That old expectation IS the defect Step 2 fixes. "Unresolvable page"
    only ever meant "data/chunked_chunks.json has no non-empty chunk on
    that page number" -- a property of the CHUNK corpus, which has
    nothing to do with whether the rule's own quote is genuine. Dropping
    the rule threw away a gate-verified claim (13 of 99 live rules,
    FT_003 among them). A rule now cites itself, so the page number is
    never resolved against anything and cannot fail."""
    bogus = replace(BY_ID["HL_006"], rule_id="BOGUS_PAGE", source_page=999999)
    claims, diagnostics = claims_from_rules([bogus])
    assert len(claims) == 1
    assert diagnostics["dropped_rule_ids"] == []
    citation = claims[0].citation
    assert isinstance(citation, CitationByRule)
    assert citation.rule_id == "BOGUS_PAGE"
    assert citation.source_page == 999999
    assert citation.source_quote == BY_ID["HL_006"].source_quote


def test_claim_id_ordering_stable_across_multi_rule_set_no_gaps():
    """CHANGED BY S119 STEP 2. Was: BOGUS_PAGE dropped without consuming
    a claim_id number, so 4 surfaced rules yielded C1,C2,C3. Now nothing
    drops, so 4 surfaced rules yield C1..C4 -- the contiguity property
    this test actually exists to pin is unchanged and still asserted; only
    the count moved, because the drop it was compensating for is gone."""
    bogus = replace(BY_ID["HL_006"], rule_id="BOGUS_PAGE", source_page=999999)
    surfaced = [BY_ID["HL_006"], bogus, BY_ID["HL_011"], BY_ID["H_002"]]
    claims, diagnostics = claims_from_rules(surfaced)
    assert [c.claim_id for c in claims] == ["C1", "C2", "C3", "C4"]
    assert [diagnostics["citations"][c.claim_id]["rule_id"] for c in claims] == [
        "HL_006", "BOGUS_PAGE", "HL_011", "H_002",
    ]
    assert diagnostics["dropped_rule_ids"] == []


def test_hl006_claim_object_fields():
    claims, diagnostics = claims_from_rules([BY_ID["HL_006"]])
    assert len(claims) == 1
    claim = claims[0]
    assert claim.claim_id == "C1"
    # CHANGED BY S119 STEP 2. Was:
    #   assert claim.chunk_id == "cheiroslanguageo00chei_1_p160_c0"
    # HL_006 is one of the 31 rules whose page DID resolve to a chunk
    # containing its quote, so that assertion was not itself wrong -- but
    # it pinned the re-derivation MECHANISM, which is what Step 2 removes.
    # The claim now carries HL_006's own verified citation directly.
    assert claim.chunk_id is None
    assert claim.citation == CitationByRule(
        "HL_006", BY_ID["HL_006"].source_page, BY_ID["HL_006"].source_quote
    )
    assert claim.citation_ref == f"rule:HL_006@p{BY_ID['HL_006'].source_page}"
    assert claim.claim_text == BY_ID["HL_006"].claim
    assert claim.valence == "supports"
    assert claim.condition_text is None
    assert claim.excluded_from_voice is False
    assert claim.exclusion_reason is None
    # source_quote is NOT on the Claim object at all (see module
    # docstring) -- it lives in the side-channel citations dict instead.
    assert not hasattr(claim, "source_quote")
    assert diagnostics["citations"]["C1"]["source_quote"] == BY_ID["HL_006"].source_quote
    # chunk_id retired to a stable-shape None in the side-channel too.
    assert diagnostics["citations"]["C1"]["chunk_id"] is None
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


# ═══ S119 STEP 2: rule claims cite by-rule, never by re-derived chunk ════


def _gate_verifier():
    """The AUTHORING-TIME citation gate (scripts/gate_rule_citations.py),
    loaded once -- the same page-level corpus + overlap primitive that
    reports NOT_FOUND_ANYWHERE: 0 across every live rule. Returns a
    callable rule_dict -> gate status."""
    import json as _json

    from scripts.gate_rule_citations import (
        DEFAULT_CORPUS_PATH,
        build_full_corpus_text,
        build_page_text_index,
        classify_rule_citation,
        tokens_of,
    )

    corpus = _json.loads(DEFAULT_CORPUS_PATH.read_text(encoding="utf-8"))
    page_text = build_page_text_index(corpus)
    page_token_sets = {p: set(tokens_of(t)) for p, t in page_text.items()}
    full_text = build_full_corpus_text(page_text)
    full_token_set = set(tokens_of(full_text))

    def verify(rule_dict: dict) -> str:
        return classify_rule_citation(
            rule_dict, page_text, page_token_sets, full_text, full_token_set
        )["status"]

    return verify


# ─── (1) THE FIX, MEASURED: 31/99 -> 99/99 ──────────────────────────────


def test_every_live_rule_produces_a_claim_citing_its_own_gate_verified_quote():
    """HARDEST CASE -- the whole rule corpus, not a sample. Re-runs Step 0's
    question (probes/citation_accuracy_audit_S119.py) against the NEW path.

    Step 0 measured the OLD resolve-a-chunk path over these same 99 live
    rules: 31 RESOLVED_CORRECT, 52 RESOLVED_WRONG, 13 DROPPED_NONE,
    3 NO_ANCHOR_ANYWHERE -- 31.3% citation accuracy. Under by-rule
    citation there is nothing left to get wrong: each claim's citation IS
    the rule's own source_page + source_quote, and this test proves every
    one of those quotes independently passes the authoring gate."""
    rules = load_rule_set()
    # 99 -> 89 at S119 Step 5 (10 mount base-meaning rows retired) -> 87 at
    # S119 Defect 2 close (M_015/M_016 retired). This test measures
    # CITATION ACCURACY, which is unaffected by the live set shrinking: it
    # re-verifies whatever rules are live, all of them.
    assert len(rules) == 87, "live rule count moved -- re-baseline this test"

    claims, diagnostics = claims_from_rules(rules)

    # 0 dropped: Defect 1 (13 dropped rules) closed.
    assert len(claims) == len(rules)
    assert diagnostics["dropped_rule_ids"] == []
    assert [c.claim_id for c in claims] == [f"C{i}" for i in range(1, len(rules) + 1)]

    verify = _gate_verifier()
    by_rule_id = {r.rule_id: r for r in rules}
    for claim in claims:
        citation = claim.citation
        assert isinstance(citation, CitationByRule)
        rule = by_rule_id[citation.rule_id]
        # The citation is the rule's OWN provenance, not a re-derivation.
        assert citation.source_page == rule.source_page
        assert citation.source_quote == rule.source_quote
        assert claim.chunk_id is None
        # ...and that provenance is gate-verified, per rule, all 99.
        assert verify(
            {"source_quote": citation.source_quote, "source_page": citation.source_page}
        ) == "CLEAN"


def test_the_fate_offset_rules_no_longer_mis_cite():
    """The +60 page offset between the fate rule file's source_page and the
    corpus page_ref was the single largest RESOLVED_WRONG driver in Step 0.
    It is now IRRELEVANT: nothing maps source_page onto a corpus page to
    pick a chunk, so no offset can mis-target anything."""
    fate = [r for r in load_rule_set() if r.topic_group == "line_fate"]
    assert fate, "no fate rules loaded"
    claims, diagnostics = claims_from_rules(fate)

    assert len(claims) == len(fate)
    assert diagnostics["dropped_rule_ids"] == []
    for claim, rule in zip(claims, fate):
        assert claim.citation == CitationByRule(
            rule.rule_id, rule.source_page, rule.source_quote
        )


# ─── (2) FT_003 end to end: the original live failure ───────────────────


def test_ft003_extreme_good_fortune_survives_to_voicing_citing_by_rule():
    """THE ORIGINAL LIVE FAILURE. FT_003's source_page is 103, which has no
    non-empty chunk in data/chunked_chunks.json -- resolve_chunk_id
    returned None, so the rule fired, produced no claim, and its "extreme
    good fortune" reading was silently lost. It now survives all the way
    into a voiced reading."""
    ft003 = {r.rule_id: r for r in load_rule_set()}["FT_003"]
    # The precondition that used to kill it is still true of the corpus --
    # this rule is not saved by the chunk data changing, but by not
    # consulting it.
    assert resolve_chunk_id(ft003.source_page) is None

    claims, diagnostics = claims_from_rules([ft003])

    assert len(claims) == 1
    assert diagnostics["dropped_rule_ids"] == []
    claim = claims[0]
    assert claim.citation == CitationByRule(
        "FT_003", ft003.source_page, ft003.source_quote
    )
    assert claim.citation_ref == f"rule:FT_003@p{ft003.source_page}"
    assert "extreme good fortune" in claim.claim_text

    # ...and it reaches Stage 2 as a real, citable claim.
    draft = (
        "A fate line rising from the wrist and running straight to the "
        "Mount of Saturn is a sign of extreme good fortune and success.[C1]"
    )
    result = voice_claims(claims, texts_by_feature={}, client=_FakeClient(content=draft))
    assert result.validation_failures == ()
    assert "[C1]" in result.reading_text_tagged


# ─── (5) dropped_rule_ids is a retired, always-empty tripwire ───────────


def test_dropped_rule_ids_is_empty_on_rules_that_previously_dropped():
    """All 13 Step-0 DROPPED_NONE rules in one call. Every one of them used
    to vanish; none does now."""
    rules = load_rule_set()
    previously_dropped = [r for r in rules if resolve_chunk_id(r.source_page) is None]
    assert len(previously_dropped) == 13, "Step-0 drop set moved -- re-baseline"

    claims, diagnostics = claims_from_rules(previously_dropped)

    assert len(claims) == 13
    assert diagnostics["dropped_rule_ids"] == []
    assert {c.citation.rule_id for c in claims} == {r.rule_id for r in previously_dropped}


# ─── (3)/(4) V-2 anchor legality: by-rule accepted, by-chunk unchanged ──


def test_by_rule_anchor_is_out_of_v2_jurisdiction_not_flagged_fabricated():
    """A by-rule citation identity can never be reported as an
    unknown/malformed chunk_id, on an EMPTY legal set -- the strictest
    possible input."""
    from agent.interpretive.palm_reading import _check_anchor_legality

    claim = claims_from_rules([BY_ID["HL_006"]])[0][0]
    text = f"The head takes command of the affections.[{claim.citation_ref}]"
    assert _check_anchor_legality(text, frozenset()) == []


def test_v2_still_kills_a_fabricated_by_chunk_anchor():
    """GUARD INTACT: V-2's real job is unchanged. A chunk-shaped anchor that
    was never gated is still reported."""
    from agent.interpretive.palm_reading import _check_anchor_legality

    legal = frozenset({"cheiroslanguageo00chei_1_p147_c0"})
    failures = _check_anchor_legality(
        "Real doctrine.[cheiroslanguageo00chei_1_p147_c0] "
        "Invented doctrine.[cheiroslanguageo00chei_1_p999_c9]",
        legal,
    )
    assert len(failures) == 1
    assert "cheiroslanguageo00chei_1_p999_c9" in failures[0]
    assert "cheiroslanguageo00chei_1_p147_c0" not in failures[0]


def test_by_chunk_retrieval_claims_are_unchanged_through_e1_and_v2():
    """(4) The retrieval path is untouched by Step 2. E-1 still accepts a
    legal chunk_id and rejects one outside the feature's own gated set, and
    the resulting claims are still by-chunk with their chunk_id intact."""
    import json as _json

    from agent.interpretive.claim_extraction import extract_claims
    from agent.interpretive.palm_reading import _check_anchor_legality

    gated = {
        "head line": [
            {"chunk_id": "bk_p147_c0",
             "text": "A short line of head denotes a material nature."}
        ]
    }
    payload = _json.dumps({
        "feature": "head line",
        "claims": [{
            "claim_id": "C1", "chunk_id": "bk_p147_c0",
            "claim_text": "A short head line denotes a material nature.",
            "valence": "supports", "condition_text": None,
            "observation_basis": "short",
        }],
    })
    result = extract_claims(gated, {"head line": "short"}, client=_FakeClient(content=payload))

    assert len(result.claims) == 1
    claim = result.claims[0]
    assert isinstance(claim.citation, CitationByChunk)
    assert claim.chunk_id == "bk_p147_c0"
    assert claim.citation_ref == "bk_p147_c0"
    # ...and V-2 treats its anchor exactly as before.
    assert _check_anchor_legality("Doctrine.[bk_p147_c0]", frozenset({"bk_p147_c0"})) == []
    assert _check_anchor_legality("Doctrine.[bk_p147_c0]", frozenset()) != []


# ─── (6) source_quote containment, still ────────────────────────────────


def test_source_quote_reaches_no_voicer_facing_field_on_the_by_rule_path():
    """Step 2 puts the quote ON the claim (its CitationByRule). The
    containment guarantee it must not break: claim_voicing reads only
    claim_id/claim_text/valence/observation_basis, and the quote appears in
    none of them nor in the prompt actually sent."""
    from agent.interpretive.claim_voicing import _build_user_prompt

    rules = load_rule_set()
    claims, _ = claims_from_rules(rules)
    for claim in claims:
        quote = claim.citation.source_quote
        assert quote.strip()
        for voicer_field in ("claim_id", "claim_text", "valence", "observation_basis"):
            assert quote not in str(getattr(claim, voicer_field))
        assert quote not in claim.citation_ref

    prompt = _build_user_prompt(list(claims), {})
    for claim in claims:
        assert claim.citation.source_quote not in prompt
