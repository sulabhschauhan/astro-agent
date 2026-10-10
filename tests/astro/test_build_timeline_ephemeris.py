"""The two tiers composed against the real ephemeris. NO SKIPS (house style:
swisseph is a hard dependency).

The pure tests next door cover the projection logic. This file proves the real
engines actually populate it, and pins the properties that would break silently:
the sky blob carrying no birth data, and the same window serving two different
charts from one scan.
"""
import datetime as _dt

from agent.astro import build_timeline, ephemeris_cache

AS_OF = _dt.date(2026, 10, 7)
HORIZON = 365

# Two deliberately different charts: Sagittarius lagna / Cancer Moon, and
# Gemini lagna / Capricorn Moon.
CHART_A = {"planetary_positions": {"Moon": {"longitude": 105.0}},
           "meta": {"asc_lon_sidereal": 255.0}}
CHART_B = {"planetary_positions": {"Moon": {"longitude": 285.0}},
           "meta": {"asc_lon_sidereal": 65.0}}


def _shared(tmp_path):
    return ephemeris_cache.load_or_build_shared(
        AS_OF, HORIZON, cache_dir=str(tmp_path))


def test_shared_window_populates_every_fact_class(tmp_path):
    s = _shared(tmp_path)
    assert s["errors"] == {}
    assert s["ayanamsa"] == "LAHIRI" and s["nirayana"] is True
    assert len(s["ingress"]["events"]) > 100      # measured 209 over a year
    assert s["ingress"]["errors"] == {}
    assert len(s["masa"]["months"]) >= 12         # measured 14 (over-scanned)
    assert len(s["combustion"]["intervals"]) >= 5  # measured 10
    assert all(m["complete"] for m in s["masa"]["months"])


def test_shared_window_contains_no_birth_data(tmp_path):
    """The property that makes Tier A shareable and keeps it out of the gitignored
    PII directories. If a future change leaks a chart field in here, this fails."""
    def keys(node):
        if isinstance(node, dict):
            for k, v in node.items():
                yield k
                yield from keys(v)
        elif isinstance(node, list):
            for v in node:
                yield from keys(v)

    present = {k.lower() for k in keys(_shared(tmp_path))}
    forbidden = {
        # chart identity / birth details -- must never reach a shared file
        "asc_lon_sidereal", "planetary_positions", "natal", "birth",
        "birth_date", "birth_place", "latitude", "longitude", "tz", "name",
        # chart-relative projections -- these are Tier B by definition
        "house", "house_from_lagna", "house_from_moon",
        "from_house_from_lagna", "to_house_from_lagna",
        "from_house_from_moon", "to_house_from_moon",
    }
    leaked = present & forbidden
    assert not leaked, f"{sorted(leaked)} leaked into the shared blob"


def test_one_scan_serves_two_charts_with_different_houses(tmp_path):
    """Tier A is identical for both charts; Tier B differs. This is the whole
    split, asserted end to end."""
    s = _shared(tmp_path)
    a = build_timeline.build_timeline(CHART_A, AS_OF, shared_loader=lambda d, h: s)
    b = build_timeline.build_timeline(CHART_B, AS_OF, shared_loader=lambda d, h: s)
    assert a["projected"] and b["projected"]
    assert [e["jd"] for e in a["ingress"]] == [e["jd"] for e in b["ingress"]]
    assert any(x["to_house_from_lagna"] != y["to_house_from_lagna"]
               for x, y in zip(a["ingress"], b["ingress"]))
    # only ONE file was written for both charts
    assert len(list(tmp_path.glob("*.json"))) == 1


def test_every_projected_house_is_in_range(tmp_path):
    s = _shared(tmp_path)
    tl = build_timeline.build_timeline(CHART_A, AS_OF, shared_loader=lambda d, h: s)
    for e in tl["ingress"]:
        for k in ("from_house_from_lagna", "to_house_from_lagna",
                  "from_house_from_moon", "to_house_from_moon"):
            assert 1 <= e[k] <= 12


def test_a_retrograde_ingress_shows_as_a_backward_house_move(tmp_path):
    """Measured in this window: Jupiter enters the 9th from a Sagittarius lagna
    on 2026-10-31, retrogrades back into the 8th on 2027-01-24, and re-enters on
    2027-06-25. A midpoint snapshot of a multi-year period cannot express that
    sequence at all; the interval form can."""
    s = _shared(tmp_path)
    tl = build_timeline.build_timeline(CHART_A, AS_OF, shared_loader=lambda d, h: s)
    jup = [e for e in tl["ingress"] if e["body"] == "jupiter"]
    back = [e for e in jup if e["retrograde"]]
    assert back, "no retrograde Jupiter ingress in this window"
    for e in back:
        assert e["to_house_from_lagna"] < e["from_house_from_lagna"] \
            or (e["from_house_from_lagna"], e["to_house_from_lagna"]) == (1, 12)


def test_the_window_reaches_a_full_horizon_ahead(tmp_path):
    s = _shared(tmp_path)
    assert s["as_of"] == AS_OF.isoformat()
    assert s["horizon_end"] == (AS_OF + _dt.timedelta(days=HORIZON)).isoformat()
    assert s["end_jd"] - s["start_jd"] == float(HORIZON)


def test_cached_read_does_not_rescan(tmp_path):
    """The point of the store: the second chart of the day pays nothing."""
    import time
    t0 = time.time()
    _shared(tmp_path)
    cold = time.time() - t0
    t0 = time.time()
    _shared(tmp_path)
    warm = time.time() - t0
    assert warm < cold / 5.0
