"""
tests/interpretive/test_emission_menus.py
Tests for agent/interpretive/emission_menus.py -- THE single emission-menu
accessor (S121 #2b-i). Additive only; nothing consumes this module yet.

Covers: the committed menus come back verbatim from the real registry;
UNBOUND attributes return None (no flat-pool fallback); the
normalization_worklist has exactly 14 entries; and -- the "not a hardcoded
copy" proof -- the loader is exercised against a synthetic tmp registry
file whose content differs from the real one, so a regression that
silently hardcodes menu data in Python (rather than reading
data/ontology_registry.json) would be caught here even if the "real
registry" assertions still happened to pass.
"""

from __future__ import annotations

import json

import pytest

from agent.interpretive import emission_menus


# ─── committed menus come back verbatim (real registry) ──────────────────


@pytest.mark.parametrize(
    "feature,attribute,expected",
    [
        ("Line of Life", "Depth", ("deep", "shallow")),
        ("Line of Head", "Depth", ("deep", "shallow")),
        ("Line of Heart", "Depth", ("deep", "shallow")),
        ("Line of Fate", "Depth", ("deep", "shallow")),
        ("Line of Life", "Width", ("narrow", "broad")),
        ("Line of Head", "Width", ("narrow", "broad")),
        ("Line of Life", "Length", ("short", "medium", "long")),
        ("Line of Fate", "Length", ("short", "medium", "long")),
        ("Line of Life", "Curve", ("straight", "curved")),
        ("Line of Life", "Continuity", ("unbroken", "broken", "chained", "forked", "islanded")),
        ("Line of Head", "Continuity", ("unbroken", "broken", "chained", "forked", "islanded")),
        ("Line of Fate", "Length_Extent", ("cutting_into_finger_of_Saturn", "n/a")),
        ("Line of Fate", "Break_Type", ("broken", "broken_overlapping", "n/a")),
        ("Line of Head", "Slope", ("upward", "downward", "straight")),
        ("Line of Head", "Slope_Magnitude", ("slight", "very")),
        ("Line of Head", "Proximity", ("touching", "medium", "distant")),
        ("Line of Head", "ORIGIN", ("Mount of Jupiter", "Line of Life", "Lower Mount of Mars")),
        ("Line of Head", "TERMINATION", ("Mount of Luna", "Percussion", "Upper Mount of Mars")),
        (
            "Mount of Venus",
            "Development",
            (
                "well developed", "small", "abnormally large", "full and large",
                "very poor development", "not well developed", "depressed",
                "very high", "not notably developed", "cannot-tell",
            ),
        ),
        ("Mount of Jupiter", "Development", ("developed", "not notably developed", "cannot-tell")),
        ("Upper Mount of Mars", "Development", ("large", "present", "not notably developed", "cannot-tell")),
    ],
)
def test_menu_for_returns_committed_menu_verbatim(feature, attribute, expected):
    assert emission_menus.menu_for(feature, attribute) == expected


def test_menu_for_returns_a_tuple_not_a_list():
    # menu_for's return type is load-bearing for callers that treat it as
    # immutable -- a list would let a caller mutate the module cache.
    assert isinstance(emission_menus.menu_for("Line of Life", "Depth"), tuple)


# ─── UNBOUND attributes return None, never a flat-pool fallback ──────────


@pytest.mark.parametrize(
    "feature,attribute",
    [
        ("Line of Head", "Direction"),
        ("Line of Heart", "Direction"),
        ("Line of Life", "Clarity"),
        # Curve is bound for Line of Life but explicitly NOT bound for
        # Head/Heart/Fate (S121 2a report: never solicited on those 3
        # lines) -- proves is_unbound is feature-aware, not attribute-only.
        ("Line of Head", "Curve"),
        ("Line of Heart", "Curve"),
        ("Line of Fate", "Curve"),
        # Never a real combination at all -- still reads as "no menu",
        # per this accessor's documented, deliberately narrow scope.
        ("Mount of Venus", "Depth"),
    ],
)
def test_unbound_attributes_return_none_not_a_fallback(feature, attribute):
    assert emission_menus.menu_for(feature, attribute) is None


@pytest.mark.parametrize(
    "feature,attribute",
    [
        ("Line of Head", "Direction"),
        ("Line of Life", "Clarity"),
        ("Line of Head", "Curve"),
    ],
)
def test_is_unbound_true_for_unbound_attributes(feature, attribute):
    assert emission_menus.is_unbound(feature, attribute) is True


def test_is_unbound_false_for_a_bound_attribute():
    assert emission_menus.is_unbound("Line of Life", "Curve") is False
    assert emission_menus.is_unbound("Line of Head", "Depth") is False


# ─── normalization_worklist: 14 committed entries, spec for task #5 ──────


def test_normalization_worklist_has_14_entries():
    entries = emission_menus.normalization_worklist()
    assert len(entries) == 14


def test_normalization_worklist_entries_are_dicts_with_required_keys():
    entries = emission_menus.normalization_worklist()
    required = {"rule_id", "feature", "attribute", "from", "to", "fix_type"}
    for entry in entries:
        assert required.issubset(entry.keys())


def test_normalization_worklist_contains_known_rewrites():
    entries = {(e["rule_id"], e["attribute"]): e for e in emission_menus.normalization_worklist()}
    assert entries[("FT_001", "Depth")]["from"] == "well_marked"
    assert entries[("FT_001", "Depth")]["to"] == "deep"
    assert entries[("FT_006", "Length")]["to_attribute"] == "Length_Extent"
    assert entries[("FT_012", "Continuity")]["to_attribute"] == "Break_Type"


def test_normalization_worklist_excludes_out_of_scope_untouched():
    # out_of_scope_untouched (6 rows: H_010a/H_010b comparative Depth,
    # L_018 Clarity, L_023/L_024/HL_016 parked granularity tokens) is a
    # SEPARATE registry list documenting rules deliberately left alone --
    # not rewrites for task #5 to apply. Confirm none of those rule_ids
    # leak into the worklist this accessor exposes.
    worklist_rule_ids = {e["rule_id"] for e in emission_menus.normalization_worklist()}
    assert "H_010a" not in worklist_rule_ids
    assert "L_018" not in worklist_rule_ids
    assert "L_023" not in worklist_rule_ids


# ─── all_menus(): full map, shape check against the real registry ───────


def test_all_menus_includes_every_expected_feature():
    menus = emission_menus.all_menus()
    for feature in (
        "Line of Life", "Line of Head", "Line of Heart", "Line of Fate",
        "Mount of Venus", "Mount of Jupiter", "Mount of Saturn",
        "Mount of the Sun", "Upper Mount of Mars",
    ):
        assert feature in menus


def test_all_menus_excludes_reserved_non_feature_keys():
    menus = emission_menus.all_menus()
    for reserved in ("_meta", "normalization_worklist", "_mounts_note", "unbound"):
        assert reserved not in menus


def test_all_menus_is_a_copy_not_the_live_cache():
    menus = emission_menus.all_menus()
    menus["Line of Life"]["Depth"] = ("mutated",)
    # a second call must be unaffected -- proves all_menus() does not leak
    # a reference to the module's internal cache.
    assert emission_menus.all_menus()["Line of Life"]["Depth"] == ("deep", "shallow")


# ─── proof this is a REAL reader, not a hardcoded copy ───────────────────
# Exercises the loader/cache-builder functions directly against a synthetic
# tmp registry whose emission_menus content differs from the real file --
# a regression that hardcodes menu data in Python rather than reading JSON
# would still pass every test above (the hardcoded copy could coincidentally
# match the real registry) but would fail these, since there is nothing to
# hardcode a match against here.


def test_loader_reads_from_the_given_registry_path_not_a_hardcoded_copy(tmp_path):
    synthetic_registry = {
        "emission_menus": {
            "_meta": {"purpose": "synthetic test fixture"},
            "normalization_worklist": {"entries": [{"rule_id": "ZZZ_1", "feature": "Test Feature",
                                                      "attribute": "Test Attr", "from": "x",
                                                      "to": "y", "fix_type": "value_normalization"}]},
            "unbound": {"Some Attr": {"status": "UNBOUND: pending ruling"}},
            "Test Feature": {
                "Test Attr": {"menu": ["alpha", "beta", "gamma"]},
            },
        }
    }
    registry_path = tmp_path / "synthetic_registry.json"
    registry_path.write_text(json.dumps(synthetic_registry), encoding="utf-8")

    loaded = emission_menus._load_emission_menus(registry_path)
    cache = emission_menus._build_menu_cache(loaded)

    assert cache == {"Test Feature": {"Test Attr": ("alpha", "beta", "gamma")}}
    # a token that only exists in the REAL registry must be absent here --
    # proves this run did not silently fall back to the real file/cache.
    assert "Line of Life" not in cache
    assert cache["Test Feature"]["Test Attr"] != ("deep", "shallow")


def test_loader_raises_a_clear_error_when_emission_menus_key_is_missing(tmp_path):
    registry_path = tmp_path / "no_emission_menus.json"
    registry_path.write_text(json.dumps({"meta": {"version": "0.0.0"}}), encoding="utf-8")

    with pytest.raises(RuntimeError, match="emission_menus"):
        emission_menus._load_emission_menus(registry_path)


def test_loader_raises_a_clear_error_when_file_is_missing(tmp_path):
    missing_path = tmp_path / "does_not_exist.json"
    with pytest.raises(RuntimeError, match="not found"):
        emission_menus._load_emission_menus(missing_path)


def test_loader_raises_a_clear_error_on_malformed_json(tmp_path):
    registry_path = tmp_path / "malformed.json"
    registry_path.write_text("{not valid json", encoding="utf-8")

    with pytest.raises(RuntimeError, match="not valid JSON"):
        emission_menus._load_emission_menus(registry_path)


def test_module_cache_matches_a_fresh_independent_parse_of_the_real_registry():
    # Cross-check: independently re-parse data/ontology_registry.json in
    # THIS test (not via the module under test) and confirm the module's
    # cached menu_for output matches -- catches any drift between the
    # module's own loading logic and the actual committed file.
    real_path = emission_menus._DEFAULT_REGISTRY_PATH
    fresh = json.loads(real_path.read_text(encoding="utf-8"))
    fresh_depth_menu = tuple(fresh["emission_menus"]["Line of Life"]["Depth"]["menu"])
    assert emission_menus.menu_for("Line of Life", "Depth") == fresh_depth_menu

    fresh_worklist_len = len(fresh["emission_menus"]["normalization_worklist"]["entries"])
    assert len(emission_menus.normalization_worklist()) == fresh_worklist_len
