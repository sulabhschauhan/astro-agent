"""Tests for agent/astro/fact_store.py -- the V1.5 static fact cache (S147).

Pure stdlib logic (no swisseph): the heavy assembly is injected as `builder`,
so these run anywhere."""
from __future__ import annotations

import json
import os

from agent.astro import fact_store as FS


def test_key_is_deterministic_and_normalises_case_and_space():
    a = FS.chart_cache_key("Sulabh", "Bengaluru", "1988-01-01", "00:30", exact=True)
    b = FS.chart_cache_key("  sulabh ", "BENGALURU", "1988-01-01", "00:30", exact=True)
    assert a == b
    assert len(a) == 16 and all(c in "0123456789abcdef" for c in a)


def test_key_depends_on_exact_flag():
    a = FS.chart_cache_key("S", "B", "1988-01-01", "00:30", exact=True)
    b = FS.chart_cache_key("S", "B", "1988-01-01", "00:30", exact=False)
    assert a != b


def test_miss_builds_persists_and_stamps(tmp_path):
    calls = {"n": 0}

    def builder():
        calls["n"] += 1
        return {"ascendant_sign": "Sagittarius"}

    out = FS.load_or_build("k1", builder, cache_dir=str(tmp_path),
                           identity={"name": "Sulabh"})
    assert out == {"ascendant_sign": "Sagittarius"} and calls["n"] == 1
    blob = json.loads((tmp_path / "k1.json").read_text(encoding="utf-8"))
    assert blob["schema_version"] == FS.SCHEMA_VERSION
    assert blob["identity"] == {"name": "Sulabh"}
    assert blob["facts"]["ascendant_sign"] == "Sagittarius"


def test_hit_loads_without_rebuilding(tmp_path):
    calls = {"n": 0}

    def builder():
        calls["n"] += 1
        return {"x": 1}

    FS.load_or_build("k", builder, cache_dir=str(tmp_path))
    FS.load_or_build("k", builder, cache_dir=str(tmp_path))
    assert calls["n"] == 1, "builder was re-called on a cache hit"


def test_schema_mismatch_rebuilds(tmp_path, monkeypatch):
    calls = {"n": 0}

    def builder():
        calls["n"] += 1
        return {"x": 1}

    FS.load_or_build("k", builder, cache_dir=str(tmp_path))
    monkeypatch.setattr(FS, "SCHEMA_VERSION", FS.SCHEMA_VERSION + 1)
    FS.load_or_build("k", builder, cache_dir=str(tmp_path))
    assert calls["n"] == 2, "a stale-schema file must be rebuilt"


def test_unreadable_cache_falls_back_to_building(tmp_path):
    (tmp_path / "bad.json").write_text("{ this is not json", encoding="utf-8")

    def builder():
        return {"ok": True}

    out = FS.load_or_build("bad", builder, cache_dir=str(tmp_path))
    assert out == {"ok": True}  # corrupt file never blocks the answer


def test_chart_identity_key_is_deterministic_and_sensitive():
    a = FS.chart_identity_key(2460000.123456, 262.7, exact=True)
    b = FS.chart_identity_key(2460000.123456, 262.7, exact=True)
    c = FS.chart_identity_key(2460000.123456, 262.7, exact=False)   # exact flag matters
    d = FS.chart_identity_key(2460001.0, 262.7, exact=True)         # moment matters
    assert a == b and len(a) == 16
    assert a != c and a != d


def test_chart_identity_key_empty_when_unavailable():
    assert FS.chart_identity_key(None, 262.7, exact=True) == ""
    assert FS.chart_identity_key(2460000.0, "nope", exact=True) == ""


def test_empty_key_builds_without_caching(tmp_path):
    calls = {"n": 0}

    def builder():
        calls["n"] += 1
        return {"ok": 1}

    out = FS.load_or_build("", builder, cache_dir=str(tmp_path))
    assert out == {"ok": 1} and calls["n"] == 1
    assert list(tmp_path.iterdir()) == []  # nothing written for an empty key


def test_write_failure_still_returns_built_facts():
    # an impossible cache dir -> persistence fails, build still returns
    out = FS.load_or_build("k", lambda: {"ok": 1},
                           cache_dir="/proc/does_not_exist_ro")
    assert out == {"ok": 1}
