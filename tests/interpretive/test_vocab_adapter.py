"""
tests/interpretive/test_vocab_adapter.py
Tests for agent/interpretive/vocab_adapter.py -- S121 adapter #1 (additive
only, not wired into production).

Covers: Mapped (synonym-table resolution + already-canonical exact match),
NotPerceived (perception-null phrases), Unmapped (a novel unevidenced
phrase, never guessed), the wrong-map guard (a per-(feature,attribute)
scoped synonym must not leak to a sibling pair even when the target token
would also be valid there), the hard invariant (every Mapped result is a
real menu_for() member), and the unbound-attribute path (no flat-pool
fallback).
"""

from __future__ import annotations

import pytest

from agent.interpretive import emission_menus
from agent.interpretive.vocab_adapter import (
    Mapped,
    NotPerceived,
    Unmapped,
    _FULL_SYNONYM_TABLE,
    adapt,
)


# ─── Mapped ────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "feature,attribute,raw_phrase,expected_token",
    [
        ("Line of Fate", "Depth", "well_marked", "deep"),
        ("Line of Head", "Depth", "well_marked", "deep"),
        ("Line of Heart", "Width", "thin", "narrow"),
        ("Line of Heart", "Width", "wide", "broad"),
        ("Line of Head", "Continuity", "clear", "unbroken"),
        ("Line of Head", "Slope", "sloping", "downward"),
        ("Line of Heart", "Slope", "drooping", "downward"),
    ],
)
def test_mapped_via_synonym_table(feature, attribute, raw_phrase, expected_token):
    assert adapt(feature, attribute, raw_phrase) == Mapped(token=expected_token)


@pytest.mark.parametrize(
    "feature,attribute,raw_phrase",
    [
        ("Line of Life", "Depth", "deep"),
        ("Line of Life", "Width", "narrow"),
        ("Line of Head", "Slope", "straight"),
        ("Mount of Venus", "Development", "well developed"),
        ("Upper Mount of Mars", "Development", "cannot-tell"),
    ],
)
def test_mapped_already_canonical(feature, attribute, raw_phrase):
    """A raw phrase that already IS a menu token resolves without needing
    any synonym-table entry at all (adapt() step 2)."""
    assert adapt(feature, attribute, raw_phrase) == Mapped(token=raw_phrase)


def test_mapped_already_canonical_tolerates_incidental_whitespace():
    assert adapt("Line of Life", "Depth", "  deep  ") == Mapped(token="deep")


# ─── NotPerceived ──────────────────────────────────────────────────────


@pytest.mark.parametrize("raw_phrase", ["not clearly visible", "", "none", "n/a", None])
def test_not_perceived(raw_phrase):
    assert adapt("Line of Head", "Depth", raw_phrase) == NotPerceived()


def test_not_perceived_is_case_and_whitespace_insensitive():
    assert adapt("Line of Head", "Depth", "  NOT CLEARLY VISIBLE  ") == NotPerceived()
    assert adapt("Line of Head", "Depth", "NONE") == NotPerceived()


# ─── Unmapped -- a real value attempt with no canonical route ───────────


def test_unmapped_novel_phrase_is_not_a_guess():
    result = adapt("Line of Fate", "Depth", "moderately etched")
    assert isinstance(result, Unmapped)
    assert result.raw_phrase == "moderately etched"
    assert result.reason == "no canonical route"


def test_unmapped_records_the_exact_raw_phrase_verbatim():
    """Unmapped must preserve raw_phrase untouched (not the normalized
    form) -- the capture record needs the ORIGINAL phrase to be useful for
    a future human review pass."""
    result = adapt("Line of Fate", "Depth", "  Moderately Etched  ")
    assert result == Unmapped(raw_phrase="  Moderately Etched  ", reason="no canonical route")


# ─── WRONG-MAP GUARD ─────────────────────────────────────────────────────


def test_wrong_map_guard_synonym_does_not_leak_across_sibling_features():
    """'wide' -> 'broad' is evidenced ONLY for Line of Heart's Width in the
    S121 ledger (HL_013/HL_018/HL_020). Line of Head's Width menu also
    contains 'broad', so a naive global word->token table would happily
    (and wrongly) map Line of Head's 'wide' too. The per-(feature,
    attribute)-scoped table must refuse this -- proving the scoping is
    real, not just documented."""
    assert ("Line of Head", "Width") not in _FULL_SYNONYM_TABLE
    result = adapt("Line of Head", "Width", "wide")
    assert isinstance(result, Unmapped)
    assert result.reason == "no canonical route"
    # Sanity: 'broad' really is a legal Line of Head Width token -- this is
    # a scoping refusal, not a case where 'broad' doesn't exist there.
    assert "broad" in emission_menus.menu_for("Line of Head", "Width")


def test_wrong_map_guard_ambiguous_phrase_is_not_silently_resolved():
    """A phrase that is plausible-sounding for a graded mount but was never
    entered into the synonym table must not be guessed at, even though a
    similarly-worded canonical token exists on the same menu."""
    result = adapt("Mount of Saturn", "Development", "quite well developed")
    assert isinstance(result, Unmapped)
    assert result.reason == "no canonical route"


# ─── HARD INVARIANT -- every Mapped result is a real menu_for() member ───


def test_invariant_every_synonym_table_mapping_lands_in_its_own_menu():
    for (feature, attribute), mapping in _FULL_SYNONYM_TABLE.items():
        menu = emission_menus.menu_for(feature, attribute)
        assert menu is not None, f"{(feature, attribute)} has a synonym entry but no bound menu"
        for raw_phrase, expected_token in mapping.items():
            result = adapt(feature, attribute, raw_phrase)
            assert isinstance(result, Mapped), (feature, attribute, raw_phrase, result)
            assert result.token in menu
            assert result.token == expected_token


def test_invariant_every_mapped_result_across_every_bound_menu_is_a_member():
    """Broader property sweep: feed every canonical token from every bound
    menu back through adapt(). Whenever the result IS Mapped, its token
    must be a genuine member of that same menu (the hard invariant).

    One real, documented exception: 'n/a' is simultaneously a perception-
    null phrase (adapt()'s step 1, module docstring) AND a legal
    escape-hatch token on Line of Fate's Break_Type/Length_Extent menus.
    Perception-null takes precedence by design, so 'n/a' correctly comes
    back NotPerceived there rather than Mapped -- excluded from the
    Mapped assertion below, not treated as a violation."""
    for feature, attrs in emission_menus.all_menus().items():
        for attribute, menu in attrs.items():
            for token in menu:
                result = adapt(feature, attribute, token)
                if isinstance(result, NotPerceived):
                    assert token.strip().lower() in {"not clearly visible", "", "none", "n/a"}
                    continue
                assert isinstance(result, Mapped), (feature, attribute, token, result)
                assert result.token in menu


# ─── Unbound attribute -- no flat-pool fallback ─────────────────────────


@pytest.mark.parametrize(
    "feature,attribute,raw_phrase",
    [
        ("Line of Head", "Direction", "sloping"),
        ("Line of Heart", "Direction", "drooping"),
        ("Line of Life", "Clarity", "clear"),
    ],
)
def test_unmapped_reason_attribute_unbound(feature, attribute, raw_phrase):
    assert emission_menus.menu_for(feature, attribute) is None  # precondition
    result = adapt(feature, attribute, raw_phrase)
    assert result == Unmapped(raw_phrase=raw_phrase, reason="attribute unbound")
