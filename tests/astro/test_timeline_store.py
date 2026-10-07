"""Tests for agent/astro/timeline_store.py -- the V1.5 dated fact cache (S147).

Pure stdlib logic (no swisseph): the ephemeris sweep is injected as `builder`,
and `today` is injected, so re-anchor behaviour is deterministic and runs
anywhere."""
from __future__ import annotations

import datetime as dt
import json

from agent.astro import timeline_store as TS


def _day(s: str) -> dt.date:
    return dt.date.fromisoformat(s)


# ── needs_reanchor: the single-threshold anchor logic ───────────────────────

def test_reanchor_true_for_missing_or_malformed_blob():
    assert TS.needs_reanchor(None, _day("2026-10-04")) is True
    assert TS.needs_reanchor("not a dict", _day("2026-10-04")) is True
    assert TS.needs_reanchor({}, _day("2026-10-04")) is True


def test_reanchor_true_on_schema_mismatch():
    blob = {"timeline_schema_version": TS.TIMELINE_SCHEMA_VERSION + 1,
            "horizon_end": "2099-01-01"}
    assert TS.needs_reanchor(blob, _day("2026-10-04")) is True


def test_reanchor_true_on_malformed_horizon():
    blob = {"timeline_schema_version": TS.TIMELINE_SCHEMA_VERSION,
            "horizon_end": "not-a-date"}
    assert TS.needs_reanchor(blob, _day("2026-10-04")) is True


def test_reanchor_false_when_window_reaches_far_enough():
    # horizon 200d ahead > 90d tail -> fresh
    blob = {"timeline_schema_version": TS.TIMELINE_SCHEMA_VERSION,
            "horizon_end": (_day("2026-10-04") + dt.timedelta(days=200)).isoformat()}
    assert TS.needs_reanchor(blob, _day("2026-10-04")) is False


def test_reanchor_fires_exactly_at_the_tail_boundary():
    today = _day("2026-10-04")
    # exactly 90d ahead -> NOT yet below threshold (< is strict) -> fresh
    at_90 = {"timeline_schema_version": TS.TIMELINE_SCHEMA_VERSION,
             "horizon_end": (today + dt.timedelta(days=90)).isoformat()}
    assert TS.needs_reanchor(at_90, today) is False
    # 89d ahead -> below threshold -> rebuild
    at_89 = {"timeline_schema_version": TS.TIMELINE_SCHEMA_VERSION,
             "horizon_end": (today + dt.timedelta(days=89)).isoformat()}
    assert TS.needs_reanchor(at_89, today) is True


def test_reanchor_true_when_window_already_in_the_past():
    blob = {"timeline_schema_version": TS.TIMELINE_SCHEMA_VERSION,
            "horizon_end": "2020-01-01"}
    assert TS.needs_reanchor(blob, _day("2026-10-04")) is True


# ── load_or_refresh: build / persist / hit / re-anchor ──────────────────────

def test_miss_builds_stamps_window_and_persists(tmp_path):
    calls = {"n": 0, "as_of": None}

    def builder(as_of):
        calls["n"] += 1
        calls["as_of"] = as_of
        return {"transit": {"ingresses": []}}

    today = _day("2026-10-04")
    out = TS.load_or_refresh("k1", builder, today, cache_dir=str(tmp_path),
                             identity={"as_of_note": "x"})
    assert out == {"transit": {"ingresses": []}} and calls["n"] == 1
    assert calls["as_of"] == today  # builder is handed the anchor
    blob = json.loads((tmp_path / "k1.json").read_text(encoding="utf-8"))
    assert blob["timeline_schema_version"] == TS.TIMELINE_SCHEMA_VERSION
    assert blob["as_of"] == "2026-10-04"
    assert blob["horizon_end"] == (today + dt.timedelta(days=TS.WINDOW_DAYS)).isoformat()
    assert blob["identity"] == {"as_of_note": "x"}


def test_fresh_window_loads_without_rebuilding(tmp_path):
    calls = {"n": 0}

    def builder(as_of):
        calls["n"] += 1
        return {"x": 1}

    today = _day("2026-10-04")
    TS.load_or_refresh("k", builder, today, cache_dir=str(tmp_path))
    # a day later, still deep inside the window -> no rebuild
    TS.load_or_refresh("k", builder, today + dt.timedelta(days=1),
                       cache_dir=str(tmp_path))
    assert calls["n"] == 1, "a window that still reaches far enough must not rebuild"


def test_stale_tail_triggers_reanchor_and_rewrites_window(tmp_path):
    calls = {"n": 0, "anchors": []}

    def builder(as_of):
        calls["n"] += 1
        calls["anchors"].append(as_of)
        return {"n": calls["n"]}

    today = _day("2026-10-04")
    TS.load_or_refresh("k", builder, today, cache_dir=str(tmp_path))
    # jump to 300d later: horizon (365d from build) now only 65d ahead -> rebuild
    later = today + dt.timedelta(days=300)
    out = TS.load_or_refresh("k", builder, later, cache_dir=str(tmp_path))
    assert calls["n"] == 2 and out == {"n": 2}
    assert calls["anchors"][1] == later  # re-anchored to the new "now"
    blob = json.loads((tmp_path / "k.json").read_text(encoding="utf-8"))
    assert blob["as_of"] == later.isoformat()  # file overwritten, not duplicated


def test_schema_bump_rebuilds(tmp_path, monkeypatch):
    calls = {"n": 0}

    def builder(as_of):
        calls["n"] += 1
        return {"x": 1}

    today = _day("2026-10-04")
    TS.load_or_refresh("k", builder, today, cache_dir=str(tmp_path))
    monkeypatch.setattr(TS, "TIMELINE_SCHEMA_VERSION", TS.TIMELINE_SCHEMA_VERSION + 1)
    TS.load_or_refresh("k", builder, today, cache_dir=str(tmp_path))
    assert calls["n"] == 2, "a stale-schema window must be rebuilt"


def test_corrupt_file_falls_back_to_building(tmp_path):
    (tmp_path / "bad.json").write_text("{ not json", encoding="utf-8")
    out = TS.load_or_refresh("bad", lambda as_of: {"ok": True},
                             _day("2026-10-04"), cache_dir=str(tmp_path))
    assert out == {"ok": True}


def test_empty_key_builds_without_caching(tmp_path):
    calls = {"n": 0}

    def builder(as_of):
        calls["n"] += 1
        return {"ok": 1}

    out = TS.load_or_refresh("", builder, _day("2026-10-04"), cache_dir=str(tmp_path))
    assert out == {"ok": 1} and calls["n"] == 1
    assert list(tmp_path.iterdir()) == []  # nothing written for an empty key


def test_write_failure_still_returns_built_facts():
    out = TS.load_or_refresh("k", lambda as_of: {"ok": 1}, _day("2026-10-04"),
                             cache_dir="/proc/does_not_exist_ro")
    assert out == {"ok": 1}


def test_today_defaults_to_date_today_when_omitted(tmp_path):
    out = TS.load_or_refresh("k", lambda as_of: {"ok": as_of.isoformat()},
                             cache_dir=str(tmp_path))
    assert out["ok"] == dt.date.today().isoformat()
