"""
tests/interpretive/test_gate_rule_citations.py

Tests for scripts/gate_rule_citations.py (S114) -- the gate previously
had ZERO test coverage. Hardest-case first: the printed-page-vs-page_ref
offset tolerance is the exact bug this task fixes, so it leads.

Uses the REAL corpus (data/cheiro/cheiro_clean_v1.json, 310 chunks) --
small enough to load once per test module with no performance concern,
and testing against synthetic corpus text would not actually prove the
offset-tolerance fix works against the real book.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.gate_rule_citations import (
    ROOT,
    DEFAULT_CORPUS_PATH,
    build_full_corpus_text,
    build_page_text_index,
    classify_rule_citation,
    load_rules_from_file,
    tokens_of,
)


@pytest.fixture(scope="module")
def corpus_index():
    """Loads the REAL corpus once for the whole module -- 310 chunks,
    negligible cost, and only the real book proves the offset-tolerance
    fix actually works against real data."""
    chunks = json.loads(DEFAULT_CORPUS_PATH.read_text(encoding="utf-8"))
    page_text = build_page_text_index(chunks)
    page_token_sets = {p: set(tokens_of(t)) for p, t in page_text.items()}
    full_text = build_full_corpus_text(page_text)
    full_token_set = set(tokens_of(full_text))
    return page_text, page_token_sets, full_text, full_token_set


def _rule(source_page, source_quote, rule_id="TEST_RULE"):
    return {"rule_id": rule_id, "source_page": source_page, "source_quote": source_quote}


# ─── HARDEST CASE FIRST: the printed-page-vs-page_ref offset tolerance ────


def test_offset_tolerance_ft007_quote_at_offset_page_is_clean(corpus_index):
    """THE EXACT BUG THIS TASK FIXES: FT_007's real quote, with its real
    source_page (104, PRINTED page) -- the corpus's own page_ref for this
    text is 164, a +60 offset. The old script matched source_page
    directly against page_ref (+/-1 only) and would have called this
    UNMATCHED. The new whole-corpus anchor search must find it and
    report CLEAN, with matched_pages including 164 and an implied offset
    of +60."""
    page_text, page_token_sets, full_text, full_token_set = corpus_index
    rule = _rule(
        104,
        "When the line of fate is abruptly stopped by the line of heart, success will be ruined through the affections;",
        rule_id="FT_007",
    )
    result = classify_rule_citation(rule, page_text, page_token_sets, full_text, full_token_set)
    assert result["status"] == "CLEAN"
    assert 164 in result["matched_pages"]
    assert 60 in result["implied_offsets"]


def test_offset_tolerance_ft008_quote_at_offset_page_is_clean(corpus_index):
    """Symmetric proof, FT_008's own quote (same page_ref 164, same
    passage) -- confirms the offset tolerance isn't a fluke of one
    specific quote."""
    page_text, page_token_sets, full_text, full_token_set = corpus_index
    rule = _rule(
        104,
        "When stopped by the line of head, it foretells that success will be thwarted by some stupidity or blunder of the head.",
        rule_id="FT_008",
    )
    result = classify_rule_citation(rule, page_text, page_token_sets, full_text, full_token_set)
    assert result["status"] == "CLEAN"
    assert 164 in result["matched_pages"]
    assert 60 in result["implied_offsets"]


# ─── Fabrication: the gate must still bite ─────────────────────────────


def test_fabricated_quote_not_in_corpus_is_not_found_anywhere(corpus_index):
    """A quote that does not exist anywhere in the corpus -- proves the
    whole-corpus search doesn't degrade into blanket permissiveness just
    because it searches every page instead of one."""
    page_text, page_token_sets, full_text, full_token_set = corpus_index
    rule = _rule(
        104,
        "The purple elephant of destiny dances upon the seventh mountain of prosperity and everlasting joy.",
        rule_id="FAKE_FABRICATED",
    )
    result = classify_rule_citation(rule, page_text, page_token_sets, full_text, full_token_set)
    assert result["status"] == "NOT_FOUND_ANYWHERE"
    assert result["matched_pages"] == []


# ─── GENERATOR_PLACEHOLDER / UNCITED ────────────────────────────────────


def test_tilde_prefixed_quote_is_generator_placeholder(corpus_index):
    page_text, page_token_sets, full_text, full_token_set = corpus_index
    rule = _rule(104, "~ this is a generator placeholder, not a real quote")
    result = classify_rule_citation(rule, page_text, page_token_sets, full_text, full_token_set)
    assert result["status"] == "GENERATOR_PLACEHOLDER"


def test_missing_quote_is_uncited(corpus_index):
    page_text, page_token_sets, full_text, full_token_set = corpus_index
    rule = _rule(104, "")
    result = classify_rule_citation(rule, page_text, page_token_sets, full_text, full_token_set)
    assert result["status"] == "UNCITED"

    rule_no_key = {"rule_id": "NO_QUOTE_KEY", "source_page": 104}
    result2 = classify_rule_citation(rule_no_key, page_text, page_token_sets, full_text, full_token_set)
    assert result2["status"] == "UNCITED"


# ─── Short quotes (<6 tokens): substring-only, no overlap score ────────


def test_short_quote_present_verbatim_is_clean_via_substring(corpus_index):
    """A short (<6-token) quote must still resolve via substring match --
    the overlap-score test is scope-guarded to >=6 tokens, but substring
    matching has no length floor."""
    page_text, page_token_sets, full_text, full_token_set = corpus_index
    # "success will be ruined" is a genuine short (4-token) fragment of
    # FT_007's real, corpus-anchored sentence.
    rule = _rule(104, "success will be ruined", rule_id="SHORT_CLEAN")
    result = classify_rule_citation(rule, page_text, page_token_sets, full_text, full_token_set)
    assert result["status"] == "CLEAN"
    assert result["score"] is None  # too short for overlap scoring -- substring-only, no score logged


def test_short_quote_absent_is_not_found(corpus_index):
    page_text, page_token_sets, full_text, full_token_set = corpus_index
    rule = _rule(104, "purple elephant dances", rule_id="SHORT_FABRICATED")
    result = classify_rule_citation(rule, page_text, page_token_sets, full_text, full_token_set)
    assert result["status"] == "NOT_FOUND_ANYWHERE"
    assert result["score"] is None  # too short for overlap scoring


# ─── Report-only guard: no data/palm_rules/ file is ever written ───────


def test_report_only_no_rule_file_is_written(tmp_path, monkeypatch):
    """Runs the real main() end-to-end (via subprocess, the actual CLI
    entry point) and asserts every data/palm_rules/*.json file's mtime
    and content hash are UNCHANGED before/after -- the report-only
    guarantee this task's own commit gate requires."""
    import hashlib
    import subprocess
    import sys

    rules_dir = ROOT / "data" / "palm_rules"
    rule_files = sorted(rules_dir.glob("palm_rules_*.json"))
    assert rule_files, "no rule files found -- test setup itself is broken"

    def _hash(path: Path) -> str:
        return hashlib.sha256(path.read_bytes()).hexdigest()

    before = {p: (_hash(p), p.stat().st_mtime) for p in rule_files}

    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "gate_rule_citations.py")],
        cwd=str(ROOT), capture_output=True, text=True, timeout=120,
    )
    assert result.returncode == 0, f"gate script exited non-zero: {result.stderr}"

    after = {p: (_hash(p), p.stat().st_mtime) for p in rule_files}
    assert before == after, "gate_rule_citations.py modified a data/palm_rules/ rule file -- must be report-only"


# ─── Sanity: rule-file loading is section-generic, not per-file-hardcoded ──


def test_load_rules_from_file_finds_validated_candidates_and_all_parked_sections():
    """head_heart's parked section is named differently
    (parked_pending_relation_target) from fate/life's (parked_pending) --
    proves the generic parked_* prefix match picks up both shapes."""
    fate_path = ROOT / "data" / "palm_rules" / "palm_rules_fate_line_v1.json"
    head_heart_path = ROOT / "data" / "palm_rules" / "palm_rules_head_heart_v1.json"

    fate_live, fate_parked = load_rules_from_file(fate_path)
    assert len(fate_live) > 0
    assert len(fate_parked) > 0  # palm_rules_fate_line_v1.json's own "parked_pending"

    hh_live, hh_parked = load_rules_from_file(head_heart_path)
    assert len(hh_live) > 0
    assert len(hh_parked) > 0  # palm_rules_head_heart_v1.json's own "parked_pending_relation_target"


def test_load_rules_from_file_skips_retired_and_non_list_sections():
    """life_line's file has a top-level "meta" key (not a rule list) and
    a "retired_superseded" section -- neither should ever appear in
    live/parked."""
    life_path = ROOT / "data" / "palm_rules" / "palm_rules_life_line_v1.json"
    raw = json.loads(life_path.read_text(encoding="utf-8"))
    assert "meta" in raw  # confirms the fixture actually exercises this case
    assert "retired_superseded" in raw

    live, parked = load_rules_from_file(life_path)
    live_ids = {r["rule_id"] for r in live}
    parked_ids = {r["rule_id"] for r in parked}
    retired_ids = {r["rule_id"] for r in raw["retired_superseded"]}
    assert not (live_ids & retired_ids)
    assert not (parked_ids & retired_ids)
