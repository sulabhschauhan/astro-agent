# frontend/app.py — AstroSage terminal-bare display + Pratyantar/Lal-Kitab withholding (Session 65, 4b)

Docs/code task: ONE file edited (`frontend/app.py`), user's-own AstroSage
PDF block only. `astrosage_parser.py` untouched — verified by not opening
it for edit, only reading it to confirm the combined-output format before
writing the splitter (per CLAUDE.md's "verify task prompts against code"
discipline). `ast.parse()` passes. Splitter functionally verified against
a simulated real `parse_astrosage_pdf()` output shape (see below) — no
live Streamlit run, no live API/PDF-parsing call.

## Confirmation: palm / spouse-PDF / chat / ask() blocks show zero diff lines

```
$ git diff frontend/app.py | grep -E "^\+|^-" | grep -iE "palm_left|palm_right|spouse_pdf|chat_input|chat_message|palm_reading_result|st\.session_state\.messages|def ask|ask\(|orchestrator"

+# ask()) is NOT modified, and astrosage_parser.py is NOT modified; the RAG/
```

The single match is a **code comment** (part of the new `_WITHHELD_SECTIONS`
justification block) that mentions `ask()` by name to explain that
`pdf_context` still flows there unmodified — not a change to any excluded
block's logic. Zero functional diff lines touch palm, spouse-PDF, chat, or
`ask()`/orchestrator wiring.

## Two minimal top-of-file additions, outside the literal "AstroSage PDF block" location

The task's "log a warning" requirement for the fail-soft path needed
Python logging, which `app.py` didn't previously import. Added:
- `import logging` to the existing stdlib import block.
- `logger = logging.getLogger(__name__)` right after the import block
  (matching this codebase's convention elsewhere, e.g. `astrosage_parser.py`
  itself, `palm_processor.py`).

These don't touch or alter any excluded block's behavior — they're a
necessary shared prerequisite for the new helper's fail-soft logging, not
functional changes to palm/spouse/chat/ask() code.

## The helper's split logic

```python
def _split_astrosage_sections(pdf_context: str) -> list[tuple[str, str]]:
    parts = re.split(r"^\[([^\]]+)\]$", pdf_context, flags=re.MULTILINE)
    # parts[0] is whatever precedes the first header (the "ASTROSAGE PDF
    # DATA:" prefix line, not a real section) -- discarded. Remaining
    # parts alternate name, content, name, content, ...
    if len(parts) < 3:
        logger.warning(...)
        return [("AstroSage Report", pdf_context)]

    pairs: list[tuple[str, str]] = []
    for i in range(1, len(parts), 2):
        name = parts[i].strip()
        content = parts[i + 1].strip() if i + 1 < len(parts) else ""
        pairs.append((name, content))
    return pairs
```

**Why this works against the real format**, verified by reading
`agent/astrosage_parser.py` line-by-line before writing this (not assumed
from the task prompt): `parse_astrosage_pdf()` returns exactly
`"ASTROSAGE PDF DATA:\n" + "\n\n".join(f"[{name}]\n{content}" for name,
content in sections.items())`. `re.split` with a `^\[([^\]]+)\]$`
capturing group, `re.MULTILINE`, splits the string at every line that is
*exactly* `[SomeName]` and keeps the captured names in the result list —
so the result alternates `[pre-text, name1, content1, name2, content2,
...]`. `parts[0]` is always just the `"ASTROSAGE PDF DATA:"` prefix line
(not a section), discarded; the rest are paired up two at a time.

**SENSITIVE_TO** comment placed directly above the function, quoting the
exact join expression — if `astrosage_parser.py`'s combined-output format
(join separator, header bracket syntax, or the leading prefix) ever
changes, this splitter must be re-verified and updated with it.

**Fail-soft path**: if `len(parts) < 3` (i.e., no `[Name]` header line was
found anywhere — `re.split` returned the original string as a single
unsplit element, `parts == [pdf_context]`), the function logs a warning
via `logger.warning(...)` and returns `[("AstroSage Report", pdf_context)]`
— the full string is still displayed, degraded (unsectioned) but never
crashing, per the task's explicit "fail-soft" requirement.

**Verified functionally** (not just read) against a simulated real
`parse_astrosage_pdf()` output:

```
$ python -c "<simulated combined-output test>"
WARNING:test:no headers found -- displaying unsplit
Parsed sections: [('Varshaphal', 'Varshaphal body text'), ('Pratyantar', 'Pratyantar body text'), ('Muntha', 'Muntha body text'), ('Lal Kitab', 'Lal Kitab body text')]

After withholding filter: ['Varshaphal', 'Muntha']

Fail-soft test: [('AstroSage Report', 'just some plain text, no headers here')]
```

Confirms: (1) all 4 simulated sections split correctly; (2) the withholding
filter correctly drops exactly `Pratyantar` and `Lal Kitab`, leaving
`Varshaphal` and `Muntha`; (3) the fail-soft path degrades to a single
unsplit section and logs a warning, without raising.

## Widget choice: st.text(), not st.markdown(), for section bodies

The task said "render... VERBATIM — no LLM, no rephrasing, no truncation,"
without specifying a widget (unlike the earlier palm-description task,
which explicitly asked for a widget-choice call). For true verbatim
fidelity, `st.markdown()` risks reinterpreting any incidental
markdown-special characters in the PDF-extracted text (`*`, `_`, `#`,
etc. — plausible in astrological tabular text) as formatting instead of
literal content. `st.text()` renders the string with zero markup
interpretation and preserves whitespace/line breaks exactly — the safer
choice for a "VERBATIM" contract. `st.subheader()` labels the section
name (a UI structural element, not part of the extracted content itself,
so styling it is fine).

## Spouse PDF — explicitly out of scope, confirmed

No code was added for the spouse AstroSage PDF. It remains context-only
in V1, per the task's explicit instruction; the diff-grep check above
independently confirms zero lines touch `spouse_pdf`.

## Rendering placement and persistence

The new expander is rendered via `if st.session_state.pdf_context:`,
placed immediately after the existing upload/parse `if`/`elif` block and
gated independently of the upload event itself — so it persists across
Streamlit reruns (e.g., after a chat turn triggers a rerun) rather than
only appearing in the same run as a fresh parse. This matches the
existing pattern already used elsewhere in this file for other
persistent context displays (the palm confirmed-description expanders,
the sidebar's Kundali Summary expander).

## pdf_context / parse-failure / clearing-on-removal paths: confirmed unchanged

The existing `if uploaded_pdf is not None: ... elif
st.session_state["_astrosage_pdf_name"] is not None: ...` block (lines
219–232 pre-edit) is untouched byte-for-byte in the diff — the new
expander block was inserted immediately after it, not interleaved into it.

## Full diff

```diff
diff --git a/frontend/app.py b/frontend/app.py
index 3b620ae..7d3b15d 100644
--- a/frontend/app.py
+++ b/frontend/app.py
@@ -4,6 +4,7 @@ Streamlit UI — Vedic astrology assistant (Parashara RAG agent).
 """
 
 import hashlib
+import logging
 import re
 import sys
 import os
@@ -25,6 +26,8 @@ from PIL import Image
 from agent.palm_processor import validate_palm_image, describe_palm_image, describe_hand_detail_image
 from agent.interpretive.palm_reading import generate_palm_reading
 
+logger = logging.getLogger(__name__)
+
 # ─── Page config (must be first Streamlit call) ───────────────────────────────
 
 st.set_page_config(
@@ -211,6 +214,59 @@ with st.sidebar:
 
 # ─── Main area ────────────────────────────────────────────────────────────────
 
+# T4 architecture / T4 V1 boundaries lock (CLAUDE.md Session 65): display-
+# layer withholding ONLY -- pdf_context (the full parsed string threaded to
+# ask()) is NOT modified, and astrosage_parser.py is NOT modified; the RAG/
+# LLM path still sees these sections in full. Pratyantar: suppressed per
+# the +/-37-day-drift/wrong-lord posture (same root cause as
+# prompt_builder.py's kundali-slot carry-forward) -- Pratyantar-level date
+# claims aren't reliable enough to show a user as if they were precise.
+# Lal Kitab: post-V1 hard gate (CLAUDE.md "Post-V1 design gate: Lal Kitab
+# remedy tier", Session 61) -- remedies are out of V1 scope entirely,
+# withheld here rather than partially surfaced. Scope guard: this
+# frozenset governs ONLY the "Your AstroSage Report" display expander
+# below -- no other code path reads it. Revisit trigger: Lal Kitab V1.1
+# unlock (gated on that carry-forward's required steps) or a future
+# Pratyantar-precision fix.
+_WITHHELD_SECTIONS = frozenset({"Pratyantar", "Lal Kitab"})
+
+
+def _split_astrosage_sections(pdf_context: str) -> list[tuple[str, str]]:
+    """
+    Split parse_astrosage_pdf()'s combined output into (name, content) pairs
+    for verbatim display.
+
+    SENSITIVE_TO astrosage_parser.py's parse_astrosage_pdf() combined-output
+    format: `"ASTROSAGE PDF DATA:\\n" + "\\n\\n".join(f"[{name}]\\n{content}"
+    for name, content in sections.items())`. This splitter locates each
+    "[Name]" header line and slices the text between headers as that
+    section's body. If astrosage_parser.py's join format ever changes,
+    this splitter breaks with it -- re-verify against the source before
+    trusting this function after any astrosage_parser.py edit.
+
+    Fail-soft: if no "[Name]" headers are found, returns the full string
+    unsplit under a single "AstroSage Report" label and logs a warning --
+    never raises.
+    """
+    parts = re.split(r"^\[([^\]]+)\]$", pdf_context, flags=re.MULTILINE)
+    # parts[0] is whatever precedes the first header (the "ASTROSAGE PDF
+    # DATA:" prefix line, not a real section) -- discarded. Remaining
+    # parts alternate name, content, name, content, ...
+    if len(parts) < 3:
+        logger.warning(
+            "app.py: no '[Name]' section headers found in AstroSage "
+            "pdf_context — displaying unsplit (degraded, not crashing)."
+        )
+        return [("AstroSage Report", pdf_context)]
+
+    pairs: list[tuple[str, str]] = []
+    for i in range(1, len(parts), 2):
+        name = parts[i].strip()
+        content = parts[i + 1].strip() if i + 1 < len(parts) else ""
+        pairs.append((name, content))
+    return pairs
+
+
 st.title("Parashara — Vedic Astrology")
 
 with st.expander("Upload context (PDF + palms)", expanded=False):
@@ -231,6 +287,15 @@ with st.expander("Upload context (PDF + palms)", expanded=False):
         st.session_state.pdf_context = None
         st.session_state["_astrosage_pdf_name"] = None
 
+    if st.session_state.pdf_context:
+        _astrosage_sections = _split_astrosage_sections(st.session_state.pdf_context)
+        with st.expander("Your AstroSage Report"):
+            for _section_name, _section_content in _astrosage_sections:
+                if _section_name in _WITHHELD_SECTIONS:
+                    continue
+                st.subheader(_section_name)
+                st.text(_section_content)
+
     # ── Left palm ─────────────────────────────────────────────────────────────
     uploaded_left = st.file_uploader(
         "Left hand (innate potential)", type=["jpg", "jpeg", "png"], key="palm_left_uploader",
```
