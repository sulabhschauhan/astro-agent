# frontend/app.py — palm human checkpoint + palm reading generation (Session 65)

Docs/code task: ONE file edited (`frontend/app.py`), palm-related blocks
only. Verified via `grep` that the diff touches zero lines matching
`astrosage_pdf|spouse_pdf|chat_input|orchestrator|def ask|ask(` — the
AstroSage PDF block, spouse PDF block, chat loop, and `ask()`/orchestrator
wiring are untouched, as scoped. Syntax-checked with `ast.parse()` (passes)
and the new import target resolves (`from agent.interpretive.palm_reading
import generate_palm_reading` imports cleanly). No live Streamlit run, no
live API calls performed — `st.set_page_config()` requires a real Streamlit
runtime context, so a full `streamlit run` was out of scope for a
static/syntax-level check; see the manual smoke checklist below for what a
human should click through instead. Not committed — holding for
design-chat ratification.

## Design choices made, per the task's "your call — REPORT which and why"

**st.markdown() inside st.expander(), not st.text_area()**, for displaying
the vision-output description. Rationale: `st.text_area` is an editable
widget — even though this code never reads back an edited value, presenting
the description in an editable-looking box sends a misleading UI signal
that free-text editing is supported, when the task explicitly bans it in
V1 ("an edited description would be untraceable to the vision output").
`st.markdown` in an `st.expander` unambiguously renders read-only text and
reuses a pattern already established elsewhere in this same file (the
"Kundali Summary" expander, the "Upload context" expander) — visual
consistency, not a new UI idiom.

**Confirmed badge** = `st.caption("✓ Description confirmed")` above a
collapsed (`expanded=False`) expander holding the same read-only text —
kept visible but out of the way once confirmed.

## Session state keys added

Only **one** new key: `palm_reading_result` (default `None`), added to the
existing per-key `if "X" not in st.session_state: st.session_state.X = ...`
defaults block. Everything else needed already existed in the file
(`palm_left_confirmed` / `palm_right_confirmed` were already scaffolded —
this task is what finally wires real UI to them; they were previously
being auto-set to `True` immediately after `describe_palm_image()`
succeeded, which is exactly the auto-confirm this task removes).

## Enumeration of every touch point

1. **Import** — added `from agent.interpretive.palm_reading import
   generate_palm_reading` directly below the existing `agent.palm_processor`
   import (same import block, same style).
2. **Session default** — `palm_reading_result = None`.
3. **Auto-confirm removal** (both hands) — `palm_X_confirmed = True` ->
   `False` right after a successful `describe_palm_image()` call; success
   toast changed from `"Left/Right palm read ✓"` to `"Left/Right palm
   described — review below"`.
4. **New content-confirmation UI** (both hands) — a new `elif` branch,
   sibling to the existing `if not st.session_state.palm_X_hand_confirmed:`
   ("Is this your hand?" orientation check). Gated so it only appears
   *after* the orientation check passes — showing "confirm this text" before
   the user has even confirmed which hand it is would be confusing, since a
   swap at that point regenerates the text anyway. This ordering choice is
   a judgment call, flagged here rather than silently assumed.
   - Pending: `st.expander(..., expanded=True)` + `st.markdown(desc)`, two
     buttons ("Looks right — use this description" -> confirmed=True;
     "Discard — re-upload" -> full reset).
   - Confirmed: `st.caption("✓ Description confirmed")` + collapsed
     read-only expander.
5. **"Discard — re-upload" reset** (both hands) — reuses the *exact* same
   8-key reset shape already used by this file's existing "uploader cleared"
   `elif` block (`palm_X_str/hash/status/bytes/confirmed/hand_confirmed/
   needs_reupload/regen_warning` + `_palm_X_image_name`), plus the new
   `palm_reading_result = None` stale-guard.
6. **Swap-regen path** (both hands, both swap-button handlers — the
   left-side and right-side "No (swap)" handlers contain byte-identical
   regen code, so one `replace_all` edit updated both at once) — after each
   successful `describe_palm_image()` regen call, that hand's
   `palm_X_confirmed` is now set to `False`. The existing regen-failure
   `except RuntimeError:` warning path is untouched, as instructed.
7. **"Generate Palm Reading" button** — new block placed at the end of the
   `with st.expander("Upload context (PDF + palms)")` block, right after
   the Hand Detail Photo section (co-located with the rest of the palm
   context UI, not mixed into the chat flow below). Rendered only when
   `_any_hand_confirmed` is true. On click: builds `_confirmed_left` /
   `_confirmed_right` by passing `None` for any hand whose `confirmed` flag
   is `False`, even if that hand's description string still exists in
   session state; calls `generate_palm_reading(palm_left=..., palm_right=...,
   hand_detail=st.session_state.get("hand_detail_str"))` (no `client=` arg
   — production path, real `OpenAI()` constructed inside the module); wraps
   in `except (ValueError, RuntimeError) as e: st.error(str(e))`.
8. **Result display** — reads `st.session_state.palm_reading_result` each
   rerun (not just on click, so it persists across reruns without
   regenerating). If `validation.passed is False`: `st.error(...)` listing
   every failure string, `reading_text` is never rendered (fail-closed
   display). If passed: `st.markdown(reading_text)`, then a collapsed
   `st.expander("Classical sources")` listing `book, p.<page> (score:
   <score>)` per chunk — sources never appear inline in the reading itself.
9. **Stale-reading guard (`palm_reading_result = None`)** — added
   everywhere a hand's description transitions to `None` within the palm
   blocks: both `hard_reject` branches, both duplicate-image-uploaded
   branches, both `describe_palm_image()` `RuntimeError` catches, both
   "uploader cleared" `elif` auto-reset blocks, both swap-`else`
   single-hand-present branches, and the two new "Discard — re-upload"
   buttons. **12 sites total** (6 per hand).

## One deliberately NOT-implemented case — flagged, not fixed

Task item 5 scopes the stale-reading guard to exactly two triggers:
**"discarded or re-uploaded."** I implemented it at every literal
discard/re-upload/clear-to-`None` site (enumerated above), but I did
**not** add it to the swap-regen success path (item 6) — a swap doesn't
discard or re-upload anything; it regenerates fresh (unconfirmed) content
for both hands while leaving `palm_reading_result` alone. This means: if a
user generates a reading, then later clicks "No (swap)," the old
`palm_reading_result` stays on screen even though it was built from
pre-swap descriptions and both hands are now newly unconfirmed. The
`palm_X_confirmed = False` change (item 6) does correctly force the user
through fresh confirmation before they can *generate a new* reading, but
the *stale old reading* itself is not proactively cleared or hidden in
the meantime. I stayed literal to the item-5 wording rather than
expanding scope unilaterally — **flagging this as a probable real gap**
for a design-chat call: should swap-regen also clear
`palm_reading_result`?

## Manual smoke checklist (not run — no live API calls made)

**Checkpoint -> confirm -> generate path:**
1. Enter birth details, calculate chart.
2. Open "Upload context" expander, upload a left-hand image.
3. Confirm "Is this your Left hand?" -> Yes.
4. Expect: success toast reads "Left palm described — review below" (not
   "read ✓"); an expanded "Review left palm description" box appears with
   the raw vision-output text; two buttons below it.
5. Click "Looks right — use this description."
6. Expect: box collapses to a caption "✓ Description confirmed" + a
   collapsed "Left palm description" expander; a "Generate Palm Reading"
   button now appears further down (since `_any_hand_confirmed` is now
   true with only one hand).
7. Click "Generate Palm Reading."
8. Expect: spinner "Generating your palm reading…", then either a rendered
   reading (`st.markdown`) with a collapsed "Classical sources" expander
   below it, or an `st.error` if validation failed or the call raised.

**Discard path:**
9. Upload a right-hand image, confirm orientation Yes, but this time click
   "Discard — re-upload" instead of "Looks right."
10. Expect: all right-hand state clears (image preview disappears, hash/
    status/bytes/confirmed/hand_confirmed/needs_reupload/regen_warning all
    reset) and, if a reading had already been generated, it disappears too
    (stale-guard).

**Fail-closed validation path:**
11. (Requires a stubbed/mocked `generate_palm_reading` to force
    `validation.passed=False` without a live call — not exercised here.)
    Expect: `st.error("Palm reading failed validation and cannot be
    shown: ...")` listing each failure string, and `reading_text` is never
    rendered anywhere on the page.

**Swap-after-reading path (the flagged gap above):**
12. Generate a reading with both hands confirmed, then click "No (swap)"
    on either hand.
13. Expect (per current implementation): both hands regenerate and both
    `confirmed` flags reset to `False` (fresh confirmation required before
    a NEW reading can be generated) — but the OLD `palm_reading_result`
    remains visible on screen until a new reading is generated or a
    discard/re-upload happens. Confirm whether this is acceptable or
    should be closed per the flag above.

**Partial-confirmation exclusion path:**
14. Confirm only the left hand (leave right unconfirmed, description
    string still present). Click "Generate Palm Reading."
15. Expect: `generate_palm_reading` is called with `palm_left=<left
    description>, palm_right=None` — the unconfirmed right description is
    never passed through, even though `st.session_state.palm_right_str`
    still holds a value.
