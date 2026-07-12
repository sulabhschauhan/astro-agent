# S66 Task 3 — Fix-forward: nested-expander crash class in frontend/app.py

Self-gated, one source file edited: `frontend/app.py`. Live crash:
StreamlitAPIException "Expanders may not be nested inside other
expanders" at line ~301 (`st.expander("Your AstroSage Report")`) on
real-PDF upload.

## Step 1 — Audit (pre-edit classification)

All `st.expander` calls in `frontend/app.py`, pre-edit line numbers:

| Line | Expander | Nested inside "Upload context" (line 281)? |
|---|---|---|
| 203 | `Kundali Summary` | No — sidebar, executes before line 281 |
| 281 | `Upload context (PDF + palms)` | N/A — the containing expander |
| 301 | `Your AstroSage Report` | **Yes** |
| 441 | `Review left palm description` | **Yes** |
| 463 | `Left palm description` (confirmed, collapsed) | **Yes** |
| 604 | `Review right palm description` | **Yes** |
| 626 | `Right palm description` (confirmed, collapsed) | **Yes** |
| 713 | `Classical sources` | **Yes** — additional member found beyond the listed set; it's a display surface (palm-reading-result block), same class as the AstroSage Report |

The upload expander's `with`-block (line 281) runs through line 715 —
it dedents to column 0 at line 717 (`if not st.session_state.chart_ready:`).
Crash class = 6 nested expanders: 301, 441, 463, 604, 626, 713.

## Step 2 — Fix applied

- **Rule (a)** (display surfaces -> top level, guarded): `Your AstroSage
  Report` (was 301) and `Classical sources` (was 713, part of the
  palm-reading-result display block) both moved out of the upload
  expander's `with`-block to top level, immediately after it ends.
  `Your AstroSage Report` is now guarded by
  `if st.session_state.get("pdf_context"):`; the palm-reading-result
  block keeps its existing `if st.session_state.palm_reading_result is
  not None:` guard. Both `st.expander` calls are unchanged internally
  and are legal at top level. `_split_astrosage_sections` /
  `_WITHHELD_SECTIONS` render loop is unchanged.
- **Rule (b)** (upload-flow elements -> demoted): the four palm review/
  confirmed-description expanders (441, 463, 604, 626) replaced with
  `st.container()` + a bold `st.markdown` label line, content always
  visible (no collapse). No state keys, button keys, confirm/discard
  logic, or checkpoint flow changed — widget demotion only. Review
  descriptions becoming always-visible is intentional (collapsed review
  invites blind confirm).
- Line 203 (`Kundali Summary`, sidebar) was untouched — not a member of
  the crash class.

Post-edit `st.expander`/`st.container()` inventory:
```
203:        with st.expander("Kundali Summary"):
281:with st.expander("Upload context (PDF + palms)", expanded=False):
432:            with st.container():
455:            with st.container():
597:            with st.container():
620:            with st.container():
701:    with st.expander("Your AstroSage Report"):
717:        with st.expander("Classical sources"):
```
No nested expanders remain.

## Step 3 — Verify (headless AppTest, crash path)

```
2026-07-12 13:05:12.784 WARNING streamlit.runtime.scriptrunner_utils.script_run_context: Thread 'MainThread': missing ScriptRunContext! This warning can be ignored when running in bare mode.
2026-07-12 13:05:18.102 Thread 'MainThread': missing ScriptRunContext! This warning can be ignored when running in bare mode.
PASS: no exception after pdf_context injection
```
AppTest ran the app module (no stub-around needed — no module-level
side-effect blocker hit), then injected `pdf_context` with real
`[Varshaphal]`/`[Sade Sati]` sections and re-ran. No exception either
run — the `Your AstroSage Report` expander at top level (post-fix) no
longer triggers the nested-expander StreamlitAPIException.

Full suite:
```
3166 passed, 3 skipped, 1 warning in 127.16s (0:02:07)
```
Matches expected baseline exactly — zero delta.

## Step 4 — Commit

Green -> single commit:
`94e87b6` — "S66: fix nested-expander crash — AstroSage report to top
level, palm review expanders demoted to containers"
(RATIFIED: commit authorized)
