"""
tests/interpretive/test_phrase_normalizer.py
Tests for agent/interpretive/phrase_normalizer.py's normalize(). Runs
entirely against real data/palm_phrase_lexicon_v1.json (PN_001: Line of
Life / Curve / sweeping_wide) -- no fake lexicon fixture.

v1.0.1 UPDATE: PN_001.match_any no longer contains "curves around the base
of the thumb" -- removed as anatomy-neutral over-reach (every life line
curves around the thumb base; it does not establish Cheiro's p139
"sweeps far out into the hand" wide-sweep signal). The hardest-case promote
test below now targets an unambiguous wide-sweep phrase instead
("the life line sweeps far out into the palm", a literal match_any hit);
the old thumb-base phrase moved to its own dedicated over-map guard test,
asserting it correctly stays unmapped.

Hardest case first, per project convention: a genuine positive-match
promotion, then the ambiguous-anatomy over-map guard, then the two
must_not_match/bare-miss negatives that prove the guard doesn't
over-promote, then the feature guard, the no-overwrite conflict policy,
and finally the fail-closed missing/corrupt-lexicon paths.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from agent.interpretive.observation_extractor import FeatureObservation, ObservationRecord
from agent.interpretive.phrase_normalizer import normalize

_REAL_LEXICON_PATH = (
    Path(__file__).resolve().parent.parent.parent / "data" / "palm_phrase_lexicon_v1.json"
)


def _record_with_unmapped(feature: str, quality: str, raw_prose: str = "") -> ObservationRecord:
    return ObservationRecord(
        features={
            feature: FeatureObservation(
                tokens={},
                unmapped=[{"quality": quality, "attribute_guess": "Curve"}],
                raw_prose=raw_prose or quality,
            ),
        },
    )


def test_hardest_case_unambiguous_wide_sweep_promotes_to_sweeping_wide():
    """Unambiguous wide-sweep phrasing (a literal "sweeps far out" match_any
    hit, v1.0.1's replacement hardest case). Must promote, be removed from
    unmapped, and be logged."""
    record = _record_with_unmapped(
        "Line of Life",
        "the life line sweeps far out into the palm",
        raw_prose="deep, long, the life line sweeps far out into the palm, no breaks",
    )

    promotions = normalize(record, _REAL_LEXICON_PATH)

    fobs = record.features["Line of Life"]
    assert fobs.tokens["Curve"] == {
        "value": "sweeping_wide",
        "confidence": 1.0,
        "source": "phrase_lexicon:PN_001",
    }
    assert fobs.unmapped == []
    assert promotions == [{
        "entry_id": "PN_001",
        "feature": "Line of Life",
        "attribute": "Curve",
        "token": "sweeping_wide",
        "matched_quality": "the life line sweeps far out into the palm",
    }]


def test_ambiguous_thumb_base_curve_is_not_promoted_overmap_guard():
    """v1.0.1 OVER-MAP GUARD: "curves around the base of the thumb" is
    anatomy-neutral (every life line curves around the thumb base) and does
    NOT establish Cheiro's p139 "sweeps far out into the hand" wide-sweep
    signal -- removed from PN_001.match_any for exactly this reason. Must
    stay unmapped, not promoted, same real captured life-line prose used as
    the hardest case in test_observation_extractor.py."""
    record = _record_with_unmapped(
        "Line of Life",
        "curves around the base of the thumb",
        raw_prose="deep, long, curves around the base of the thumb, no breaks",
    )

    promotions = normalize(record, _REAL_LEXICON_PATH)

    fobs = record.features["Line of Life"]
    assert fobs.tokens == {}
    assert fobs.unmapped == [
        {"quality": "curves around the base of the thumb", "attribute_guess": "Curve"},
    ]
    assert promotions == []


def test_must_not_match_slightly_curved_is_not_promoted():
    record = _record_with_unmapped("Line of Life", "slightly curved")

    promotions = normalize(record, _REAL_LEXICON_PATH)

    fobs = record.features["Line of Life"]
    assert fobs.tokens == {}
    assert fobs.unmapped == [{"quality": "slightly curved", "attribute_guess": "Curve"}]
    assert promotions == []


def test_bare_curved_is_not_promoted():
    """No match_any phrase is a substring of bare 'curved' -- must stay
    unmapped, not promoted via a partial/fuzzy match."""
    record = _record_with_unmapped("Line of Life", "curved")

    promotions = normalize(record, _REAL_LEXICON_PATH)

    fobs = record.features["Line of Life"]
    assert fobs.tokens == {}
    assert fobs.unmapped == [{"quality": "curved", "attribute_guess": "Curve"}]
    assert promotions == []


def test_feature_guard_same_phrase_under_wrong_feature_not_promoted():
    """The identical matching phrase under 'Line of Head' (not in PN_001's
    applies_to_features=['Line of Life']) must not promote."""
    record = _record_with_unmapped("Line of Head", "curves around the base of the thumb")

    promotions = normalize(record, _REAL_LEXICON_PATH)

    fobs = record.features["Line of Head"]
    assert fobs.tokens == {}
    assert fobs.unmapped == [
        {"quality": "curves around the base of the thumb", "attribute_guess": "Curve"},
    ]
    assert promotions == []


def test_attribute_already_populated_no_overwrite_conflict_logged(caplog):
    """Curve already has an extraction-produced token -- normalize must not
    overwrite it, and the matched unmapped item must stay in place (not
    removed) since it was never actually applied.

    v1.0.1 NOTE: quality string swapped from "curves around the base of the
    thumb" to the unambiguous wide-sweep phrase -- this test exercises the
    CONFLICT branch, which is only reached when the phrase guard actually
    matches; the thumb-base phrase no longer matches anything post-v1.0.1
    (see test_ambiguous_thumb_base_curve_is_not_promoted_overmap_guard),
    so it can no longer trigger this path. Not a scope violation of "leave
    other tests as-is" -- forced by the same v1.0.1 removal instruction #1
    already reacts to elsewhere; the test's assertions/intent are unchanged,
    only the input phrase needed to still be a real match."""
    record = ObservationRecord(
        features={
            "Line of Life": FeatureObservation(
                tokens={"Curve": {"value": "straight", "confidence": 1.0}},
                unmapped=[{"quality": "the life line sweeps far out into the palm", "attribute_guess": "Curve"}],
                raw_prose="the life line sweeps far out into the palm",
            ),
        },
    )

    with caplog.at_level("INFO"):
        promotions = normalize(record, _REAL_LEXICON_PATH)

    fobs = record.features["Line of Life"]
    assert fobs.tokens == {"Curve": {"value": "straight", "confidence": 1.0}}
    assert fobs.unmapped == [
        {"quality": "the life line sweeps far out into the palm", "attribute_guess": "Curve"},
    ]
    assert promotions == []
    assert any("conflict" in message.lower() for message in caplog.messages)


def test_missing_lexicon_path_returns_empty_list_no_crash(tmp_path):
    record = _record_with_unmapped("Line of Life", "curves around the base of the thumb")
    missing_path = tmp_path / "does_not_exist.json"

    promotions = normalize(record, missing_path)

    assert promotions == []
    # record untouched -- no promotion happened
    fobs = record.features["Line of Life"]
    assert fobs.tokens == {}
    assert fobs.unmapped == [
        {"quality": "curves around the base of the thumb", "attribute_guess": "Curve"},
    ]


def test_corrupt_lexicon_json_raises_runtime_error(tmp_path):
    record = _record_with_unmapped("Line of Life", "curves around the base of the thumb")
    corrupt_path = tmp_path / "corrupt.json"
    corrupt_path.write_text("{not valid json", encoding="utf-8")

    with pytest.raises(RuntimeError, match="phrase_normalizer.normalize"):
        normalize(record, corrupt_path)


def test_empty_entries_list_returns_empty_no_crash(tmp_path):
    record = _record_with_unmapped("Line of Life", "curves around the base of the thumb")
    empty_path = tmp_path / "empty_entries.json"
    empty_path.write_text('{"meta": {}, "entries": []}', encoding="utf-8")

    promotions = normalize(record, empty_path)

    assert promotions == []
    fobs = record.features["Line of Life"]
    assert fobs.tokens == {}
