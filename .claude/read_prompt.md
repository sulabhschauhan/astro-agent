# Read Prompt

#Paste your instructions here. Then tell Claude: "Read .claude/read_prompt.md and execute"


Rewrite the following four test files in full. Each is a complete
replacement — the old content is entirely obsolete.

FILE 1 — tests/test_nudge_endtoend.py
Rename the file's purpose in the docstring: these are now integration
tests for context_classifier.classify() using the new signature.
Import classify from agent.context_classifier and ContextBundle from
agent.context_bundle. No imports of classify_context or route anywhere.

Write five tests using real GPT-4o-mini calls:
  1. Palmistry question with no palm in bundle — hard_block True, blocked_on "palm"
  2. Time-bound question with no own_pdf in bundle — hard_block True, blocked_on "own_pdf"
  3. Palmistry question with palm present in bundle — hard_block False, proceed True
  4. Time-bound question with own_pdf present in bundle — hard_block False, proceed True
  5. General vedic question with empty bundle — hard_block False, retrieval_profile "vedic"

FILE 2 — tests/test_prompt_builder.py
Rename the file's purpose in the docstring: these are now tests for
the new build_prompts() signature with spouse_pdf and hand_detail.
No imports of route or classify. All tests are deterministic — no GPT calls.

Write four tests:
  1. spouse_pdf slot renders correctly — pass spouse_pdf string and
     context_order containing "spouse_pdf", assert "Spouse AstroSage" in user message
  2. hand_detail slot renders correctly — pass hand_detail string and
     context_order containing "hand_detail", assert "Hand Detail Analysis" in user message
  3. Dual palm synthesis still works — palm_left and palm_right both passed,
     assert "Synthesise both" in user message
  4. Nudge block is gone — pass no palm, assert the old nudge string
     "[If you have a palm description available" is NOT in user message
     (this is a regression guard — confirms PALM_TOPICS removal is clean)

FILE 3 — tests/test_context_integration.py
Rename the file's purpose in the docstring: these are now tests for
build_prompts() rendering with classifier-style context_order inputs.
No imports of route. No GPT calls. Call build_prompts() directly with
hardcoded context_order lists that mirror what classify() would return.

Write four tests covering:
  1. Vedic-only context_order — kundali + rag, no pdf/palm blocks in output
  2. Palmistry context_order — palm_left + palm_right + rag, assert LEFT HAND and RIGHT HAND present
  3. own_pdf context_order — own_pdf slot renders AstroSage Annual Report header
  4. Full context_order with all slots — kundali + own_pdf + spouse_pdf +
     palm_left + palm_right + hand_detail + rag — assert all six context
     headers present in user message

FILE 4 — tests/test_palm_quality.py
Surgical edits only — do not rewrite. Update the two ask() call sites
to add spouse_pdf=None and hand_detail=None explicitly. No other changes.

After writing all four files, run the full test suite with pytest and
report the pass/fail count. Do not proceed to fix failures — report them.