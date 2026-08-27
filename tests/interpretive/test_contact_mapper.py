"""
tests/interpretive/test_contact_mapper.py

Tests for agent/interpretive/contact_mapper.py (S104 Step 4) -- standalone,
hardest-case-first. This module is not wired into the rules path yet
(Step 5); these tests exercise map_contact() directly against explicit
inline fixtures, mirroring the shape observation_extractor.extract_
relations' isolated "contacts" namespace actually produces.
"""

from agent.interpretive.contact_mapper import (
    map_contact,
    _DISTINCT_VERB_TABLE,
    _JOIN_FAMILY_VERBS,
    _INFLECTION_MAP,
)


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


# ─── S106: deterministic inflection normalization ──────────────────────────
# Closes the exact gap that aborted S104 Step 5b: live vision reported
# "joined" (past tense) for a Head-joins-Life contact, but only "joins"
# (base form) was declared, so map_contact silently returned token=None
# and H_028 became unreachable. Tests below are HARDEST-CASE-FIRST per
# CLAUDE.md Working Style #3 -- the exact abort-triggering case leads.


def test_joined_at_start_resolves_joins_at_origin_the_s104_abort_case():
    # HARDEST CASE FIRST: this exact contact is what aborted S104 5b.
    result = map_contact(_contact("joined", "at start"))
    assert result["token"] == "joins_at_origin"
    assert result["confidence"] == "high"
    assert result["raw_verb"] == "joined"  # verbatim, unmodified
    assert result["reason"] is None


def test_joining_at_start_resolves_joins_at_origin():
    result = map_contact(_contact("joining", "at start"))
    assert result["token"] == "joins_at_origin"
    assert result["confidence"] == "high"
    assert result["reason"] is None


def test_joined_mid_course_resolves_meets_position_split_still_governs():
    # Inflection normalizes the VERB only -- the join-family verb, once
    # normalized to its canonical "joins", still goes through the exact
    # same position split as any exact-match join-family verb.
    result = map_contact(_contact("joined", "mid-course"))
    assert result["token"] == "meets"
    assert result["confidence"] == "high"
    assert result["reason"] is None


def test_touched_and_touching_resolve_touches_distinct_table_position_independent():
    for verb in ("touched", "touching"):
        result = map_contact(_contact(verb, "at start"))
        assert result["token"] == "touches", f"verb={verb!r}"
        assert result["confidence"] == "high"
        assert result["reason"] is None
    # Position-independent: a different position must not change the outcome.
    result = map_contact(_contact("touched", "mid-course"))
    assert result["token"] == "touches"


def test_crossing_resolves_cuts():
    result = map_contact(_contact("crossing", "mid-course", target="Line of Head"))
    assert result["token"] == "cuts"
    assert result["confidence"] == "high"
    assert result["reason"] is None


def test_crossed_by_exact_multiword_still_wins_verbatim_unaffected_by_inflection():
    result = map_contact(_contact("crossed by", "mid-course", target="Line of Head"))
    assert result["token"] == "cut_by"
    assert result["confidence"] == "high"
    assert result["reason"] is None


def test_crossed_bare_is_collision_guarded_to_none_never_guessed_as_cuts():
    # COLLISION GUARD: "crossed" is the bare active -ed form of "crosses",
    # but "crossed by" is ALSO a declared passive multi-word key mapping
    # to a DIFFERENT token (cut_by). The two are genuinely ambiguous from
    # the bare word alone -- this module must never guess; "crossed" is
    # deliberately absent from _INFLECTION_MAP and falls through honestly.
    result = map_contact(_contact("crossed", "mid-course", target="Line of Head"))
    assert result["token"] is None
    assert result["confidence"] is None
    assert "crossed" in result["reason"]
    assert "crossed" not in _INFLECTION_MAP


def test_merged_and_merging_are_treated_as_merges_join_family_position_split():
    # merge-family verbs go through the SAME join-family position split
    # as any exact "merges" -- inflection normalization does not bypass
    # position-dependent resolution.
    at_start = map_contact(_contact("merged", "at start"))
    assert at_start["token"] == "joins_at_origin"
    assert at_start["confidence"] == "high"

    mid_course = map_contact(_contact("merging", "mid-course"))
    assert mid_course["token"] == "meets"
    assert mid_course["confidence"] == "high"


def test_whitespace_and_case_insensitive_for_inflected_forms_too():
    result = map_contact(_contact("  JOINED  ", "at start"))
    assert result["token"] == "joins_at_origin"
    assert result["confidence"] == "high"
    assert result["raw_verb"] == "  JOINED  "  # verbatim, unmodified


def test_unknown_genuine_synonym_still_falls_through_to_none_with_reason():
    # "fuses" is not derived from any declared verb -- a genuine synonym,
    # not a tense/aspect variant -- so it must still fall through to
    # token=None, unchanged from pre-S106 behavior (a future LLM fallback
    # is the intended remedy for this class, not inflection expansion).
    result = map_contact(_contact("fuses", "at start"))
    assert result["token"] is None
    assert result["confidence"] is None
    assert "fuses" in result["reason"]
    assert "fuses" not in _INFLECTION_MAP


def test_inflection_map_never_shadows_an_exact_table_key_with_a_different_canonical():
    # No generated inflected form may collide with an EXISTING exact
    # single-word table key -- that would silently shadow the exact
    # tables. (The module itself also enforces this at import time via a
    # RuntimeError in _build_inflection_map; this test locks the
    # INVARIANT independently of whether that guard fired correctly.)
    exact_single_word_keys = {
        v for v in list(_DISTINCT_VERB_TABLE) + list(_JOIN_FAMILY_VERBS) if " " not in v
    }
    shadowed = exact_single_word_keys & set(_INFLECTION_MAP)
    assert not shadowed, f"inflection map shadows exact keys: {shadowed}"


def test_inflection_map_is_locked_against_drift():
    # Dumps/asserts the FULL generated map so the expansion is auditable
    # and any future change to _DISTINCT_VERB_TABLE/_JOIN_FAMILY_VERBS
    # that silently alters the generated forms is caught here, not
    # discovered live. Update this fixture deliberately, in the same
    # commit as the vocabulary change that caused it to drift.
    assert _INFLECTION_MAP == {
        "joined": "joins",
        "joining": "joins",
        "merged": "merges",
        "merging": "merges",
        "meeted": "meets",
        "meeting": "meets",
        "crossing": "crosses",
        "touched": "touches",
        "touching": "touches",
        "cutted": "cuts",
        "cutting": "cuts",
        "branches": "branch",
        "branched": "branch",
        "branching": "branch",
    }
