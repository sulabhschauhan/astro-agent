"""Tests for agent.astro.dated_facts -- the S152 timeline-kind dispatcher.

The trim functions are PURE selection over already-scanned records, so they are
tested on synthetic timeline output with a fixed `now_jd` (HARDEST CASE FIRST:
past / ongoing / near / far windows, and a standard vs intercalary month).
`build_timeline_facts` is tested with an INJECTED builder, so no ephemeris scan
and no network happen -- the dispatcher's decisions (which caps, which horizon,
fail-soft) are what these pin, not the astronomy (that is build_timeline's own
oracle-tested job).
"""
from __future__ import annotations

import datetime as _dt

from agent.astro import dated_facts as df

_NOW = 2461000.0          # an arbitrary fixed Julian Day used as "now" in trims
_AS_OF = _dt.date(2026, 10, 17)


# ── trim_ingress ───────────────────────────────────────────────────────────

def test_trim_ingress_keeps_earliest_per_body_and_orders_by_date():
    events = [  # build_timeline hands these time-sorted; two Saturn rows, two bodies
        {"body": "saturn", "jd": _NOW + 50, "from_index": 10, "to_index": 11,
         "to_house_from_lagna": 8, "to_house_from_moon": 3, "retrograde": False},
        {"body": "mars", "jd": _NOW + 120, "from_index": 0, "to_index": 1,
         "to_house_from_lagna": 10, "to_house_from_moon": 5, "retrograde": False},
        {"body": "saturn", "jd": _NOW + 900, "from_index": 11, "to_index": 0,
         "to_house_from_lagna": 9, "to_house_from_moon": 4, "retrograde": True},
    ]
    out = df.trim_ingress(events)
    bodies = [e["body"] for e in out["events"]]
    assert bodies == ["Saturn", "Mars"]              # one per body, earliest kept, title-cased
    sat = out["events"][0]
    assert sat["from_sign"] == "Aquarius" and sat["to_sign"] == "Pisces"  # idx 10->11
    assert sat["to_house_from_lagna"] == 8 and sat["to_house_from_moon"] == 3


def test_trim_ingress_tolerates_bad_sign_index():
    out = df.trim_ingress([{"body": "mercury", "jd": _NOW + 1,
                            "from_index": None, "to_index": 99,
                            "to_house_from_lagna": 2, "to_house_from_moon": 7}])
    assert out["events"][0]["from_sign"] is None
    assert out["events"][0]["to_sign"] is None       # 99 out of range -> None, no raise


# ── trim_combustion ────────────────────────────────────────────────────────

def test_trim_combustion_drops_past_and_far_keeps_current_and_near():
    intervals = [
        {"planet": "Sun", "start_jd": _NOW - 20, "end_jd": _NOW - 10},   # over -> drop
        {"planet": "Venus", "start_jd": _NOW - 5, "end_jd": _NOW + 5,    # ongoing -> keep
         "retrograde_at_mid": False},
        {"planet": "Mercury", "start_jd": _NOW + 30, "end_jd": _NOW + 40,  # near -> keep
         "retrograde_at_mid": True},
        {"planet": "Mars", "start_jd": _NOW + 300, "end_jd": _NOW + 310},  # beyond 180 -> drop
    ]
    out = df.trim_combustion(intervals, _NOW)
    planets = [w["planet"] for w in out["windows"]]
    assert planets == ["Venus", "Mercury"]           # ordered by start, past/far removed
    assert out["windows"][0]["ongoing"] is True
    assert out["windows"][1]["ongoing"] is False
    assert out["windows"][1]["retrograde_at_mid"] is True


# ── trim_masa ──────────────────────────────────────────────────────────────

def test_trim_masa_finds_current_caps_upcoming_and_passes_name_through():
    months = [
        {"start_jd": _NOW - 10, "end_jd": _NOW + 20, "complete": True,
         "sankranti_count": 1, "name_sa": "Kartika", "masa_index": 7},
        {"start_jd": _NOW + 20, "end_jd": _NOW + 50, "complete": True,
         "sankranti_count": 2, "name_sa": None, "masa_index": None},      # intercalary
        {"start_jd": _NOW + 50, "end_jd": _NOW + 80, "complete": True,
         "sankranti_count": 1, "name_sa": "Margashirsha", "masa_index": 8},
        {"start_jd": _NOW + 80, "end_jd": _NOW + 110, "complete": True,
         "sankranti_count": 1, "name_sa": "Pausha", "masa_index": 9},     # 3rd -> dropped (cap 2)
        {"start_jd": _NOW + 5, "end_jd": _NOW + 9, "complete": False,     # incomplete -> ignored
         "sankranti_count": 1, "name_sa": "X", "masa_index": 0},
    ]
    out = df.trim_masa(months, _NOW)
    assert out["current"]["name_sa"] == "Kartika"
    assert len(out["upcoming"]) == 2
    assert out["upcoming"][0]["name_sa"] is None          # intercalary name NOT invented
    assert out["upcoming"][0]["sankranti_count"] == 2
    assert out["upcoming"][1]["name_sa"] == "Margashirsha"


# ── build_timeline_facts (injected builder; no scan, no network) ───────────

_PROJECTED = {
    "projected": True,
    "horizon_end": "2029-10-21",
    "ingress": [{"body": "saturn", "jd": _NOW + 50, "from_index": 10, "to_index": 11,
                 "to_house_from_lagna": 8, "to_house_from_moon": 3, "retrograde": False}],
    "combustion": [{"planet": "Mercury", "start_jd": _NOW + 10, "end_jd": _NOW + 20,
                    "retrograde_at_mid": False}],
    "masa": [{"start_jd": _NOW - 5, "end_jd": _NOW + 25, "complete": True,
              "sankranti_count": 1, "name_sa": "Kartika", "masa_index": 7}],
}


def _fake_builder(seen):
    def _b(chart, as_of, *, horizon_days):
        seen["horizon_days"] = horizon_days
        seen["as_of"] = as_of
        return _PROJECTED
    return _b


def test_build_timeline_facts_returns_only_requested_caps():
    seen = {}
    out = df.build_timeline_facts({}, ["ingress"], as_of=_AS_OF, now_jd=_NOW,
                                  builder=_fake_builder(seen))
    assert set(out) == {"ingress"}
    assert out["ingress"]["events"][0]["body"] == "Saturn"
    assert out["ingress"]["window"]["end_date"] == "2029-10-21"


def test_build_timeline_facts_scans_at_the_widest_requested_horizon():
    seen = {}
    df.build_timeline_facts({}, ["combustion", "masa"], as_of=_AS_OF, now_jd=_NOW,
                            builder=_fake_builder(seen))
    assert seen["horizon_days"] == 400          # max(400, 400); never the 1100 ingress scan
    seen2 = {}
    df.build_timeline_facts({}, ["combustion", "ingress"], as_of=_AS_OF, now_jd=_NOW,
                            builder=_fake_builder(seen2))
    assert seen2["horizon_days"] == 1100         # ingress widens the shared scan


def test_build_timeline_facts_unknown_caps_build_nothing():
    assert df.build_timeline_facts({}, ["not_a_cap"], as_of=_AS_OF, now_jd=_NOW,
                                   builder=_fake_builder({})) == {}


def test_build_timeline_facts_fail_soft_when_not_projected():
    out = df.build_timeline_facts({}, ["ingress"], as_of=_AS_OF, now_jd=_NOW,
                                  builder=lambda *a, **k: {"projected": False,
                                                           "chart_error": "bad"})
    assert out == {}


def test_build_timeline_facts_fail_soft_when_builder_raises():
    def _boom(*a, **k):
        raise RuntimeError("scan blew up")
    out = df.build_timeline_facts({}, ["ingress"], as_of=_AS_OF, now_jd=_NOW,
                                  builder=_boom)
    assert out == {}                            # a bad scan costs the facts, not the answer
