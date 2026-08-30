"""
tests/interpretive/test_claim_extraction.py
S69 F-H P2 -- test suite for agent/interpretive/claim_extraction.py.

Fake OpenAI client classes (_FakeMessage/_FakeChoice/_FakeResponse/
_FakeCompletions/_FakeClient) are TRANSPLANTED from
tests/interpretive/test_palm_reading.py (same shapes, same
responses=[(content, exception), ...] call-order-indexed convention for
first-attempt-vs-retry tests) -- cited, not reinvented, since
extract_claims' `client` seam takes the identical
client.chat.completions.create(...) surface generate_palm_reading's does.
"""

from __future__ import annotations

import dataclasses
import json

import pytest

from agent.interpretive.claim_extraction import (
    CitationByChunk,
    CitationByRule,
    Claim,
    ExtractionResult,
    _is_two_sided_definitional,
    extract_claims,
)

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
    (content, exception) tuples consumed in call order -- lets a single
    fake answer the first attempt and the retry attempt differently. Past
    the end of `responses`, the LAST entry is reused (clamped index) --
    tests proving "never a 3rd call" must assert `len(.calls)`
    explicitly, not rely on this clamping to crash."""

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


# ─── Fixture builders ────────────────────────────────────────────────────


def _chunk(chunk_id: str, text: str) -> dict:
    """Minimal gated-chunk dict -- extract_claims only reads chunk_id/text,
    same shape palm_reading._apply_support_gate's chunk dicts carry (extra
    keys like score/page_ref are simply ignored, not needed here)."""
    return {"chunk_id": chunk_id, "text": text}


def _raw_claim(
    claim_id: str = "C1",
    chunk_id: str = "p1_c0",
    claim_text: str = "x",
    valence: str = "supports",
    condition_text: str | None = None,
    observation_basis: str = "obs",
) -> dict:
    return {
        "claim_id": claim_id,
        "chunk_id": chunk_id,
        "claim_text": claim_text,
        "valence": valence,
        "condition_text": condition_text,
        "observation_basis": observation_basis,
    }


def _response(feature: str, claims: list[dict]) -> str:
    return json.dumps({"feature": feature, "claims": claims})


# ─── E-3 fixture: hand-computed content-word overlap ────────────────────
# Chunk text content words (8, none in claim_extraction._STOPWORDS):
# alpha, bravo, charlie, delta, echo, foxtrot, golf, hotel.
_E3_CHUNK_TEXT = "Alpha bravo charlie delta echo foxtrot golf hotel."

# PASS claim: content words {alpha, bravo, charlie, xray, yankee} (5).
# shared with chunk = {alpha, bravo, charlie} = 3.
# overlap = shared / min(len(claim_words), len(chunk_words)) = 3 / min(5, 8) = 3/5 = 0.60
# -- above the 0.40 floor.
_E3_CLAIM_TEXT_PASS = "Alpha bravo charlie xray yankee."

# FAIL claim: content words {alpha, xray, yankee, zulu, whiskey} (5).
# shared with chunk = {alpha} = 1.
# overlap = 1 / min(5, 8) = 1/5 = 0.20 -- below the 0.40 floor.
_E3_CLAIM_TEXT_FAIL = "Alpha xray yankee zulu whiskey."

# E2F step 2: second chunk/claim pair, same 8-content-word template as
# above but distinct words, for the partial-failure retry-pool-exclusion
# test below -- needs a SECOND gated chunk with text that never appears
# in the first chunk's text, so the test can assert the excluded
# chunk's text is genuinely absent from the retry prompt (not just
# coincidentally absent because both chunks share vocabulary).
# Chunk text content words (8): india, juliet, kilo, lima, mike,
# november, oscar, papa.
_E3_CHUNK_TEXT_2 = "India juliet kilo lima mike november oscar papa."

# PASS claim: content words {india, juliet, kilo, quebec, romeo} (5).
# shared with chunk_2 = {india, juliet, kilo} = 3.
# overlap = 3 / min(5, 8) = 3/5 = 0.60 -- above the 0.40 floor.
_E3_CLAIM_TEXT_PASS_2 = "India juliet kilo quebec romeo."


# ─── Happy path + E-2 duplicate-id re-key proof ─────────────────────────


def test_happy_path_two_features_claims_rekeyed_and_diagnostics_populated():
    gated_results = {
        "life line": [_chunk("p1_c0", "A long deep life line without breaks promises long life and vitality.")],
        "thumb": [_chunk("p2_c0", "A medium thumb set at a wide angle shows balance of will and logic.")],
    }
    texts_by_feature = {
        "life line": "Present, deep, long, no breaks visible.",
        "thumb": "Medium size, wide angle.",
    }
    # Both features' raw responses reuse claim_id "C1" -- proves
    # extract_claims re-keys with its own module-owned counter across the
    # WHOLE inventory rather than trusting or deduping the model's ids.
    resp_life = _response("life line", [_raw_claim(
        claim_id="C1", chunk_id="p1_c0",
        claim_text="A long deep life line without breaks promises long life and vitality.",
        valence="supports", observation_basis="deep, long, no breaks",
    )])
    resp_thumb = _response("thumb", [_raw_claim(
        claim_id="C1", chunk_id="p2_c0",
        claim_text="A medium thumb set at a wide angle shows balance of will and logic.",
        valence="supports", observation_basis="medium size, wide angle",
    )])
    client = _FakeClient(responses=[(resp_life, None), (resp_thumb, None)])

    result = extract_claims(gated_results, texts_by_feature, client=client)

    assert isinstance(result, ExtractionResult)
    assert len(result.claims) == 2
    assert result.failed_features == ()

    ids = [c.claim_id for c in result.claims]
    assert ids == ["C1", "C2"]
    assert len({c.claim_id for c in result.claims}) == 2

    life_claim, thumb_claim = result.claims
    assert isinstance(life_claim, Claim)
    assert life_claim.feature == "life line"
    assert life_claim.chunk_id == "p1_c0"
    assert life_claim.excluded_from_voice is False
    assert life_claim.exclusion_reason is None
    assert thumb_claim.feature == "thumb"
    assert thumb_claim.chunk_id == "p2_c0"

    diag = result.diagnostics["features"]
    assert diag["life line"]["call_count"] == 1
    assert diag["life line"]["retry_used"] is False
    assert diag["life line"]["status"] == "ok"
    assert diag["life line"]["claim_count"] == 1
    assert len(diag["life line"]["overlap_scores"]) == 1
    assert diag["thumb"]["status"] == "ok"
    assert result.diagnostics["exclusion_ledger"] == []


# ─── E-1: out-of-set chunk_id ────────────────────────────────────────────


def test_e1_illegal_chunk_id_retry_fed_failure_text_persistent_failure():
    # A second, always-succeeding feature ("thumb") rides along so this
    # single-feature persistent failure does NOT trip the separate
    # "ALL attempted features failed -> RuntimeError" path (that path has
    # its own dedicated test below) -- isolates E-1's retry/fail-closed
    # behavior on "life line" alone.
    gated_results = {
        "life line": [_chunk("p1_c0", "A long deep life line without breaks promises long life and vitality.")],
        "thumb": [_chunk("p2_c0", "y")],
    }
    texts_by_feature = {"life line": "deep, long, no breaks", "thumb": "obs"}
    # Cites a chunk_id NOT in this feature's own gated set on BOTH tries.
    bad_resp = _response("life line", [_raw_claim(chunk_id="not_a_real_chunk", claim_text="x", valence="supports")])
    thumb_resp = _response("thumb", [_raw_claim(chunk_id="p2_c0", claim_text="y", valence="supports")])
    client = _FakeClient(responses=[(bad_resp, None), (bad_resp, None), (thumb_resp, None)])

    result = extract_claims(gated_results, texts_by_feature, client=client)

    assert result.failed_features == ("life line",)
    assert [c.feature for c in result.claims] == ["thumb"]

    retry_messages = client.completions.calls[1]["messages"]
    correction = retry_messages[-1]["content"]
    assert "Your extraction failed these checks" in correction
    assert "not_a_real_chunk" in correction
    assert "not in this feature's own gated set" in correction

    diag = result.diagnostics["features"]["life line"]
    assert diag["retry_used"] is True
    assert diag["call_count"] == 2
    assert diag["status"] == "failed"


# ─── E-2: bad valence, missing field, duplicate ids (re-key already ─────
# proven above; these isolate the two other E-2 failure shapes) ──────────


def test_e2_invalid_valence_triggers_retry_then_recovers():
    gated_results = {"life line": [_chunk("p1_c0", "A long deep life line without breaks promises long life and vitality.")]}
    texts_by_feature = {"life line": "deep, long, no breaks"}
    bad_resp = _response("life line", [_raw_claim(
        chunk_id="p1_c0",
        claim_text="A long deep life line without breaks promises long life and vitality.",
        valence="maybe",
    )])
    good_resp = _response("life line", [_raw_claim(
        chunk_id="p1_c0",
        claim_text="A long deep life line without breaks promises long life and vitality.",
        valence="supports",
    )])
    client = _FakeClient(responses=[(bad_resp, None), (good_resp, None)])

    result = extract_claims(gated_results, texts_by_feature, client=client)

    assert len(result.claims) == 1
    assert result.failed_features == ()
    retry_messages = client.completions.calls[1]["messages"]
    assert "invalid valence" in retry_messages[-1]["content"]
    diag = result.diagnostics["features"]["life line"]
    assert diag["retry_used"] is True
    assert diag["call_count"] == 2
    assert diag["status"] == "ok"


def test_e2_missing_required_field_triggers_retry_persistent_failure():
    # "thumb" rides along, always-succeeding, so this single-feature
    # persistent failure doesn't trip the all-fail RuntimeError path.
    gated_results = {
        "life line": [_chunk("p1_c0", "some chunk text")],
        "thumb": [_chunk("p2_c0", "y")],
    }
    texts_by_feature = {"life line": "obs", "thumb": "obs"}
    # condition_text and observation_basis are both absent.
    incomplete_claim = {"claim_id": "C1", "chunk_id": "p1_c0", "claim_text": "x", "valence": "supports"}
    bad_resp = json.dumps({"feature": "life line", "claims": [incomplete_claim]})
    thumb_resp = _response("thumb", [_raw_claim(chunk_id="p2_c0", claim_text="y", valence="supports")])
    client = _FakeClient(responses=[(bad_resp, None), (bad_resp, None), (thumb_resp, None)])

    result = extract_claims(gated_results, texts_by_feature, client=client)

    assert result.failed_features == ("life line",)
    retry_messages = client.completions.calls[1]["messages"]
    assert "missing keys" in retry_messages[-1]["content"]
    assert "condition_text" in retry_messages[-1]["content"]
    assert "observation_basis" in retry_messages[-1]["content"]


# ─── E-3: paraphrase overlap floor ───────────────────────────────────────


def test_e3_overlap_below_floor_skips_retry_when_no_viable_chunks():
    """Attempt 1's only chunk fails E-3 overlap; the retry pool would be
    empty, so retry is skipped entirely. The feature still lands in
    failed_features (fail-closed preserved), diagnostics reflect the
    no-viable-retry path, and only the initial call was made."""
    # "thumb" rides along, always-succeeding, so this single-feature
    # persistent failure doesn't trip the all-fail RuntimeError path.
    gated_results = {
        "life line": [_chunk("p1_c0", _E3_CHUNK_TEXT)],
        "thumb": [_chunk("p2_c0", "y")],
    }
    texts_by_feature = {"life line": "obs", "thumb": "obs"}
    bad_resp = _response("life line", [_raw_claim(chunk_id="p1_c0", claim_text=_E3_CLAIM_TEXT_FAIL, valence="supports")])
    thumb_resp = _response("thumb", [_raw_claim(chunk_id="p2_c0", claim_text="y", valence="supports")])
    # Only ONE response for "life line" -- under E2F step 1's new logic,
    # its single chunk fails E-3 on attempt 1, exhausts the retry pool,
    # and the retry is skipped entirely, so no second "life line" call is
    # ever made for a second bad_resp to answer.
    client = _FakeClient(responses=[(bad_resp, None), (thumb_resp, None)])

    result = extract_claims(gated_results, texts_by_feature, client=client)

    assert result.failed_features == ("life line",)

    # Exactly 2 calls total: life line's failed attempt 1, thumb's
    # successful (only) attempt -- proves no retry call was made for
    # life line.
    assert len(client.completions.calls) == 2
    call_2_messages = client.completions.calls[1]["messages"]
    call_2_text = " ".join(m["content"] for m in call_2_messages)
    assert "thumb" in call_2_text
    assert "overlap 0.20 below floor 0.4" not in call_2_text

    diag = result.diagnostics["features"]["life line"]
    assert diag["final_outcome"] == "failed_first_no_viable_retry"
    assert diag["attempt_2_status"] == "skipped_no_viable_chunks"
    assert diag["retry_used"] is False
    assert diag["first_attempt_failures"]
    assert "below floor" in diag["first_attempt_failures"][0]


def test_e3_overlap_at_or_above_floor_passes():
    gated_results = {"life line": [_chunk("p1_c0", _E3_CHUNK_TEXT)]}
    texts_by_feature = {"life line": "obs"}
    good_resp = _response("life line", [_raw_claim(chunk_id="p1_c0", claim_text=_E3_CLAIM_TEXT_PASS, valence="supports")])
    client = _FakeClient(content=good_resp)

    result = extract_claims(gated_results, texts_by_feature, client=client)

    assert len(result.claims) == 1
    assert result.claims[0].claim_text == _E3_CLAIM_TEXT_PASS
    assert result.failed_features == ()
    assert len(client.completions.calls) == 1
    overlap_recorded = result.diagnostics["features"]["life line"]["overlap_scores"][0]["overlap"]
    assert overlap_recorded == 0.6


def test_e3_partial_failure_excludes_failed_chunk_from_retry_pool():
    """Attempt 1 fails E-3 on one of two gated chunks; the retry's turn 1
    preserves the full original chunk list (matching what attempt 1
    saw), and the turn 3 correction instruction names the failed chunk
    explicitly and forbids re-citing it. Retry cites the remaining
    chunk and validates -- final_outcome == "success_retry"."""
    # "thumb" rides along, always-succeeding, so this doesn't trip the
    # all-fail RuntimeError path.
    gated_results = {
        "life line": [_chunk("p1_c0", _E3_CHUNK_TEXT), _chunk("p2_c0", _E3_CHUNK_TEXT_2)],
        "thumb": [_chunk("p3_c0", "y")],
    }
    texts_by_feature = {"life line": "obs", "thumb": "obs"}
    bad_resp = _response("life line", [_raw_claim(chunk_id="p1_c0", claim_text=_E3_CLAIM_TEXT_FAIL, valence="supports")])
    retry_resp = _response("life line", [_raw_claim(chunk_id="p2_c0", claim_text=_E3_CLAIM_TEXT_PASS_2, valence="supports")])
    thumb_resp = _response("thumb", [_raw_claim(chunk_id="p3_c0", claim_text="y", valence="supports")])
    client = _FakeClient(responses=[(bad_resp, None), (retry_resp, None), (thumb_resp, None)])

    result = extract_claims(gated_results, texts_by_feature, client=client)

    assert result.failed_features == ()
    assert len(client.completions.calls) == 3

    retry_messages = client.completions.calls[1]["messages"]
    # Turn 1 (E2F step 3a): the retry's own first user message must
    # match what attempt 1 actually saw -- BOTH chunks' text present,
    # never filtered. Filtering turn 1 (step 1's original mechanism) is
    # what caused the 2026-07-29 dogfood incoherent-history regression.
    retry_chunk_presentation = retry_messages[1]["content"]
    assert "p2_c0" in retry_chunk_presentation
    assert _E3_CHUNK_TEXT_2 in retry_chunk_presentation
    assert _E3_CHUNK_TEXT in retry_chunk_presentation

    # Turn 3 (E2F step 3a): retry-pool discipline is now enforced ONLY
    # via the correction instruction, which names the failed chunk_id
    # explicitly and forbids re-citing it -- not by hiding it from turn 1.
    correction_content = retry_messages[-1]["content"]
    assert "must NOT be cited on this retry" in correction_content
    assert "'p1_c0'" in correction_content
    assert "Same chunks, same feature." not in correction_content

    diag = result.diagnostics["features"]["life line"]
    assert diag["final_outcome"] == "success_retry"
    assert diag["attempt_1_status"] == "validation_failed"
    assert diag["attempt_2_status"] == "validated"
    assert diag["retry_used"] is True


def test_non_e3_failure_leaves_retry_pool_intact():
    """Attempt 1 fails E-2 (missing required keys), NOT E-3 -- no
    chunk_id is identifiable from that failure string, so the retry
    pool is left completely unchanged (both original chunks still
    offered) and the OLD "Same chunks, same feature." wording is used,
    not the new exclusion wording. Pins that E2F step 1's pool-filtering
    is genuinely E-3-specific, not a blanket behavior change for every
    retry."""
    p1_text = "A long deep life line without breaks promises long life and vitality."
    p2_text = "A strong deep head line without breaks promises great intellect and clarity."
    gated_results = {
        "life line": [_chunk("p1_c0", p1_text), _chunk("p2_c0", p2_text)],
        "thumb": [_chunk("p3_c0", "y")],
    }
    texts_by_feature = {"life line": "obs", "thumb": "obs"}
    # condition_text and observation_basis are both absent -- E-2
    # missing-keys failure, same shape as
    # test_e2_missing_required_field_triggers_retry_persistent_failure.
    incomplete_claim = {"claim_id": "C1", "chunk_id": "p1_c0", "claim_text": p1_text, "valence": "supports"}
    bad_resp = json.dumps({"feature": "life line", "claims": [incomplete_claim]})
    retry_resp = _response("life line", [_raw_claim(chunk_id="p1_c0", claim_text=p1_text, valence="supports")])
    thumb_resp = _response("thumb", [_raw_claim(chunk_id="p3_c0", claim_text="y", valence="supports")])
    client = _FakeClient(responses=[(bad_resp, None), (retry_resp, None), (thumb_resp, None)])

    result = extract_claims(gated_results, texts_by_feature, client=client)

    assert result.failed_features == ()
    assert len(client.completions.calls) == 3

    retry_messages = client.completions.calls[1]["messages"]
    retry_chunk_presentation = retry_messages[1]["content"]
    assert p1_text in retry_chunk_presentation
    assert p2_text in retry_chunk_presentation

    correction_content = retry_messages[-1]["content"]
    assert "Same chunks, same feature." in correction_content
    assert "Chunks that failed the overlap check on attempt 1 have been removed" not in correction_content

    diag = result.diagnostics["features"]["life line"]
    assert diag["final_outcome"] == "success_retry"
    assert diag["attempt_1_status"] == "validation_failed"
    assert diag["attempt_2_status"] == "validated"


# ─── E-4: conditional fail-closed / corrective retained ─────────────────


def test_e4_conditional_excluded_unless_condition_text_matches_confirmed_observation():
    # claim_text == chunk_text (overlap forced to 1.0, trivially above the
    # E-3 floor) so this test isolates E-4 behavior only.
    chunk_text = "If the fate line rises from the line of life, success is won by personal merit."
    gated_results = {"fate line": [_chunk("p163_c1", chunk_text)]}

    # (a) condition_text IS a substring of the feature's confirmed text -> not excluded.
    texts_matched = {"fate line": "The line rises from the line of life and is faint."}
    resp_matched = _response("fate line", [_raw_claim(
        chunk_id="p163_c1", claim_text=chunk_text, valence="conditional",
        condition_text="rises from the line of life",
    )])
    result_matched = extract_claims(gated_results, texts_matched, client=_FakeClient(content=resp_matched))

    assert len(result_matched.claims) == 1
    assert result_matched.claims[0].excluded_from_voice is False
    assert result_matched.claims[0].exclusion_reason is None
    assert result_matched.diagnostics["exclusion_ledger"] == []

    # (b) condition_text is NOT a substring ("barely visible" never states
    # where the line rises from) -> excluded.
    texts_unmatched = {"fate line": "Barely visible."}
    resp_unmatched = _response("fate line", [_raw_claim(
        chunk_id="p163_c1", claim_text=chunk_text, valence="conditional",
        condition_text="rises from the line of life",
    )])
    result_unmatched = extract_claims(gated_results, texts_unmatched, client=_FakeClient(content=resp_unmatched))

    assert len(result_unmatched.claims) == 1
    claim = result_unmatched.claims[0]
    assert claim.excluded_from_voice is True
    assert claim.exclusion_reason == "precondition unverified"
    ledger = result_unmatched.diagnostics["exclusion_ledger"]
    assert len(ledger) == 1
    assert ledger[0]["claim_id"] == claim.claim_id
    assert ledger[0]["feature"] == "fate line"


def test_e4_corrective_claim_retained_not_excluded():
    chunk_text = "The statement that fingers must be longer than the palm is erroneous and misleading."
    gated_results = {"fingers": [_chunk("p98_c1", chunk_text)]}
    texts_by_feature = {"fingers": "Fingers are long relative to the palm."}
    resp = _response("fingers", [_raw_claim(
        chunk_id="p98_c1", claim_text=chunk_text, valence="corrective", condition_text=None,
    )])
    client = _FakeClient(content=resp)

    result = extract_claims(gated_results, texts_by_feature, client=client)

    assert len(result.claims) == 1
    claim = result.claims[0]
    assert claim.valence == "corrective"
    assert claim.excluded_from_voice is False
    assert claim.exclusion_reason is None
    assert result.diagnostics["exclusion_ledger"] == []


# ─── E-5: disjunctive-taxonomy fail-closed (S71 head-line valence bug) ───
# Real claim_text strings, sourced verbatim from diagnostics/dogfood_capture.md.


@pytest.mark.parametrize(
    "claim_text,expected_signal",
    [
        pytest.param(
            "The line of head relates principally to the mentality of the "
            "subject, including intellectual strength or weakness and the "
            "direction and quality of talent.",
            "S1:antonym-pair",
            id="p145_c0_strength_or_weakness",
        ),
        pytest.param(
            "The line of head divides the hand into two parts, representing "
            "mind and material.",
            "S2:definitional",
            id="bare_taxonomy_divides_the_hand",
        ),
    ],
)
def test_e5_flags_disjunctive_taxonomy(claim_text, expected_signal):
    signal = _is_two_sided_definitional(claim_text)
    assert signal is not None
    assert signal == expected_signal


@pytest.mark.parametrize(
    "claim_text",
    [
        pytest.param(
            "A long, deep, and narrow line of life without irregularities "
            "promises long life, good health, and vitality.",
            id="life_line_quality_qualifiers",
        ),
        pytest.param(
            "When the line of life sweeps far out into the hand, it is a "
            "sign of good physical strength and long life.",
            id="life_line_sweeps_quality_word",
        ),
        pytest.param(
            "A well-developed Mount of Venus indicates strong and robust health.",
            id="mount_of_venus_no_definitional_predicate",
        ),
        pytest.param(
            "A well-formed thumb that is not too close to the side or at "
            "right angles to the palm indicates a nature that is independent.",
            id="thumb_no_line_or_mount_subject_a",
        ),
        pytest.param(
            "A well-formed thumb that is not too close to the palm indicates "
            "independence of spirit and strength of character.",
            id="thumb_no_line_or_mount_subject_b",
        ),
        pytest.param(
            "The statement that in every case the fingers must be longer "
            "than the palm is erroneous and misleading.",
            id="fingers_no_subject_no_antonym_pair",
        ),
    ],
)
def test_e5_keeps_genuine_one_sided_claims(claim_text):
    assert _is_two_sided_definitional(claim_text) is None


def test_e5_integration_p145_head_line_claim_excluded_via_apply_e4():
    # Real p145_c0 doctrine, valence="supports", condition_text=None -- E-4
    # never touches this (not conditional, no condition_text); E-5 must
    # catch it on the S1 antonym-pair signal.
    chunk_text = (
        "The line of head relates principally to the mentality of the "
        "subject, including intellectual strength or weakness and the "
        "direction and quality of talent."
    )
    gated_results = {"head line": [_chunk("p145_c0", chunk_text)]}
    texts_by_feature = {"head line": "A long, straight head line."}
    resp = _response("head line", [_raw_claim(
        chunk_id="p145_c0", claim_text=chunk_text, valence="supports", condition_text=None,
    )])
    client = _FakeClient(content=resp)

    result = extract_claims(gated_results, texts_by_feature, client=client)

    assert len(result.claims) == 1
    claim = result.claims[0]
    assert claim.excluded_from_voice is True
    assert claim.exclusion_reason.startswith("disjunctive-taxonomy (S71)")
    ledger = result.diagnostics["exclusion_ledger"]
    assert len(ledger) == 1
    assert ledger[0]["claim_id"] == claim.claim_id
    assert ledger[0]["feature"] == "head line"


# ─── Retry cap ───────────────────────────────────────────────────────────


def test_retry_cap_exactly_two_calls_never_three():
    # "thumb" rides along, always-succeeding, so this single-feature
    # persistent failure doesn't trip the all-fail RuntimeError path.
    gated_results = {
        "life line": [_chunk("p1_c0", "some chunk text")],
        "thumb": [_chunk("p2_c0", "y")],
    }
    texts_by_feature = {"life line": "obs", "thumb": "obs"}
    bad_resp = _response("life line", [_raw_claim(chunk_id="nonexistent", claim_text="x", valence="supports")])
    thumb_resp = _response("thumb", [_raw_claim(chunk_id="p2_c0", claim_text="y", valence="supports")])
    # Only 2 responses provided for "life line" -- if extract_claims ever
    # made a 3rd call for it, _FakeCompletions would silently reuse the
    # 2nd (clamped index), so the real proof here is life line's own
    # call COUNT, not a crash.
    client = _FakeClient(responses=[(bad_resp, None), (bad_resp, None), (thumb_resp, None)])

    result = extract_claims(gated_results, texts_by_feature, client=client)

    assert result.diagnostics["features"]["life line"]["call_count"] == 2
    assert result.failed_features == ("life line",)
    assert [c.feature for c in result.claims] == ["thumb"]


# ─── API exceptions ──────────────────────────────────────────────────────


def test_api_exception_on_first_call_marks_feature_failed_others_succeed_no_raise():
    gated_results = {
        "life line": [_chunk("p1_c0", "A long deep life line without breaks promises long life and vitality.")],
        "thumb": [_chunk("p2_c0", "y")],
    }
    texts_by_feature = {"life line": "deep, long, no breaks", "thumb": "obs"}
    good_resp = _response("life line", [_raw_claim(
        chunk_id="p1_c0",
        claim_text="A long deep life line without breaks promises long life and vitality.",
        valence="supports",
    )])
    client = _FakeClient(responses=[(good_resp, None), (None, RuntimeError("network down"))])

    result = extract_claims(gated_results, texts_by_feature, client=client)

    assert result.failed_features == ("thumb",)
    assert len(result.claims) == 1
    assert result.claims[0].feature == "life line"
    diag = result.diagnostics["features"]["thumb"]
    assert diag["status"] == "failed"
    assert "claim_extraction: API call failed for feature 'thumb'" in diag["error"]
    # No retry attempted -- an API exception on the FIRST call skips retry
    # entirely (only a validation failure on a SUCCESSFUL response triggers
    # the retry path).
    assert diag["call_count"] == 1
    assert diag["retry_used"] is False


def test_api_exception_on_retry_call_marks_feature_failed_no_raise():
    gated_results = {
        "life line": [_chunk("p1_c0", "A long deep life line without breaks promises long life and vitality.")],
        "thumb": [_chunk("p2_c0", "y")],
    }
    texts_by_feature = {"life line": "deep, long, no breaks", "thumb": "obs"}
    good_resp = _response("life line", [_raw_claim(
        chunk_id="p1_c0",
        claim_text="A long deep life line without breaks promises long life and vitality.",
        valence="supports",
    )])
    bad_resp = _response("thumb", [_raw_claim(chunk_id="nonexistent", claim_text="x", valence="supports")])
    # thumb: first call returns an E-1-illegal response (triggers retry),
    # then the RETRY call itself raises -- a different failure point than
    # a first-call exception.
    client = _FakeClient(responses=[(good_resp, None), (bad_resp, None), (None, RuntimeError("timeout"))])

    result = extract_claims(gated_results, texts_by_feature, client=client)

    assert result.failed_features == ("thumb",)
    diag = result.diagnostics["features"]["thumb"]
    assert diag["status"] == "failed"
    assert diag["retry_used"] is True
    assert diag["call_count"] == 2
    assert "claim_extraction: API retry failed for feature 'thumb'" in diag["error"]
    assert "first_attempt_failures" in diag


def test_all_features_fail_raises_runtime_error():
    gated_results = {
        "life line": [_chunk("p1_c0", "text")],
        "thumb": [_chunk("p2_c0", "text")],
    }
    texts_by_feature = {"life line": "obs", "thumb": "obs"}
    # Every call (both features x both attempts) returns the same
    # malformed content -- both features exhaust their retry and fail.
    client = _FakeClient(content="{not valid json")

    with pytest.raises(RuntimeError, match="all 2 attempted feature"):
        extract_claims(gated_results, texts_by_feature, client=client)

    assert len(client.completions.calls) == 4


# ─── Empty claims list / empty gated sets ───────────────────────────────


def test_empty_claims_list_is_legitimate_not_a_failure():
    gated_results = {"fate line": [_chunk("p163_c1", "text")]}
    texts_by_feature = {"fate line": "Barely visible."}
    resp = _response("fate line", [])  # model legitimately declines to extract anything
    client = _FakeClient(content=resp)

    result = extract_claims(gated_results, texts_by_feature, client=client)

    assert result.claims == ()
    assert result.failed_features == ()
    diag = result.diagnostics["features"]["fate line"]
    assert diag["status"] == "ok"
    assert diag["claim_count"] == 0
    assert len(client.completions.calls) == 1  # no retry -- an empty list is a valid outcome


def test_feature_with_empty_gated_chunks_is_skipped_entirely():
    gated_results = {"life line": [_chunk("p1_c0", "text")], "heart line": []}
    texts_by_feature = {"life line": "obs"}
    resp = _response("life line", [_raw_claim(chunk_id="p1_c0", claim_text="text", valence="supports")])
    client = _FakeClient(content=resp)

    result = extract_claims(gated_results, texts_by_feature, client=client)

    assert "heart line" not in result.diagnostics["features"]
    assert "heart line" not in result.failed_features
    assert len(client.completions.calls) == 1


def test_all_gated_empty_returns_empty_result_no_raise():
    gated_results = {"life line": [], "thumb": []}
    texts_by_feature: dict[str, str] = {}
    # Belt-and-suspenders proof (same convention as test_palm_reading.py's
    # _explosive_client): the LLM must never fire when nothing is gated.
    client = _FakeClient(exception=AssertionError("must not call the LLM when nothing is gated"))

    result = extract_claims(gated_results, texts_by_feature, client=client)

    assert result.claims == ()
    assert result.failed_features == ()
    assert result.diagnostics == {"features": {}, "exclusion_ledger": []}
    assert client.completions.calls == []


# ─── S119 Step 1: citation sum type (additive carrier) ──────────────────
#
# Step 1 adds the CAPABILITY only -- no producer builds a by-rule citation
# and no consumer reads the by-rule branch yet (Step 2 wires it). These
# tests therefore pin (a) that the by-chunk path is byte-for-byte what it
# always was, (b) that the by-rule branch exists and carries what Step 2
# needs, and (c) that a rule's source_quote cannot reach the voicer.


_CLAIM_FIELD_NAMES = (
    "claim_id", "feature", "chunk_id", "claim_text", "valence",
    "condition_text", "observation_basis", "excluded_from_voice",
    "exclusion_reason",
)


def _by_chunk_kwargs(**overrides) -> dict:
    base = dict(
        claim_id="C1",
        feature="head line",
        chunk_id="cheiroslanguageo00chei_1_p145_c0",
        claim_text="A short head line indicates a practical, material nature.",
        valence="supports",
        condition_text=None,
        observation_basis="short and clearly marked",
        excluded_from_voice=False,
        exclusion_reason=None,
    )
    base.update(overrides)
    return base


# --- (1) backward compatibility ------------------------------------------


def test_existing_style_construction_is_a_by_chunk_citation_with_identical_chunk_id():
    """The plain constructor -- what every pre-S119 call site and test
    fixture uses -- still yields a by-chunk claim whose chunk_id is
    unchanged, and whose citation identity IS that same chunk_id."""
    kwargs = _by_chunk_kwargs()
    claim = Claim(**kwargs)

    assert claim.chunk_id == kwargs["chunk_id"]
    assert claim.citation == CitationByChunk(kwargs["chunk_id"])
    assert claim.citation_ref == kwargs["chunk_id"]
    # Every other accessor unchanged.
    for name in _CLAIM_FIELD_NAMES:
        assert getattr(claim, name) == kwargs[name]


def test_by_chunk_classmethod_is_indistinguishable_from_the_plain_constructor():
    kwargs = _by_chunk_kwargs()
    assert Claim.by_chunk(**kwargs) == Claim(**kwargs)
    assert repr(Claim.by_chunk(**kwargs)) == repr(Claim(**kwargs))
    assert Claim.by_chunk(**kwargs).citation == Claim(**kwargs).citation


def test_claim_dataclass_field_set_is_unchanged_by_the_citation_carrier():
    """The carrier is NOT a dataclass field -- __init__/__eq__/__repr__ and
    dataclasses.fields() are all exactly what they were."""
    assert tuple(f.name for f in dataclasses.fields(Claim)) == _CLAIM_FIELD_NAMES
    assert not hasattr(Claim(**_by_chunk_kwargs()), "source_quote")


# --- (2) new capability: by-rule ------------------------------------------


def test_by_rule_carries_rule_id_source_page_and_source_quote():
    claim = Claim.by_rule(
        claim_id="C1",
        feature="head line",
        rule_id="H_005",
        source_page=146,
        source_quote="When the line of head is short ...",
        claim_text="A short head line indicates a practical, material nature.",
        valence="rule_derived",
        condition_text=None,
        observation_basis="head line Length=short",
        excluded_from_voice=False,
        exclusion_reason=None,
    )

    assert claim.citation == CitationByRule("H_005", 146, "When the line of head is short ...")
    assert claim.citation.rule_id == "H_005"
    assert claim.citation.source_page == 146
    assert claim.citation.source_quote == "When the line of head is short ..."
    # chunk_id is None BY DESIGN -- there is no retrieval chunk behind it.
    assert claim.chunk_id is None


def test_by_rule_citation_ref_returns_a_rule_form_without_the_quote():
    """Shape only -- no consumer reads this branch yet. The accessor must
    never render the quote (source_quote containment)."""
    claim = Claim.by_rule(
        claim_id="C1", feature="life line", rule_id="L_012", source_page="p139",
        source_quote="a long line sweeping far out into the hand",
        claim_text="text", valence="rule_derived", condition_text=None,
        observation_basis="life line Length=long", excluded_from_voice=False,
        exclusion_reason=None,
    )

    assert claim.citation_ref == "rule:L_012@pp139"
    assert "sweeping far out" not in claim.citation_ref


def test_claim_with_no_chunk_id_and_no_rule_citation_raises_rather_than_guessing():
    claim = Claim(**_by_chunk_kwargs(chunk_id=None))
    with pytest.raises(ValueError, match="neither a chunk_id nor a rule citation"):
        claim.citation


# --- (3) source_quote never reaches a voicer-facing field ----------------


def test_source_quote_never_reaches_any_voicer_facing_field():
    """claim_voicing reads exactly claim_id/claim_text/valence/
    observation_basis and builds its prompt from those -- a by-rule
    citation's quote must appear in none of them, nor in the built
    prompt."""
    from agent.interpretive.claim_voicing import _build_user_prompt

    quote = "ZZQUOTEZZ the line of head when short denotes a material nature"
    claim = Claim.by_rule(
        claim_id="C1", feature="head line", rule_id="H_005", source_page=146,
        source_quote=quote, claim_text="A short head line indicates practicality.",
        valence="rule_derived", condition_text=None,
        observation_basis="head line Length=short", excluded_from_voice=False,
        exclusion_reason=None,
    )

    for voicer_field in ("claim_id", "claim_text", "valence", "observation_basis"):
        assert quote not in str(getattr(claim, voicer_field))
    assert quote not in _build_user_prompt([claim], {"head line": "short"})
    assert quote not in claim.citation_ref


# --- (4) every enumerated existing construction site still builds --------


def test_every_existing_construction_site_shape_still_builds_a_valid_claim():
    """The four production/test construction shapes enumerated at S119
    Step 1: claim_extraction._apply_e4, rule_to_claim.claims_from_rules,
    tests/interpretive/test_claim_voicing.py's _claim builder, and
    tests/test_app_dogfood_capture.py's inline fixtures. All keyword-only,
    all nine fields, no citation argument."""
    shapes = (
        # claim_extraction._apply_e4 (excluded, E-4 reason)
        _by_chunk_kwargs(
            claim_id="C2", valence="conditional",
            condition_text="fate line rises from the life line",
            excluded_from_voice=True, exclusion_reason="precondition unverified",
        ),
        # rule_to_claim.claims_from_rules
        _by_chunk_kwargs(
            feature="life line", valence="rule_derived",
            observation_basis="life line Length=long",
        ),
        # test_claim_voicing._claim
        _by_chunk_kwargs(chunk_id="c1", claim_text="Claim one text.", observation_basis="deep, long"),
        # test_app_dogfood_capture inline fixture
        _by_chunk_kwargs(
            feature="fate line", chunk_id="cheiroslanguageo00chei_1_p200_c1",
            valence="positive", observation_basis="barely visible",
        ),
    )
    for kwargs in shapes:
        claim = Claim(**kwargs)
        assert isinstance(claim.citation, CitationByChunk)
        assert claim.citation_ref == kwargs["chunk_id"]
