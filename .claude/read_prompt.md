# Read Prompt

#Paste your instructions here. Then tell Claude: "Read .claude/read_prompt.md and execute"

Make exactly ONE surgical edit to CLAUDE.md, then run the full 
test suite once.

EDIT — CLAUDE.md

Find this exact line:
**Session 10 COMPLETE.** Next: Session 11 — _PALM_TOPICS keyword audit + any new tasks.

Replace with:
**Session 11 COMPLETE.** Next: Session 12 — multi-source retrieval 
validation + _PALM_TOPICS keyword audit (carried forward).

Also update SESSION_LOG.md — append this entry at the end of the 
existing log entries:

- Session 11 (2026-05-29): prompt_builder.py — CQ behaviour block 
  added (missing context → ask one clarifying question); 
  needs_disclaimer() guard added (suppress on CQ responses, <80 words + 
  ends with ?); cross-verification block added (mandatory kundali × palm 
  synthesis when both present); query_engine.py — multi_source_search() 
  added (2 chunks × 5 books, dedup by chunk_id, score-sorted, 
  per-book try/except); astrologer.py — multi_source param wired to 
  ask(); test_palm_quality.py — test_no_context_no_hallucination updated 
  with CQ guard; SYSTEM_PROMPT ~580-600 words; 40/40 tests passing — 
  COMPLETE. Known debt: _PALM_TOPICS keyword audit still pending.

After both edits, run the full test suite ONCE and report:
- Total pass/fail count
- Any failures with exact assertion errors
- Nothing else