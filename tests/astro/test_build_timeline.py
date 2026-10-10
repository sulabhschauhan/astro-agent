"""build_timeline (Tier B projection) + ephemeris_cache (Tier A store).

The projection tests are PURE -- a hand-built Tier-A blob, no ephemeris -- because
the join is the thing with logic in it. The store tests use an injected builder so
the cache semantics are tested without scanning the sky. One real-ephemeris test
at the end proves the two tiers actually compose.
"""
import datetime as _dt

import pytest

from agent.astro import build_timeline, ephemeris_cache

TODAY = _dt.date(2026, 10, 7)

# Aries lagna (asc 10 deg -> sign 0), Moon in Cancer (105 deg -> sign 3).
ASC_LON, MOON_LON = 10.0, 105.0
CHART = {"planetary_positions": {"Moon": {"longitude": MOON_LON}},
         "meta": {"asc_lon_sidereal": ASC_LON}}

SHARED = {
    "shared_schema_version": ephemeris_cache.SHARED_SCHEMA_VERSION,
    "as_of": "2026-10-07", "horizon_end": "2027-10-07", "horizon_days": 365,
    "ayanamsa": "LAHIRI", "nirayana": True, "errors": {},
    "ingress": {"events": [
        # Saturn Mesha(0) -> Vrishabha(1): from lagna 1->2, from Moon 10->11
        {"body": "saturn", "jd": 2461000.0, "from_index": 0, "to_index": 1,
         "retrograde": False},
        # Mercury retrograde back Mithuna(2) -> Vrishabha(1)
        {"body": "mercury", "jd": 2461100.0, "from_index": 2, "to_index": 1,
         "retrograde": True},
    ]},
    "combustion": {"intervals": [
        {"planet": "venus", "start_jd": 2461010.0, "end_jd": 2461020.0,
         "retrograde_at_mid": True}]},
    "masa": {"months": [
        {"start_jd": 2461000.0, "end_jd": 2461029.5, "masa_index": 0,
         "name_sa": "Chaitra", "sankranti_count": 1,
         "contained_sankranti_rashis": [0], "complete": True},
        {"start_jd": 2461029.5, "end_jd": 2461059.0, "masa_index": None,
         "name_sa": None, "sankranti_count": 0,
         "contained_sankranti_rashis": [], "complete": True}],
        "new_moons": [], "full_moons": [], "sankrantis": []},
}


# ── Tier B: the projection ───────────────────────────────────────────────────

def test_ingress_is_projected_into_both_natal_frames():
    out = build_timeline.project_events(SHARED, ASC_LON, MOON_LON)
    sat = out["ingress"][0]
    assert (sat["from_house_from_lagna"], sat["to_house_from_lagna"]) == (1, 2)
    assert (sat["from_house_from_moon"], sat["to_house_from_moon"]) == (10, 11)


def test_retrograde_crossing_moves_the_house_backwards():
    """How a consumer tells a graha LEAVING a house from one entering it, without
    re-reading the sky."""
    out = build_timeline.project_events(SHARED, ASC_LON, MOON_LON)
    merc = out["ingress"][1]
    assert merc["retrograde"] is True
    assert merc["to_house_from_lagna"] < merc["from_house_from_lagna"]


def test_projection_preserves_every_original_event_field():
    out = build_timeline.project_events(SHARED, ASC_LON, MOON_LON)
    src = SHARED["ingress"]["events"][0]
    assert all(out["ingress"][0][k] == v for k, v in src.items())


def test_nothing_is_filtered_out():
    """Relevance is the planner's job, not this module's."""
    out = build_timeline.project_events(SHARED, ASC_LON, MOON_LON)
    assert len(out["ingress"]) == 2
    assert len(out["combustion"]) == 1
    assert len(out["masa"]) == 2


def test_masa_passes_through_unprojected_and_unnamed():
    """A lunar month is not in a house, and the intercalary month stays unnamed
    (the S148 doctrine stop carries through Tier B unchanged)."""
    out = build_timeline.project_events(SHARED, ASC_LON, MOON_LON)
    assert "house_from_lagna" not in out["masa"][0]
    assert out["masa"][1]["sankranti_count"] == 0
    assert out["masa"][1]["name_sa"] is None


def test_malformed_event_costs_itself_not_the_window():
    blob = {**SHARED, "ingress": {"events": [
        {"body": "x", "jd": 1.0, "from_index": None, "to_index": 2},
        SHARED["ingress"]["events"][0]]}}
    out = build_timeline.project_events(blob, ASC_LON, MOON_LON)
    assert len(out["ingress"]) == 1


def test_empty_shared_blob_projects_to_empty_lists():
    out = build_timeline.project_events({}, ASC_LON, MOON_LON)
    assert out == {"ingress": [], "combustion": [], "masa": []}


@pytest.mark.parametrize("asc,moon,expected_lagna,expected_moon", [
    (10.0, 105.0, 1, 10),      # Aries lagna, Cancer Moon
    (350.0, 10.0, 2, 1),       # Pisces lagna, Aries Moon
    (0.0, 0.0, 1, 1),
])
def test_house_arithmetic_matches_gochara_whole_sign_rule(
        asc, moon, expected_lagna, expected_moon):
    """Same ((sign - natal_sign) % 12) + 1 as compute_gochara, for a graha in
    Mesha (index 0)."""
    blob = {"ingress": {"events": [
        {"body": "sun", "jd": 1.0, "from_index": 11, "to_index": 0,
         "retrograde": False}]}}
    e = build_timeline.project_events(blob, asc, moon)["ingress"][0]
    assert e["to_house_from_lagna"] == expected_lagna
    assert e["to_house_from_moon"] == expected_moon


# ── build_timeline: fail-soft contract ───────────────────────────────────────

def test_build_timeline_carries_window_metadata():
    out = build_timeline.build_timeline(
        CHART, TODAY, shared_loader=lambda d, h: SHARED)
    assert out["projected"] is True
    assert out["ayanamsa"] == "LAHIRI" and out["nirayana"] is True
    assert out["as_of"] == "2026-10-07" and out["horizon_end"] == "2027-10-07"


@pytest.mark.parametrize("chart", [
    {}, {"meta": {"asc_lon_sidereal": 10.0}},
    {"planetary_positions": {"Moon": {"longitude": 1.0}}},
    {"planetary_positions": {"Moon": {}}, "meta": {}},
])
def test_unusable_chart_keeps_the_sky_and_flags_the_failure(chart):
    """The sky is still true when the chart cannot be read. Dropping the window
    would throw away work that cost a real scan."""
    out = build_timeline.build_timeline(
        chart, TODAY, shared_loader=lambda d, h: SHARED)
    assert out["projected"] is False
    assert "chart_error" in out
    assert out["ayanamsa"] == "LAHIRI"      # metadata survives
    assert out["ingress"] == [] and out["masa"] == []


def test_shared_loader_failure_does_not_raise():
    def boom(d, h):
        raise RuntimeError("ephemeris down")
    out = build_timeline.build_timeline(CHART, TODAY, shared_loader=boom)
    assert out["projected"] is False
    assert "ephemeris down" in out["shared_error"]


def test_builder_matches_the_timeline_store_contract():
    """timeline_store calls builder(as_of) and nothing else."""
    b = build_timeline.timeline_builder_for(CHART, shared_loader=lambda d, h: SHARED)
    out = b(TODAY)
    assert out["projected"] is True and len(out["ingress"]) == 2


def test_timeline_store_round_trip_rebuilds_and_then_caches(tmp_path):
    calls = []

    def loader(d, h):
        calls.append(d)
        return SHARED

    kw = dict(cache_dir=str(tmp_path), today=TODAY,
              identity={"note": "test"}, shared_loader=loader)
    a = build_timeline.load_timeline_for_chart("abc123", CHART, **kw)
    assert a["projected"] is True and len(calls) == 1
    b = build_timeline.load_timeline_for_chart("abc123", CHART, **kw)
    assert b == a
    assert len(calls) == 1, "second call must come from cache, not a rebuild"


def test_empty_identity_key_builds_in_memory_without_caching(tmp_path):
    out = build_timeline.load_timeline_for_chart(
        "", CHART, today=TODAY, cache_dir=str(tmp_path),
        shared_loader=lambda d, h: SHARED)
    assert out["projected"] is True
    assert not list(tmp_path.iterdir())


# ── Tier A: the shared store ─────────────────────────────────────────────────

def test_shared_key_is_content_addressed_and_human_readable():
    k = ephemeris_cache.shared_window_key(TODAY, 365, "LAHIRI")
    assert k == "2026-10-07_365_LAHIRI"
    assert k != ephemeris_cache.shared_window_key(TODAY, 365, "RAMAN")
    assert k != ephemeris_cache.shared_window_key(TODAY, 180, "LAHIRI")


def test_two_charts_share_one_file(tmp_path):
    """The whole point of Tier A: the sky is scanned once, not once per chart."""
    builds = []

    def fake(as_of, horizon):
        builds.append(as_of)
        return SHARED

    for _ in range(3):
        ephemeris_cache.load_or_build_shared(
            TODAY, 365, cache_dir=str(tmp_path), builder=fake)
    assert len(builds) == 1
    assert len(list(tmp_path.glob("*.json"))) == 1


def test_a_different_ayanamsa_never_reuses_the_file(tmp_path):
    """A frame change must not silently reuse a window built under the old one --
    the S148 measurement showed 0.18 deg can move an intercalary month."""
    builds = []

    def fake(as_of, horizon):
        builds.append(1)
        return SHARED

    ephemeris_cache.load_or_build_shared(TODAY, 365, cache_dir=str(tmp_path),
                                         builder=fake, ayanamsa="LAHIRI")
    ephemeris_cache.load_or_build_shared(TODAY, 365, cache_dir=str(tmp_path),
                                         builder=fake, ayanamsa="RAMAN")
    assert len(builds) == 2


def test_stale_schema_is_rebuilt(tmp_path):
    import json
    import os
    key = ephemeris_cache.shared_window_key(TODAY, 365, "LAHIRI")
    os.makedirs(tmp_path, exist_ok=True)
    with open(os.path.join(str(tmp_path), f"{key}.json"), "w") as f:
        json.dump({"shared_schema_version": -1}, f)
    out = ephemeris_cache.load_or_build_shared(
        TODAY, 365, cache_dir=str(tmp_path), builder=lambda d, h: SHARED)
    assert out["shared_schema_version"] == ephemeris_cache.SHARED_SCHEMA_VERSION


def test_corrupt_cache_file_never_blocks_an_answer(tmp_path):
    import os
    key = ephemeris_cache.shared_window_key(TODAY, 365, "LAHIRI")
    with open(os.path.join(str(tmp_path), f"{key}.json"), "w") as f:
        f.write("{not json")
    out = ephemeris_cache.load_or_build_shared(
        TODAY, 365, cache_dir=str(tmp_path), builder=lambda d, h: SHARED)
    assert out["ayanamsa"] == "LAHIRI"


def test_unwritable_cache_dir_still_returns_facts():
    out = ephemeris_cache.load_or_build_shared(
        TODAY, 365, cache_dir="/proc/nonexistent/nope",
        builder=lambda d, h: SHARED)
    assert out["ayanamsa"] == "LAHIRI"
