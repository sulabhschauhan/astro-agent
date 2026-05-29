# Read Prompt

#Paste your instructions here. Then tell Claude: "Read .claude/read_prompt.md and execute"

Read agent/prompt_builder.py in full before making any changes.

Make exactly two surgical edits — no other changes:

EDIT 1 — Add a new section to SYSTEM_PROMPT.
Insert it immediately after the "## Kundali / Dasha queries" section 
and before the "## Context synthesis" section.

Section to insert (exact text):

## When personal context is missing
- If a question requires personal details (birth date, birth place, life 
  situation) and no kundali, PDF, or palm context is provided, ask ONE 
  clarifying question — concise, direct, no preamble.
- Ask only what you need most to answer. Do not bundle multiple questions.
- After the user answers, incorporate it into the reading immediately.
- Never say "I cannot engage in dialogue" — you can and do hold a 
  conversation across multiple turns.
- Never refuse to engage. If you have zero context and cannot ask a useful 
  clarifying question, give the best general reading from classical 
  knowledge and note what would sharpen it.

EDIT 2 — Add a clarifying-question guard to needs_disclaimer() in 
prompt_builder.py.

Replace the current needs_disclaimer() function:

    def needs_disclaimer(answer: str) -> bool:
        return DISCLAIMER.lower() not in answer.lower()

With:

    def needs_disclaimer(answer: str) -> bool:
        """
        Return True if the disclaimer should be appended.
        Suppressed when response is a clarifying question:
        - ends with "?" AND under 60 words
        - Threshold 60: tight enough to avoid suppressing short readings.
          Tune down to 40 if false suppressions observed.
        """
        if answer.strip().endswith("?") and len(answer.split()) < 60:
            return False  # CQ path — no prediction content, no disclaimer needed
        return DISCLAIMER.lower() not in answer.lower()

After both edits, run the existing test suite and report:
- Pass/fail count
- Any test that newly fails and the exact assertion error
- Word count of SYSTEM_PROMPT after Edit 1 (approximate)

No other changes. Do not touch astrologer.py.