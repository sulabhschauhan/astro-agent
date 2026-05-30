# Read Prompt

#Paste your instructions here. Then tell Claude: "Read .claude/read_prompt.md and execute"


In agent/prompt_builder.py make four surgical edits only. Do not touch
SYSTEM_PROMPT, _LOW_CONFIDENCE_ADDENDUM, _INTRODUCE_ADDENDUM, needs_disclaimer(),
or any slot rendering logic except what is listed below.

Edit 1 — Add spouse_pdf and hand_detail parameters to build_prompts() signature,
after palm_right, before introduce:
    spouse_pdf: str | None = None,
    hand_detail: str | None = None,

Edit 2 — In the slot rendering loop, add two new elif branches after the
existing "palm" branch:

    elif slot == "own_pdf" and pdf_context:
        lines.append("\n## AstroSage Annual Report\n" + pdf_context)

    elif slot == "spouse_pdf" and spouse_pdf:
        lines.append("\n## Spouse AstroSage Annual Report\n" + spouse_pdf)

    elif slot == "hand_detail" and hand_detail:
        lines.append("\n## Hand Detail Analysis\n" + hand_detail)

Also rename the existing "pdf" branch to handle "pdf" as a legacy fallback
only — keep it but add "pdf" as an alias that also renders pdf_context,
so old callers using "pdf" in context_order do not break during transition.

Edit 3 — Remove the PALM_TOPICS constant and the entire nudge block at the
bottom of build_prompts() — the lines starting with:
    if not has_palm and any(t in question.lower() for t in PALM_TOPICS):
Remove those lines and PALM_TOPICS entirely. Nudge is now owned by the
classifier, not prompt_builder.

Edit 4 — Update the build_prompts() docstring to add spouse_pdf and
hand_detail parameter descriptions, and note that nudge logic has been
removed (now owned by context_classifier).

Paste only the edited function signature, the slot rendering loop,
and confirmation that PALM_TOPICS and the nudge block are gone.
Do not paste the full file.