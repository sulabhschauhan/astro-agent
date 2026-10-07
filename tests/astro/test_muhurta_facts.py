"""Tests for agent/astro/muhurta_facts.py -- the S147 muhurta composer (Path B).

The heavy scan (muhurta_scorer.find_muhurta_windows -> swisseph) and the
panchanga limbs (panchanga_muhurta.score_panchanga_muhurta -> swisseph) are
monkeypatched, so these exercise the composer's OWN logic -- ranking, best vs
earliest-good, days/count modes, the 730-day cap, fail-soft -- with no
ephemeris. _jd_to_iso uses real swisseph.revjul, available in the full suite.
"""
from __future__ import annotations

from agent.astro import muhurta_facts as MF
from agent.astro import planner as P
from agent.astro.muhurta_facts import build_muhurta_facts, _rank_and_select


# --------------------------------------------------- pure selector (no swe) --
def _rec(sj, tier, fav=2, avoid=0):
    return {"start_jd": sj, "tier": tier, "favorable_count": fav,
            "panchanga_avoid_count": avoid}


def test_best_can_differ_from_earliest_and_tier1_beats_sooner_tier2():
    recs = [_rec(10, "TIER_2", 1), _rec(30, "TIER_1", 2, avoid=2),
            _rec(400, "TIER_1", 2, avoid=0)]
    out = _rank_and_select(recs, want_count=None, top_n=8)
    assert out["best"]["start_jd"] == 400            # strongest, though latest
    assert out["earliest_good"]["start_jd"] == 30    # earliest TIER_1, not sooner TIER_2
    assert out["none_found"] is False
    assert [r["start_jd"] for r in out["windows"]] == [400, 30, 10]   # rank order


def test_tier2_only_fallback():
    out = _rank_and_select([_rec(50, "TIER_2", 1, avoid=1), _rec(20, "TIER_2", 1, 0)],
                           want_count=None, top_n=8)
    assert out["earliest_good"]["start_jd"] == 20
    assert out["best"]["start_jd"] == 20             # same fav_count, fewer avoids wins
    assert out["none_found"] is False


def test_all_tier3_is_none_found():
    out = _rank_and_select([_rec(10, "TIER_3"), _rec(20, "TIER_3")],
                           want_count=None, top_n=8)
    assert out["none_found"] and out["best"] is None and out["earliest_good"] is None
    assert out["windows"] == []


def test_count_mode_returns_earliest_n_by_time():
    out = _rank_and_select([_rec(400, "TIER_1"), _rec(10, "TIER_2", 1), _rec(20, "TIER_1")],
                           want_count=2, top_n=8)
    assert [r["start_jd"] for r in out["windows"]] == [10, 20]   # soonest two good
    assert out["earliest_good"]["start_jd"] == 20


def test_empty_scan_is_none_found():
    out = _rank_and_select([], want_count=None, top_n=8)
    assert out["none_found"] and out["windows"] == []


# -------------------------------------- end-to-end composer, swe monkeypatched
class _Enum:
    def __init__(self, name): self.name = name


class _Win:
    def __init__(self, sj, ej, tier, fav):
        self.start_jd = sj
        self.end_jd = ej
        self.tier = _Enum(tier)
        self.favorable_count = fav
        self.chandrabala = _Enum("FAVORABLE")
        self.tarabala = _Enum("FAVORABLE")
        self.panchaka = _Enum("NOT_PANCHAK")
        self.warnings = ()


class _PM:
    tithi = "Sukla Panchami"
    yoga = "Siddha"
    karana = "Bava"
    avoid_count = 0
    warnings = ()


_CHART = {"lagna_chart": {"rasi": "Scorpio", "nakshatra": "Vishakha"}}


def _patch(mp, windows):
    mp.setattr(MF, "find_muhurta_windows", lambda ms, nk, s, e: list(windows))
    mp.setattr(MF, "score_panchanga_muhurta", lambda jd: _PM())


def test_days_mode_builds_records_and_anchors(monkeypatch):
    _patch(monkeypatch, [_Win(2460000.0, 2460000.5, "TIER_1", 2),
                         _Win(2460100.0, 2460100.5, "TIER_2", 1)])
    out = build_muhurta_facts(_CHART, 2460000.0, horizon_days=180)
    assert out["searched"]["mode"] == "days" and out["searched"]["span_days"] == 180
    assert out["best"]["tier"] == "TIER_1"
    assert out["best"]["start"].endswith("UT")       # _jd_to_iso ran (real swisseph)
    assert out["none_found"] is False


def test_horizon_cap_clamps_to_730(monkeypatch):
    _patch(monkeypatch, [])
    out = build_muhurta_facts(_CHART, 2460000.0, horizon_days=5000)
    assert out["searched"]["span_days"] == MF.MAX_SCAN_DAYS
    assert out["searched"]["capped"] is True


def test_count_mode_scans_to_ceiling(monkeypatch):
    _patch(monkeypatch, [_Win(2460001.0, 2460001.5, "TIER_1", 2)])
    out = build_muhurta_facts(_CHART, 2460000.0, want_count=3)
    assert out["searched"]["mode"] == "count" and out["searched"]["capped"] is True
    assert out["searched"]["span_days"] == MF.MAX_SCAN_DAYS


def test_bad_args_fail_soft_to_empty(monkeypatch):
    _patch(monkeypatch, [])
    assert build_muhurta_facts(_CHART, 2460000.0) == {}                          # neither
    assert build_muhurta_facts(_CHART, 2460000.0, horizon_days=180, want_count=3) == {}  # both
    assert build_muhurta_facts(_CHART, 0, horizon_days=180) == {}                # bad start_jd
    assert build_muhurta_facts(_CHART, 2460000.0, want_count=0) == {}            # count<=0
    assert build_muhurta_facts({"lagna_chart": {"rasi": "Nope", "nakshatra": "Vishakha"}},
                               2460000.0, horizon_days=180) == {}                # moon unresolvable


# ---------------------------------------- planner muhurta_horizon validation --
def _obj(**over):
    base = {"domains": ["marriage"], "houses": [7], "whose_chart": "self",
            "time_scope": "none", "in_scope": True, "reasoning": "a date to marry"}
    base.update(over)
    return base


def test_planner_parses_muhurta_horizon():
    fields, errs = P.validate_plan_object(
        _obj(muhurta=True, muhurta_horizon={"mode": "days", "value": 180}))
    assert errs == [] and fields["muhurta"] is True
    assert fields["muhurta_horizon"] == {"mode": "days", "value": 180}


def test_planner_muhurta_absent_defaults_false():
    fields, errs = P.validate_plan_object(_obj())
    assert errs == [] and fields["muhurta"] is False and fields["muhurta_horizon"] is None


def test_planner_rejects_bad_horizon():
    for bad in ({"mode": "weeks", "value": 3}, {"mode": "days", "value": 0},
                {"mode": "days", "value": -5}, {"mode": "count"}, {"value": 3}, "180"):
        fields, errs = P.validate_plan_object(_obj(muhurta=True, muhurta_horizon=bad))
        assert fields is None and any("muhurta_horizon" in e for e in errs), bad


def test_planner_nulls_horizon_when_muhurta_false():
    fields, errs = P.validate_plan_object(
        _obj(muhurta=False, muhurta_horizon={"mode": "days", "value": 180}))
    assert errs == [] and fields["muhurta_horizon"] is None


def test_planner_rejects_non_bool_muhurta():
    fields, errs = P.validate_plan_object(_obj(muhurta="yes"))
    assert fields is None and any("muhurta" in e for e in errs)
