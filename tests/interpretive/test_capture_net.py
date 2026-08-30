"""
tests/interpretive/test_capture_net.py

Tests for agent/interpretive/capture_net.py (failure-capture net, Astro
Agent Task A) -- standalone, not wired into any caller yet. All writes
are redirected into tmp_path via monkeypatching capture_net._CAPTURE_NET_PATH
-- the real diagnostics/capture_net/ dir is never touched by this file.
"""

from __future__ import annotations

import json
import logging

import pytest

from agent.interpretive import capture_net


def _read_lines(path):
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8")
    return [line for line in text.splitlines() if line]


# ─── Hardest case: unwritable path degrades to WARNING, never raises ────────

def test_unwritable_path_logs_warning_and_does_not_raise(tmp_path, monkeypatch, caplog):
    # Make the parent directory impossible to create: a FILE sits where a
    # directory needs to go, so mkdir(parents=True) must fail.
    blocker = tmp_path / "blocked"
    blocker.write_text("i am a file, not a directory", encoding="utf-8")
    bad_path = blocker / "sub" / "failures.jsonl"
    monkeypatch.setattr(capture_net, "_CAPTURE_NET_PATH", bad_path)

    with caplog.at_level(logging.WARNING, logger="agent.interpretive.capture_net"):
        result = capture_net.record(
            trigger="silence", producer="test", payload={"raw_verb": "joins"},
            reading_id="r1",
        )

    assert result is None  # never raises, returns None
    assert any("capture_net.record" in rec.message for rec in caplog.records)
    assert not bad_path.exists()


# ─── Unknown disposition writes nothing ──────────────────────────────────────

def test_unknown_disposition_writes_nothing(tmp_path, monkeypatch):
    out_path = tmp_path / "capture_net" / "failures.jsonl"
    monkeypatch.setattr(capture_net, "_CAPTURE_NET_PATH", out_path)

    audits = [
        {"raw_verb": "touches", "disposition": "already_resolved_no_llm_needed",
         "llm_canonical_choice": None, "final_token": "touches"},
    ]
    capture_net.map_fallback_audits(audits, reading_id="r2")

    assert _read_lines(out_path) == []


# ─── Each trigger category maps correctly ────────────────────────────────────

@pytest.mark.parametrize("disposition,expected_trigger", [
    ("llm_unclear", "silence"),
    ("position_unresolved", "silence"),
    ("hallucination", "wrong_source"),
    ("batch_call_failed", "instability"),
    ("batch_malformed_response", "instability"),
    ("resolved", "ai_decision"),
])
def test_disposition_maps_to_expected_trigger(tmp_path, monkeypatch, disposition, expected_trigger):
    out_path = tmp_path / "capture_net" / "failures.jsonl"
    monkeypatch.setattr(capture_net, "_CAPTURE_NET_PATH", out_path)

    audits = [{
        "raw_verb": "fuses", "target": "life", "position": "mid-course",
        "llm_canonical_choice": "joins", "final_token": "joins_at_mid",
        "disposition": disposition,
    }]
    capture_net.map_fallback_audits(audits, reading_id="r3")

    lines = _read_lines(out_path)
    assert len(lines) == 1
    entry = json.loads(lines[0])
    assert entry["trigger"] == expected_trigger
    assert entry["disposition"] == disposition
    assert entry["producer"] == "palm_reading_fallback"
    assert entry["reading_id"] == "r3"


# ─── JSONL is valid append: two events -> two lines ──────────────────────────

def test_two_records_append_as_two_valid_jsonl_lines(tmp_path, monkeypatch):
    out_path = tmp_path / "capture_net" / "failures.jsonl"
    monkeypatch.setattr(capture_net, "_CAPTURE_NET_PATH", out_path)

    capture_net.record("silence", "test", {"raw_verb": "a"}, reading_id="r4")
    capture_net.record("wrong_source", "test", {"raw_verb": "b"}, reading_id="r4")

    lines = _read_lines(out_path)
    assert len(lines) == 2
    first = json.loads(lines[0])
    second = json.loads(lines[1])
    assert first["raw_verb"] == "a"
    assert second["raw_verb"] == "b"
    assert first["trigger"] == "silence"
    assert second["trigger"] == "wrong_source"
    # ts present and ISO-parseable on both
    for entry in (first, second):
        assert "ts" in entry
        assert "T" in entry["ts"]


# ─── No palm text/image bytes ever leak into a record ────────────────────────

def test_no_palm_text_or_image_bytes_leak_into_record(tmp_path, monkeypatch):
    out_path = tmp_path / "capture_net" / "failures.jsonl"
    monkeypatch.setattr(capture_net, "_CAPTURE_NET_PATH", out_path)

    payload = {
        "raw_verb": "joins", "disposition": "resolved",
        "llm_canonical_choice": "joins", "final_token": "joins_at_mid",
        # Fields that must NEVER appear in a capture-net record:
        "palm_text": "LIFE LINE: long, deep, curving toward the wrist...",
        "left_palm_description": "full raw vision description text",
        "image_bytes": b"\x89PNG\r\n...",
        "hand_detail": "raw hand_detail free text",
    }
    capture_net.record("ai_decision", "test", payload, reading_id="r5")

    lines = _read_lines(out_path)
    assert len(lines) == 1
    entry = json.loads(lines[0])
    forbidden_keys = {"palm_text", "left_palm_description", "image_bytes", "hand_detail"}
    assert forbidden_keys.isdisjoint(entry.keys())
    raw_line = lines[0]
    assert "LIFE LINE" not in raw_line
    assert "PNG" not in raw_line


def test_map_fallback_audits_ignores_unmapped_and_keeps_mapped(tmp_path, monkeypatch):
    out_path = tmp_path / "capture_net" / "failures.jsonl"
    monkeypatch.setattr(capture_net, "_CAPTURE_NET_PATH", out_path)

    audits = [
        {"raw_verb": "touches", "disposition": "already_resolved_no_llm_needed"},
        {"raw_verb": "fuses", "disposition": "llm_unclear", "llm_canonical_choice": None, "final_token": None},
        {"raw_verb": "converges", "disposition": "hallucination", "llm_canonical_choice": "nonsense_verb", "final_token": None},
    ]
    capture_net.map_fallback_audits(audits, reading_id="r6")

    lines = _read_lines(out_path)
    assert len(lines) == 2  # the already_resolved one is skipped
    triggers = {json.loads(line)["trigger"] for line in lines}
    assert triggers == {"silence", "wrong_source"}


# ═══ S119 STEP 4: dropped-rule producer (dormant tripwire) ═══════════════


def _rule_claim(**overrides):
    """A rule-sourced Claim, built through the real constructor."""
    from agent.interpretive.claim_extraction import Claim

    kwargs = dict(
        claim_id="C1", feature="fate line", rule_id="FT_003", source_page=103,
        source_quote="When the line of fate rises from the wrist...",
        claim_text="A fate line rising from the wrist is a sign of good fortune.",
        valence="supports", condition_text=None,
        observation_basis="Line of Fate Slope=straight",
        excluded_from_voice=False, exclusion_reason=None,
    )
    kwargs.update(overrides)
    return Claim.by_rule(**kwargs)


def test_dropped_rule_ids_producer_writes_one_wrong_source_record_per_rule(
    tmp_path, monkeypatch
):
    """HARDEST CASE for this producer: the regression it exists to catch.
    A non-empty dropped_rule_ids is exactly the pre-Step-2 state (13 of 99
    live rules fired, survived, then lost their claim to chunk
    resolution) -- it must land in the durable sink as a first-class
    event, not scroll past as a stdout WARNING."""
    out_path = tmp_path / "capture_net" / "failures.jsonl"
    monkeypatch.setattr(capture_net, "_CAPTURE_NET_PATH", out_path)

    capture_net.record_dropped_rules(["FT_003", "FT_004"], "r-drop")

    entries = [json.loads(line) for line in _read_lines(out_path)]
    assert len(entries) == 2
    assert [e["rule_id"] for e in entries] == ["FT_003", "FT_004"]
    for entry in entries:
        assert entry["trigger"] == "wrong_source"
        assert entry["producer"] == "palm_reading_rules_engine"
        assert entry["disposition"] == "dropped_rule_no_citation"
        assert entry["reading_id"] == "r-drop"


def test_dropped_rule_trigger_is_already_known_to_the_digest():
    """No new trigger category was invented: capture_net_digest derives its
    _KNOWN_TRIGGERS from _DISPOSITION_TO_TRIGGER.values(), and the producer
    reuses one of those, so the digest needed no edit."""
    from agent.interpretive import capture_net_digest

    assert "wrong_source" in capture_net_digest._KNOWN_TRIGGERS


@pytest.mark.parametrize("empty", [[], None, ()])
def test_dropped_rule_producer_is_dormant_on_the_real_state(
    tmp_path, monkeypatch, empty
):
    """DORMANT BY CONSTRUCTION. Since Step 2 nothing can be dropped for
    citation reasons, so the real input is always empty and a clean run
    writes nothing -- same silent-clean-run contract map_fallback_audits
    already has."""
    out_path = tmp_path / "capture_net" / "failures.jsonl"
    monkeypatch.setattr(capture_net, "_CAPTURE_NET_PATH", out_path)

    capture_net.record_dropped_rules(empty, "r-clean")

    assert _read_lines(out_path) == []


def test_dropped_rule_producer_never_raises_on_an_unwritable_path(
    tmp_path, monkeypatch, caplog
):
    """Same fail-safe contract as record(): a capture failure must never
    break a reading."""
    blocker = tmp_path / "blocked"
    blocker.write_text("i am a file, not a directory", encoding="utf-8")
    monkeypatch.setattr(capture_net, "_CAPTURE_NET_PATH", blocker / "sub" / "f.jsonl")

    with caplog.at_level(logging.WARNING, logger="agent.interpretive.capture_net"):
        assert capture_net.record_dropped_rules(["FT_003"], "r1") is None


def test_no_source_quote_can_reach_a_capture_record(tmp_path, monkeypatch):
    """CONTAINMENT, same discipline as the palm-text test above: the
    _PAYLOAD_KEYS allow-list is the mechanism. Even a payload that
    explicitly carries source_quote (and other book prose) cannot get it
    into a record, because the key is not on the list."""
    out_path = tmp_path / "capture_net" / "failures.jsonl"
    monkeypatch.setattr(capture_net, "_CAPTURE_NET_PATH", out_path)

    quote = "ZZQUOTEZZ When the line of fate rises from the wrist"
    capture_net.record(
        trigger="wrong_source", producer="palm_reading_rules_engine",
        payload={
            "rule_id": "FT_003", "source_page": 103,
            "source_quote": quote, "claim_text": quote, "raw_prose": quote,
        },
        reading_id="r-quote",
    )

    raw = out_path.read_text(encoding="utf-8")
    assert quote not in raw
    entry = json.loads(raw.strip())
    assert entry["rule_id"] == "FT_003"
    assert entry["source_page"] == 103
    assert "source_quote" not in entry
    assert "claim_text" not in entry
    assert "source_quote" not in capture_net._PAYLOAD_KEYS
