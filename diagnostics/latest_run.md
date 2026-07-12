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

# S66 Task 4 — Ring 3 chunk-text artifact: STOPPED (verification gate mismatch)

Docs channel, token-exempt, no source edits. Goal: replicate
`agent/interpretive/palm_reading.py`'s RAG query construction in a
scratch script, run its retrieval call against two given LEFT/RIGHT
palm descriptions, and check the returned scores against an expected
set before writing `diagnostics/ring3_chunks_S66.md`.

## Step 1 — Query reconstruction (verified against source)

`agent/interpretive/palm_reading.py:253`:
```python
query_text = " ".join(d for d in (palm_left, palm_right) if d)[:_QUERY_TRUNCATE_CHARS]
```
LEFT then RIGHT, single-space join, truncated to 500 chars
(`_QUERY_TRUNCATE_CHARS = 500`). Retrieval call:
`search(query_text, n_results=_N_RESULTS, book_name=_CHEIRO_BOOK)` with
`_N_RESULTS = 6`, `_CHEIRO_BOOK = "cheiroslanguageo00chei_1"` (both read
from the module's own constants, lines 44/54). Replicated verbatim in a
throwaway scratch script (not committed); constructed query length
confirmed at exactly 500 chars, truncated mid-word after "mounts,".

## Step 2 — Verification gate: MISMATCH

| # | Page | Expected score | Observed score | Match? |
|---|---|---|---|---|
| 1 | 163 | 0.6801 | 0.6801 | Yes |
| 2 | 123 | 0.6723 | 0.6723 | Yes |
| 3 | 135 | 0.6472 | 0.6473 | **No** |
| 4 | 120 | 0.6458 | 0.6458 | Yes |
| 5 | 134 | 0.6434 | 0.6434 | Yes |
| 6 | 166 | 0.6367 | 0.6367 | Yes |

Page ordering matches exactly; 5/6 scores match exactly; chunk 3
(page 135) is off by 0.0001 (observed 0.6473 vs. expected 0.6472).
Confirmed the discrepancy is in the stored/returned score itself, not a
display-rounding artifact (`repr(c["score"])` printed the same 0.6473).

Per the task's verification gate ("must be exactly" the six listed
scores) this is a mismatch -> STOPPED per instruction.
`diagnostics/ring3_chunks_S66.md` was **not** written; nothing
committed for Task 4 itself. Scratch script deleted (never committed).

Open question for design-chat / next touch: is the expected score set
stale (pre-dates a ChromaDB re-ingest or embedding-model change), or is
0.6473 evidence of retrieval nondeterminism on this single chunk? Not
investigated further per the STOP instruction — re-open only with an
explicit re-run or re-baseline instruction.
