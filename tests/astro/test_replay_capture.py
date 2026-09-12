"""Tests for scripts/replay_capture.py.

The point of a regression tool is that it FAILS when something regresses. Most
of these tests therefore break something on purpose and assert the replay
notices -- a harness that only ever prints "no differences" is worthless.

The fixture is a real, frozen gpt-5 run (Sulabh's chart, 2026-09-12): 2 turns,
4 claims, 0 ghost citations. Do not regenerate it casually -- it costs a live
run, and its value is that it never changes.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts import replay_capture as RC

FIXTURE = (Path(__file__).resolve().parents[1]
           / "fixtures" / "qa_captures" / "s129_live_gpt5_20260912T160015Z.md")


@pytest.fixture(scope="module")
def turns():
    return RC.parse_capture(FIXTURE)


# ── parsing the real capture ───────────────────────────────────────────────

def test_the_frozen_fixture_exists_and_is_readable():
    assert FIXTURE.exists(), (
        "the frozen live-run fixture is missing; it cannot be recreated "
        "without spending a real dogfood run")


def test_parses_both_turns_of_the_real_run(turns):
    assert len(turns) == 2
    assert "career" in turns[0].question
    assert "married" in turns[1].question


def test_each_turn_carries_what_replay_needs(turns):
    for t in turns:
        assert t.chart_facts.get("lord_house_map"), f"turn {t.index}: no lord map"
        assert t.unit_ids, f"turn {t.index}: no unit_ids -- payload cannot rebuild"
        json.loads(t.interpreter_raw)          # must be the real model JSON


def test_the_fixture_chart_is_sulabhs_oracle_verified_chart(turns):
    """Guards against someone swapping the fixture for a different chart and
    silently changing what every replay asserts."""
    lm = {int(k): int(v) for k, v in turns[0].chart_facts["lord_house_map"].items()}
    assert lm == {1: 5, 2: 1, 3: 1, 4: 5, 5: 2, 6: 6,
                  7: 4, 8: 12, 9: 4, 10: 4, 11: 6, 12: 2}
    assert turns[0].chart_facts["ascendant_sign"] == "Sagittarius"


# ── the replay reproduces the captured run ─────────────────────────────────

def test_replaying_the_real_run_reproduces_its_claims_exactly():
    """THE regression test: today's downstream code, given Friday's real model
    output, must still produce Friday's answer."""
    out = RC.replay_file(FIXTURE)
    assert out["turns_replayed"] == 2
    t1 = out["results"][0]
    assert len(t1["kept"]) == 4
    assert t1["dropped"] == []
    assert t1["ghost_citations"] == []
    assert t1["payload_segments_kept"] > 100
    t2 = out["results"][1]
    assert t2["kept"] == [] and t2["ghost_citations"] == []


def test_the_only_differences_are_additive_new_stats_keys():
    """If a replay ever reports a changed KEPT or DROPPED claim, a code change
    has altered a real answer and needs a human ruling before it ships."""
    out = RC.replay_file(FIXTURE)
    for idx, lines in out["diffs"].items():
        for line in lines:
            assert line.startswith(("NEW stats keys", "user answer NOT COMPARED")), (
                f"turn {idx} changed a real answer, not just diagnostics: {line}")


def test_replay_makes_no_api_call(monkeypatch):
    """The whole premise. If anything reaches OpenAI, fail loudly."""
    import agent.astro.interpreter as I

    def _boom(*a, **k):
        raise AssertionError("replay attempted a live model call")
    monkeypatch.setattr(I, "_default_llm", _boom)
    out = RC.replay_file(FIXTURE)
    assert out["turns_replayed"] == 2


# ── it must CATCH a regression, not just pass ──────────────────────────────

def test_a_changed_kept_claim_is_reported(turns):
    """Simulate a gate change that silently drops a claim."""
    t = turns[0]
    now = RC.replay_turn(t)
    now["kept"] = now["kept"][:-1]               # pretend the gate dropped one
    diff = RC.diff_turn(t, now)
    assert any("KEPT CLAIMS CHANGED" in d for d in diff)
    assert any("no longer kept" in d for d in diff)


def test_a_newly_dropped_claim_is_reported(turns):
    t = turns[0]
    now = RC.replay_turn(t)
    now["dropped"] = [now["kept"][0]]
    diff = RC.diff_turn(t, now)
    assert any("newly dropped" in d for d in diff)


def test_a_changed_user_facing_answer_is_reported(turns):
    """Only meaningful for a capture that stored the answer_view output. The
    frozen fixture predates that, so this builds the case explicitly."""
    t = turns[0]
    now = RC.replay_turn(t)
    modern = RC.CapturedTurn(
        index=t.index, question=t.question, chart_facts=t.chart_facts,
        unit_ids=t.unit_ids, interpreter_raw=t.interpreter_raw,
        captured_kept=t.captured_kept, captured_dropped=t.captured_dropped,
        captured_stats=t.captured_stats,
        captured_user_answer=now["user_answer"], user_answer_source="answer_view")
    assert not [d for d in RC.diff_turn(modern, now)
                if "USER-FACING" in d], "identical answers must not diff"
    now["user_answer"] = "something a renderer change produced"
    assert any("USER-FACING ANSWER CHANGED" in d for d in RC.diff_turn(modern, now))


def test_a_legacy_capture_says_the_answer_was_not_compared(turns):
    """The frozen fixture stored the PIPELINE render under a heading claiming
    it was the user's view (the S129 mislabel). Comparing against it would
    report a spurious difference on every turn, so the replay must decline to
    compare and say why."""
    t = turns[0]
    assert t.user_answer_source == "legacy_pipeline_render"
    assert any("NOT COMPARED" in d for d in RC.diff_turn(t, RC.replay_turn(t)))


def test_a_changed_verdict_count_is_reported(turns):
    t = turns[0]
    now = RC.replay_turn(t)
    now["stats"] = dict(now["stats"], applicable=99)
    assert any("stat applicable" in d for d in RC.diff_turn(t, now))


def test_an_identical_replay_reports_no_claim_differences(turns):
    """Control for the four tests above -- they must not fire on a clean run."""
    t = turns[0]
    diff = RC.diff_turn(t, RC.replay_turn(t))
    assert not [d for d in diff
                if not d.startswith(("NEW stats keys", "user answer NOT COMPARED"))]


# ── the promotion metric ───────────────────────────────────────────────────

def test_advisory_rollup_counts_real_claims():
    out = RC.replay_file(FIXTURE)
    roll = RC._advisory_rollup(out["results"])
    assert roll["claims"] == 4
    # All four are lord-shape; the planet reader correctly judges none of them.
    # ZERO here is an ABSENCE OF EVIDENCE, not evidence of safety -- the block
    # carried no planet facts when this ran, so no planet claim could exist.
    assert roll["advisory_undetermined"] == 4
    assert roll["would_drop_a_kept_claim"] == 0
    assert roll["disagreements"] == []


# ── failure posture ────────────────────────────────────────────────────────

def test_a_capture_without_unit_ids_fails_loudly(tmp_path):
    """Captures written before `unit_ids` existed are not replayable, and must
    say so rather than replaying against an empty payload."""
    p = tmp_path / "old.md"
    p.write_text(
        "# hdr\n\n## TURN 2026-01-01\n\n"
        "### question\n```\nq\n```\n\n"
        "### chart_facts\n```json\n{}\n```\n\n"
        "### selection + payload (Stages 2-3)\n```json\n{}\n```\n\n"
        "### interpreter raw response\n```\n{\"claims\": []}\n```\n",
        encoding="utf-8")
    with pytest.raises(RC.ReplayError, match="unit_ids"):
        RC.parse_capture(p)


def test_a_turn_with_no_raw_response_is_skipped_not_crashed(tmp_path):
    """A capability-gate refusal never reached the interpreter."""
    p = tmp_path / "refusal.md"
    p.write_text("# hdr\n\n## TURN 2026-01-01\n\n### question\n```\nwhen?\n```\n",
                 encoding="utf-8")
    assert RC.parse_capture(p) == []


def test_missing_capture_file_returns_an_error_code():
    assert RC.main(["/nonexistent/capture.md"]) == 2


def test_cli_runs_on_the_fixture(capsys):
    assert RC.main([str(FIXTURE)]) == 0
    out = capsys.readouterr().out
    assert "turns replayed: 2" in out
    assert "WOULD DROP A KEPT CLAIM" in out


def test_cli_json_mode_is_valid_json(capsys):
    assert RC.main([str(FIXTURE), "--json"]) == 0
    json.loads(capsys.readouterr().out)
