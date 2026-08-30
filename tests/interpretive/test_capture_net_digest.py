"""
tests/interpretive/test_capture_net_digest.py

Tests for agent/interpretive/capture_net_digest.py -- the read-only
summarizer over the capture-net JSONL log. Every test monkeypatches
capture_net._CAPTURE_NET_PATH into tmp_path; the real diagnostics/
capture_net/ dir is never touched, and no test here ever writes via
capture_net_digest itself (it has no write API to begin with).
"""

from __future__ import annotations

import json

import pytest

from agent.interpretive import capture_net, capture_net_digest


def _write_jsonl(path, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _row(ts, trigger, **extra) -> dict:
    base = {"ts": ts, "reading_id": "r", "trigger": trigger, "producer": "test"}
    base.update(extra)
    return base


@pytest.fixture
def capture_path(tmp_path, monkeypatch):
    path = tmp_path / "capture_net" / "failures.jsonl"
    monkeypatch.setattr(capture_net, "_CAPTURE_NET_PATH", path)
    return path


# ─── Hardest case: missing file -> empty digest, no crash ───────────────────

def test_missing_file_returns_empty_digest_no_crash(capture_path):
    assert not capture_path.exists()
    digest = capture_net_digest.build_digest()

    assert digest["total_rows"] == 0
    assert digest["date_range_seen"] is None
    assert digest["ai_decision_rows"] == []
    assert set(digest["counts_by_trigger"].keys()) == {"silence", "wrong_source", "instability", "ai_decision"}
    assert all(v == 0 for v in digest["counts_by_trigger"].values())


# ─── Malformed line mixed with good lines -> skipped, not fatal ─────────────

def test_malformed_line_skipped_good_rows_counted(capture_path):
    good1 = json.dumps(_row("2026-08-10T00:00:00+00:00", "silence"))
    bad = "{not valid json at all"
    good2 = json.dumps(_row("2026-08-11T00:00:00+00:00", "instability"))
    _write_jsonl(capture_path, [good1, bad, good2])

    digest = capture_net_digest.build_digest()

    assert digest["total_rows"] == 2
    assert digest["counts_by_trigger"]["silence"] == 1
    assert digest["counts_by_trigger"]["instability"] == 1


# ─── since/until boundary rows included (inclusive), out-of-range excluded ──

def test_since_until_boundary_inclusive_and_excludes_out_of_range(capture_path):
    ts1, ts2, ts3 = (
        "2026-08-01T00:00:00+00:00",
        "2026-08-15T12:00:00+00:00",
        "2026-08-30T23:59:59+00:00",
    )
    _write_jsonl(capture_path, [
        json.dumps(_row(ts1, "silence")),
        json.dumps(_row(ts2, "wrong_source")),
        json.dumps(_row(ts3, "instability")),
    ])

    # Exact boundary on both ends -> only the middle row.
    digest = capture_net_digest.build_digest(since=ts2, until=ts2)
    assert digest["total_rows"] == 1
    assert digest["date_range_seen"] == {"min_ts": ts2, "max_ts": ts2}

    # Full-span boundary -> all three rows.
    digest_all = capture_net_digest.build_digest(since=ts1, until=ts3)
    assert digest_all["total_rows"] == 3

    # since strictly after the last row -> nothing.
    digest_none_since = capture_net_digest.build_digest(since="2026-09-01T00:00:00+00:00")
    assert digest_none_since["total_rows"] == 0

    # until strictly before the first row -> nothing.
    digest_none_until = capture_net_digest.build_digest(until="2026-07-01T00:00:00+00:00")
    assert digest_none_until["total_rows"] == 0


# ─── counts_by_trigger_x_feature correct on a mixed fixture across hands ────

def test_counts_by_trigger_x_feature_correct_mixed_hands(capture_path):
    _write_jsonl(capture_path, [
        json.dumps(_row("2026-08-01T00:00:00+00:00", "silence", hand="right", feature="Line of Fate")),
        json.dumps(_row("2026-08-01T00:00:01+00:00", "ai_decision", hand="left", feature="Line of Head")),
        json.dumps(_row("2026-08-01T00:00:02+00:00", "silence", hand="left", feature="Line of Head")),
        json.dumps(_row("2026-08-01T00:00:03+00:00", "silence", hand="left", feature="Line of Head")),
    ])

    digest = capture_net_digest.build_digest()
    xfeat = digest["counts_by_trigger_x_feature"]

    assert xfeat["silence"] == {"Line of Fate": 1, "Line of Head": 2}
    assert xfeat["ai_decision"] == {"Line of Head": 1}
    assert xfeat["wrong_source"] == {}
    assert xfeat["instability"] == {}


# ─── ai_decision_rows lists exactly the ai_decision rows, nothing else ──────

def test_ai_decision_rows_lists_exactly_ai_decision_and_nothing_else(capture_path):
    resolved_row = _row(
        "2026-08-01T00:00:00+00:00", "ai_decision",
        hand="left", feature="Line of Head", raw_verb="fuses",
        llm_canonical_choice="merges", final_token="joins_at_origin", disposition="resolved",
    )
    _write_jsonl(capture_path, [
        json.dumps(_row("2026-08-01T00:00:01+00:00", "silence", raw_verb="wobbles")),
        json.dumps(resolved_row),
        json.dumps(_row("2026-08-01T00:00:02+00:00", "wrong_source", raw_verb="destroys")),
        json.dumps(_row("2026-08-01T00:00:03+00:00", "instability", raw_verb="fuses")),
    ])

    digest = capture_net_digest.build_digest()

    assert digest["ai_decision_rows"] == [resolved_row]


# ─── render_markdown runs on empty and populated digests without error ──────

def test_render_markdown_empty_digest_no_error(capture_path):
    digest = capture_net_digest.build_digest()
    text = capture_net_digest.render_markdown(digest)

    assert isinstance(text, str)
    assert "Capture-Net Digest" in text
    assert "0 row(s)" in text
    assert "None in range." in text


def test_render_markdown_populated_digest_no_error(capture_path):
    _write_jsonl(capture_path, [
        json.dumps(_row(
            "2026-08-01T00:00:00+00:00", "ai_decision",
            hand="left", feature="Line of Head", raw_verb="fuses",
            llm_canonical_choice="merges", final_token="joins_at_origin", disposition="resolved",
        )),
        json.dumps(_row("2026-08-02T00:00:00+00:00", "silence", hand="right", feature="Line of Fate", raw_verb="wobbles")),
    ])

    digest = capture_net_digest.build_digest()
    text = capture_net_digest.render_markdown(digest)

    assert isinstance(text, str)
    assert "2 row(s)" in text
    assert "fuses" in text
    assert "merges" in text
    assert "joins_at_origin" in text
    assert "Line of Head" in text
    assert "Line of Fate" in text
