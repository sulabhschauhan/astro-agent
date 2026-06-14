# Read Prompt

#Paste your instructions here. Then tell Claude: "Read .claude/read_prompt.md and execute"


In agent/context_classifier.py, the _FAIL_OPEN dict hardcodes
context_order to ["kundali", "rag"]. If the classify() API call fails
for a user who has uploaded own_pdf, spouse_pdf, palm_left, palm_right,
or hand_detail, that context is silently dropped on fallback — the user
gets a generic vedic-profile answer with no indication their uploads
were ignored.

Fix: on API failure, build context_order dynamically from what's
actually present in the ContextBundle passed into classify() — include
kundali first if present, then own_pdf, spouse_pdf, palm_left,
palm_right, hand_detail (whichever the bundle has), then rag last.
retrieval_profile on fallback should be "palmistry" if palm_left or
palm_right is present and kundali/own_pdf are not, otherwise "vedic".
needs_required and hard_block stay as-is (False/None) — fail-open must
never hard-block.

Constraints:
- Surgical edit to agent/context_classifier.py only
- _FAIL_OPEN can become a small helper function computed at the
  exception site using the bundle already in scope — do not restructure
  classify()'s overall control flow
- Do not touch _VALID_* whitelists or the LLM-facing classification
  prompt
- Add a test: simulate classify() raising an exception with a bundle
  containing kundali + palm_left + palm_right (no own_pdf) — assert
  fallback context_order is ["kundali", "palm_left", "palm_right", "rag"]
  and retrieval_profile is sensible for that case
- Run the full test suite after the change and report pass/fail count —
  do not fix unrelated failures, just report them