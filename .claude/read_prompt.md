# Read Prompt

#Paste your instructions here. Then tell Claude: "Read .claude/read_prompt.md and execute"


In agent/palm_processor.py, validate_palm_image():

1. Remove all mention of {slot} from the message sent to GPT-4o for
   hand determination — the model should determine "hand" purely from
   image content, with no slot context at all.
2. Update _SYSTEM_PROMPT's JSON schema: GPT returns only "hand",
   "quality", "issues" — drop "matches_slot" from what GPT returns
   entirely.
3. In Python, after receiving "hand" from GPT, compute
   matches_slot = (hand == slot) deterministically — slot is the
   function's existing parameter, no new input needed.
4. Keep all existing hard_reject/warn logic, just sourced from the
   Python-computed matches_slot instead of GPT's.

In tests/manual/slot_bias_check.py (keep as throwaway, don't add to
suite): re-run with the new code — call validate_palm_image(same
image bytes, "left") and validate_palm_image(same bytes, "right") —
this time "hand" should be IDENTICAL in both calls (slot-independent).
Report the new hand value for palm_left_test.jpg.

Then, in tests/test_palm_endtoend.py, replace test_left_palm_validates
and test_right_palm_validates with a single new test:
test_hand_detection_is_slot_independent — calls validate_palm_image on
the same image with both slot="left" and slot="right", asserts "hand"
is identical in both results. This is now the regression guard against
this exact bug recurring.

Run full test suite, report pass/fail count.