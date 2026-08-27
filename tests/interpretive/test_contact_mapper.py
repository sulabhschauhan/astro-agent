"""
tests/interpretive/test_contact_mapper.py

Tests for agent/interpretive/contact_mapper.py (S104 Step 4) -- standalone,
hardest-case-first. This module is not wired into the rules path yet
(Step 5); these tests exercise map_contact() directly against explicit
inline fixtures, mirroring the shape observation_extractor.extract_
relations' isolated "contacts" namespace actually produces.
"""

from agent.interpretive.contact_mapper import map_contact


def _contact(verb, position, target="Line of Life", clarity="clear"):
    return {"target": target, "verb": verb, "position": position, "clarity": clarity}


def test_join_at_start_resolves_joins_at_origin_high_confidence():
    # HARDEST CASE FIRST: the live Head-Life case.
    result = map_contact(_contact("joins", "at start"))
    assert result["token"] == "joins_at_origin"
    assert result["confidence"] == "high"
    assert result["raw_verb"] == "joins"
    assert result["reason"] is None


def test_merges_mid_course_resolves_meets_high_confidence():
    result = map_contact(_contact("merges", "mid-course"))
    assert result["token"] == "meets"
    assert result["confidence"] == "high"
    assert result["reason"] is None


def test_crosses_mid_course_resolves_cuts_high_confidence():
    # The live Fate-Head case.
    result = map_contact(_contact("crosses", "mid-course", target="Line of Head"))
    assert result["token"] == "cuts"
    assert result["confidence"] == "high"
    assert result["reason"] is None


def test_touches_at_start_resolves_touches_not_joins_at_origin():
    # Verb wins over position -- touches is its own distinct token,
    # position-independent, even at "at start" where a join-family verb
    # would resolve to joins_at_origin.
    result = map_contact(_contact("touches", "at start"))
    assert result["token"] == "touches"
    assert result["confidence"] == "high"
    assert result["reason"] is None


def test_join_at_end_resolves_stopped_by_low_confidence():
    result = map_contact(_contact("joins", "at end"))
    assert result["token"] == "stopped_by"
    assert result["confidence"] == "low"
    assert result["reason"] is None


def test_join_unknown_position_is_unresolvable_quarantine():
    result = map_contact(_contact("joins", "unknown"))
    assert result["token"] is None
    assert result["confidence"] is None
    assert result["reason"]
    assert "unresolvable" in result["reason"] or "position" in result["reason"]


def test_runs_alongside_any_position_is_unknown_verb_quarantine():
    result = map_contact(_contact("runs alongside", "mid-course"))
    assert result["token"] is None
    assert result["confidence"] is None
    assert result["reason"]
    assert "runs alongside" in result["reason"]

    # Position doesn't matter for an unknown verb -- still quarantined.
    result_at_start = map_contact(_contact("runs alongside", "at start"))
    assert result_at_start["token"] is None
    assert result_at_start["reason"]


def test_crossed_by_resolves_cut_by():
    result = map_contact(_contact("crossed by", "mid-course"))
    assert result["token"] == "cut_by"
    assert result["confidence"] == "high"
    assert result["reason"] is None


def test_stopped_by_resolves_stopped_by():
    result = map_contact(_contact("stopped by", "at end"))
    assert result["token"] == "stopped_by"
    assert result["confidence"] == "high"
    assert result["reason"] is None


def test_malformed_contact_missing_verb_key_returns_none_no_raise():
    malformed = {"target": "Line of Life", "position": "at start", "clarity": "clear"}
    result = map_contact(malformed)  # must not raise
    assert result["token"] is None
    assert result["confidence"] is None
    assert result["reason"]


def test_malformed_contact_not_a_dict_returns_none_no_raise():
    result = map_contact("not a dict")  # must not raise
    assert result["token"] is None
    assert result["reason"]


# ─── Additional coverage beyond the mandated set ───────────────────────────

def test_all_distinct_verb_table_entries_resolve_high_confidence():
    from agent.interpretive.contact_mapper import _DISTINCT_VERB_TABLE

    for verb, expected_token in _DISTINCT_VERB_TABLE.items():
        result = map_contact(_contact(verb, "unknown"))  # position irrelevant for distinct verbs
        assert result["token"] == expected_token, f"verb {verb!r} expected {expected_token!r}"
        assert result["confidence"] == "high"
        assert result["reason"] is None


def test_verb_matching_is_case_and_whitespace_insensitive():
    result = map_contact(_contact("  CROSSES  ", "mid-course"))
    assert result["token"] == "cuts"
    assert result["confidence"] == "high"


def test_none_token_always_carries_nonempty_reason():
    quarantine_cases = [
        _contact("runs alongside", "unknown"),
        _contact("joins", "unknown"),
        {"target": "X", "position": "at start", "clarity": "clear"},  # missing verb
    ]
    for contact in quarantine_cases:
        result = map_contact(contact)
        assert result["token"] is None
        assert isinstance(result["reason"], str) and result["reason"].strip()
