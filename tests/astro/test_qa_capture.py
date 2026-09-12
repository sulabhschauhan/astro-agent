"""Tests for agent/astro/qa_capture.py.

The two things that matter: (1) cited verse text is written IN FULL -- a
truncated capture is what produced two wrong fidelity verdicts on the same
Raja Yoga citation; (2) capture failure never costs the user their answer.
"""
from __future__ import annotations

import importlib

import pytest

from agent.astro import qa_capture as QC


@pytest.fixture(autouse=True)
def _isolated_capture_dir(tmp_path, monkeypatch):
    """Point the module at a temp dir and reset its per-process path."""
    monkeypatch.setattr(QC, "_CAPTURE_DIR", tmp_path / "qa_capture")
    monkeypatch.setattr(QC, "_SESSION_PATH", None)
    monkeypatch.delenv("ASTRO_QA_CAPTURE", raising=False)
    yield


_LONG_VERSE = ("10. As far as Rahu and Ketu are concerned... " + ("filler " * 900)
               + "11-12. ANGULAR AND TRINAL LORDSHIPS : If there be an exchange between an "
                 "angular lord and a trinal lord, or if these two lords join in an angle or "
                 "in a trine... One born in such a yoga will become a king and be famous")


def _result(**kw):
    base = {
        "answer": "- You will gain through patronage.",
        "kept_claims": [{"statement": "With the 10th lord in the 4th, you gain.",
                         "segment_ids": ["ch34_s011"]}],
        "dropped_claims": [], "silent_on": [], "declined": [], "dropped_domains": [],
        "ghost_citations": [], "gate_stats": {"claims_in": 1}, "usage": {"prompt_tokens": 80882},
        "tokens": 49090, "model": "gpt-5", "refused": False,
        "trace": {
            "timings": {"plan": 1.2, "interpreter": 31.4},
            "payload": {"segments": [{"segment_id": "ch34_s011", "text": _LONG_VERSE,
                                      "kept": True}], "units": []},
            "unit_ids": ["bphs1_ch34"], "estimated_real_tokens": 83453,
            "interpreter_raw": '{"claims": []}',
        },
    }
    base.update(kw)
    return base


# ── the load-bearing test ──────────────────────────────────────────────────

def test_cited_verse_text_is_written_in_full_never_truncated():
    path = QC.capture_turn("What about my career?", _result(), {"ascendant_sign": "Sagittarius"})
    assert path is not None
    body = path.read_text(encoding="utf-8")
    assert _LONG_VERSE in body, "the capture must hold the WHOLE segment, not a prefix"
    assert "ANGULAR AND TRINAL LORDSHIPS" in body
    assert f"{len(_LONG_VERSE):,} chars" in body, "the length must be stated so truncation is visible"


def test_a_cited_id_absent_from_the_payload_is_flagged_not_silently_skipped():
    r = _result(kept_claims=[{"statement": "x", "segment_ids": ["ch99_s001"]}])
    body = QC.capture_turn("q", r, {}).read_text(encoding="utf-8")
    assert "ch99_s001" in body
    assert "NOT IN PAYLOAD" in body


# ── content ────────────────────────────────────────────────────────────────

def test_turn_records_question_timings_usage_and_the_rendered_answer():
    body = QC.capture_turn("Will I travel?", _result(), {"ascendant_sign": "Leo"}).read_text(encoding="utf-8")
    for expected in ("Will I travel?", "interpreter", "31.4", "80882", "gpt-5", "Leo"):
        assert expected in body, expected
    assert "**total**" in body


# ── the three S129 labelling defects, each pinned ──────────────────────────

def test_user_answer_is_recorded_separately_from_the_internal_render():
    """DEFECT 1 (S129): the capture labelled the pipeline's internal render
    'what the user saw'. They are different strings and both must appear,
    under labels that cannot be confused."""
    r = _result(answer="- internal render [ch34_s011]\n\nNot addressed: lots of ids")
    body = QC.capture_turn("q", r, {}, user_answer="- You will gain.\n\n*Source: BPHS*").read_text(encoding="utf-8")
    assert "### what the user actually saw (answer_view)" in body
    assert "### pipeline internal render (NOT shown to the user)" in body
    assert "- You will gain." in body
    assert "Not addressed: lots of ids" in body           # kept, but correctly labelled
    assert body.index("what the user actually saw") < body.index("pipeline internal render")


def test_missing_user_answer_says_so_rather_than_mislabelling():
    body = QC.capture_turn("q", _result(), {}).read_text(encoding="utf-8")
    assert "not supplied by the caller" in body


def test_both_plans_are_recorded_pre_and_post_gate():
    """DEFECT 2 (S129): only the post-gate plan was captured, so the gate's
    narrowing was invisible."""
    r = _result()
    r["trace"]["plan_before_gate"] = {"domains": ["marriage", "timing_dasha"],
                                      "time_scope": "future"}
    r["plan"] = None
    body = QC.capture_turn("when?", r, {}).read_text(encoding="utf-8")
    assert "as the PLANNER produced it" in body
    assert "AFTER the capability gate" in body
    assert "timing_dasha" in body


def test_gate_verdict_and_empty_answer_are_separate_fields():
    """DEFECT 3 (S129): a derived 'no claims' value was reported as the gate's
    own refuse_outright verdict. They are different events."""
    r = _result(kept_claims=[], refused=True)
    r["trace"]["gate_refused_outright"] = False       # gate let it through
    body = QC.capture_turn("q", r, {}).read_text(encoding="utf-8")
    assert '"gate_refused_outright": false' in body.lower()
    assert '"answer_is_empty": true' in body.lower()


def test_ghost_citations_are_recorded():
    body = QC.capture_turn("q", _result(ghost_citations=["ch77_s001", "ch88_s002"]), {}).read_text(encoding="utf-8")
    assert "ch77_s001" in body and "ch88_s002" in body


def test_capability_gate_decline_is_recorded():
    r = _result(declined=[("dasha_timing", "I can't tell you when.")],
                dropped_domains=["timing_dasha"])
    body = QC.capture_turn("when?", r, {}).read_text(encoding="utf-8")
    assert "dasha_timing" in body and "timing_dasha" in body


# ── file-per-launch semantics ──────────────────────────────────────────────

def test_turns_append_to_one_file_for_the_process():
    p1 = QC.capture_turn("q1", _result(), {})
    p2 = QC.capture_turn("q2", _result(), {})
    assert p1 == p2
    body = p1.read_text(encoding="utf-8")
    assert body.count("## TURN") == 2
    assert "q1" in body and "q2" in body


def test_a_new_process_starts_a_new_file(monkeypatch):
    first = QC.capture_turn("q1", _result(), {})
    monkeypatch.setattr(QC, "_SESSION_PATH", None)   # simulate a fresh launch
    import time
    time.sleep(1.05)                                  # timestamps are per-second
    second = QC.capture_turn("q2", _result(), {})
    assert second != first
    assert "q1" not in second.read_text(encoding="utf-8")


# ── switch + failure posture ───────────────────────────────────────────────

@pytest.mark.parametrize("val", ["0", "false", "no", "off", "OFF"])
def test_disabled_by_env(monkeypatch, val):
    monkeypatch.setenv("ASTRO_QA_CAPTURE", val)
    assert QC.capture_enabled() is False
    assert QC.capture_turn("q", _result(), {}) is None


def test_enabled_by_default():
    assert QC.capture_enabled() is True


def test_capture_failure_returns_none_and_never_raises(monkeypatch):
    """Diagnostics must never cost the user an answer."""
    def _boom(*a, **k):
        raise OSError("disk full")
    monkeypatch.setattr(QC.Path, "open", _boom)
    assert QC.capture_turn("q", _result(), {}) is None


def test_unserialisable_trace_does_not_raise():
    r = _result()
    r["usage"] = {"weird": object()}
    assert QC.capture_turn("q", r, {}) is not None


def test_missing_trace_key_is_tolerated():
    r = _result()
    del r["trace"]
    body = QC.capture_turn("q", r, {}).read_text(encoding="utf-8")
    assert "## TURN" in body


# ── the error path ─────────────────────────────────────────────────────────

def test_capture_error_records_a_failed_turn():
    try:
        raise ValueError("interpreter did not return valid JSON")
    except ValueError as e:
        path = QC.capture_error("what about my career?", e)
    body = path.read_text(encoding="utf-8")
    assert "FAILED" in body
    assert "what about my career?" in body
    assert "interpreter did not return valid JSON" in body
