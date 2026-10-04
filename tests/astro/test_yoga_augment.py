"""Unit tests for the S136 UNIFIED yoga-tag grounding in agent/astro/planner.py.

Yogas are a second tag namespace on the SAME segments (data/yoga_tags_bphs.json,
segment->yogas, the same shape as domain_tags). A segment is kept if it matches
the question's domains OR the chart's FIRED yogas, in the one domain filter --
no separate map, no bypass. These tests pin the resolver, the fail-soft
contract, and the unified filter criterion. No LLM, no live API.

The flag-OFF no-regression guarantee is covered by the existing tests/astro/
suite (which exercises build_from_plan with the flag unset); this file covers
the new helpers and the keep_segment_ids criterion.
"""
import pytest

from agent.astro import planner


def _keys():
    return planner._load_yoga_tags()["keys"]


def test_tag_file_loads_expected_keys():
    assert {"kendra_trikona_family", "dharma_karmadhipati", "gajakesari_yoga",
            "naabhasa_*", "pmp_*", "neecha_bhanga_*", "vesi", "adhi",
            "sunaphaa", "anaphaa", "kalpadruma", "mangal_dosha"} <= _keys()


def test_match_exact_key():
    assert planner._match_yoga_key("gajakesari_yoga", _keys()) == "gajakesari_yoga"
    assert planner._match_yoga_key("dharma_karmadhipati", _keys()) == "dharma_karmadhipati"


@pytest.mark.parametrize("fid,key", [
    ("naabhasa_daama", "naabhasa_*"),
    ("naabhasa_veenaa", "naabhasa_*"),
    ("pmp_bhadra", "pmp_*"),
    ("pmp_sasa", "pmp_*"),
    ("neecha_bhanga_mercury", "neecha_bhanga_*"),
])
def test_match_family_prefix(fid, key):
    assert planner._match_yoga_key(fid, _keys()) == key


def test_match_kendra_trikona_special_case():
    assert planner._match_yoga_key("kendra_trikona_7_9", _keys()) == "kendra_trikona_family"
    assert planner._match_yoga_key("kendra_trikona_10_5", _keys()) == "kendra_trikona_family"


def test_match_parked_and_unknown_return_none():
    # PVR-parked and modern-construct yogas are not in the tag vocabulary.
    assert planner._match_yoga_key("harsha_yoga", _keys()) is None
    assert planner._match_yoga_key("vipareeta_6_8_link", _keys()) is None
    assert planner._match_yoga_key("kalsarpa_yoga", _keys()) is None
    assert planner._match_yoga_key("totally_unknown", _keys()) is None


def test_fired_keys_maps_and_ignores_parked():
    cf = {"yogas": {"fired": [
        {"id": "kendra_trikona_7_9"}, {"id": "gajakesari_yoga"},
        {"id": "naabhasa_daama"}, {"id": "harsha_yoga"}]}}
    assert planner._fired_yoga_keys(cf) == {
        "kendra_trikona_family", "gajakesari_yoga", "naabhasa_*"}


@pytest.mark.parametrize("cf", [
    None, {}, {"yogas": None}, {"yogas": {"fired": None}},
    {"yogas": {"fired": [{"noid": 1}, "junk", 5]}},
])
def test_fired_keys_malformed_never_raises(cf):
    assert planner._fired_yoga_keys(cf) == set()


def test_tag_targets_units_and_segments():
    units, segs = planner._yoga_tag_targets({"kendra_trikona_family", "pmp_*"})
    assert units == {"bphs1_ch34", "bphs2_ch75"}
    assert segs == {"ch34_s011", "ch75_s001"}


def test_tag_targets_empty_when_nothing_fired():
    assert planner._yoga_tag_targets(set()) == (set(), set())


def test_naabhasa_pulls_both_ch35_and_ch36_units():
    # naabhasa doctrine spans ch35 and spills into ch36_s001 -- both units come in.
    units, segs = planner._yoga_tag_targets({"naabhasa_*"})
    assert {"bphs1_ch35", "bphs1_ch36"} <= units
    assert "ch36_s001" in segs


class _Plan:
    domains = ["career"]


def _domain_stub(seg_domains):
    return lambda *a, **k: {
        "units": [],
        "segments": [{"segment_id": sid, "domains": doms}
                     for sid, doms in seg_domains.items()],
    }


def test_filter_keeps_yoga_segment_even_on_domain_miss(monkeypatch):
    # ch34_s011 is tagged for a domain the plan does NOT want -> would drop; with
    # keep_segment_ids it is kept in the SAME pass, marked kept_yoga_tag.
    monkeypatch.setattr(planner, "_load_domain_tags",
                        _domain_stub({"ch34_s011": ["marriage"]}))
    payload = {"segments": [{"segment_id": "ch34_s011", "tokens": 10, "kept": True}]}
    out = planner.filter_segments_by_domain(
        payload, _Plan(), keep_segment_ids=frozenset({"ch34_s011"}))
    seg = out["segments"][0]
    assert seg["kept"] is True
    assert seg["domain_filter"] == "kept_yoga_tag"
    assert seg.get("yoga_tag") is True


def test_filter_empty_keep_is_noop_domain_miss_still_drops(monkeypatch):
    # No keep set -> byte-identical old behaviour: a domain-miss segment drops.
    monkeypatch.setattr(planner, "_load_domain_tags",
                        _domain_stub({"ch34_s011": ["marriage"]}))
    payload = {"segments": [{"segment_id": "ch34_s011", "tokens": 10, "kept": True}]}
    out = planner.filter_segments_by_domain(payload, _Plan())
    assert out["segments"][0]["kept"] is False
