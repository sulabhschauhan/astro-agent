# frontend/app.py rider — swap-regen stale-reading guard (closes item-5 wording gap)

Docs/code rider on the prior 4a task: ONE file edited, single change —
`st.session_state.palm_reading_result = None` added to both success and
failure outcomes of the swap-regen path, both hands. `ast.parse()` passes.
Not committed, per instruction.

## Exact count and locations: 8 new lines (4 clear-site categories x 2 duplicated handler blocks)

The swap-regen code block (inside the "No (swap)" button handler) is
byte-identical in both the left-hand handler and the right-hand handler
(confirmed in the prior 4a report), so one `replace_all` edit updated both
occurrences at once. The **4 distinct clear-site categories** are:

1. Left regen **success** (`try:` body, after `palm_left_confirmed = False`)
2. Left regen **failure** (`except RuntimeError:` body, alongside the
   existing `palm_left_regen_warning` fallback-warning assignment)
3. Right regen **success** (`try:` body, after `palm_right_confirmed = False`)
4. Right regen **failure** (`except RuntimeError:` body, alongside the
   existing `palm_right_regen_warning` fallback-warning assignment)

Each of these 4 appears **twice** in the file (once inside the left-hand
"No (swap)" handler, once inside the right-hand "No (swap)" handler — both
handlers regenerate *both* hands regardless of which swap button was
clicked), giving **8 total new `st.session_state.palm_reading_result =
None` lines**:

- Line ~332 (left-handler block, left-success)
- Line ~339 (left-handler block, left-failure)
- Line ~347 (left-handler block, right-success)
- Line ~355 (left-handler block, right-failure)
- Line ~495 (right-handler block, left-success)
- Line ~502 (right-handler block, left-failure)
- Line ~510 (right-handler block, right-success)
- Line ~518 (right-handler block, right-failure)

(Approximate line numbers post-edit; see the diff below for exact
placement.) This closes the gap flagged in the prior 4a report: the
failure-path fallback string is hand-reframed (still describes the
post-swap bytes, just under the pre-swap hand's framing), so it is
equally stale relative to any already-generated reading as the
success-path regeneration is — both outcomes now clear
`palm_reading_result`.

## Verification

```
$ python -c "import ast; ast.parse(open('frontend/app.py', encoding='utf-8').read())"
syntax OK
```

## Full diff

```diff
diff --git a/frontend/app.py b/frontend/app.py
index 1100e61..3b620ae 100644
--- a/frontend/app.py
+++ b/frontend/app.py
@@ -329,24 +329,28 @@ with st.expander("Upload context (PDF + palms)", expanded=False):
                                     )
                                     st.session_state.palm_left_regen_warning = None
                                     st.session_state.palm_left_confirmed     = False
+                                    st.session_state.palm_reading_result     = None
                                 except RuntimeError:
                                     st.session_state.palm_left_regen_warning = (
                                         "Could not regenerate the left palm reading after "
                                         "swapping — it may reference the wrong hand. "
                                         "Consider re-uploading this image."
                                     )
+                                    st.session_state.palm_reading_result = None
                                 try:
                                     st.session_state.palm_right_str = describe_palm_image(
                                         st.session_state.palm_right_bytes, "right"
                                     )
                                     st.session_state.palm_right_regen_warning = None
                                     st.session_state.palm_right_confirmed     = False
+                                    st.session_state.palm_reading_result      = None
                                 except RuntimeError:
                                     st.session_state.palm_right_regen_warning = (
                                         "Could not regenerate the right palm reading after "
                                         "swapping — it may reference the wrong hand. "
                                         "Consider re-uploading this image."
                                     )
+                                    st.session_state.palm_reading_result = None
                         else:
                             st.session_state.palm_left_str            = None
                             st.session_state.palm_left_hash           = None
@@ -488,24 +492,28 @@ with st.expander("Upload context (PDF + palms)", expanded=False):
                                     )
                                     st.session_state.palm_left_regen_warning = None
                                     st.session_state.palm_left_confirmed     = False
+                                    st.session_state.palm_reading_result     = None
                                 except RuntimeError:
                                     st.session_state.palm_left_regen_warning = (
                                         "Could not regenerate the left palm reading after "
                                         "swapping — it may reference the wrong hand. "
                                         "Consider re-uploading this image."
                                     )
+                                    st.session_state.palm_reading_result = None
                                 try:
                                     st.session_state.palm_right_str = describe_palm_image(
                                         st.session_state.palm_right_bytes, "right"
                                     )
                                     st.session_state.palm_right_regen_warning = None
                                     st.session_state.palm_right_confirmed     = False
+                                    st.session_state.palm_reading_result      = None
                                 except RuntimeError:
                                     st.session_state.palm_right_regen_warning = (
                                         "Could not regenerate the right palm reading after "
                                         "swapping — it may reference the wrong hand. "
                                         "Consider re-uploading this image."
                                     )
+                                    st.session_state.palm_reading_result = None
                         else:
                             st.session_state.palm_right_str            = None
                             st.session_state.palm_right_hash           = None
```

## Flag: the stated commit plan implies rewriting already-pushed history

The task says "4a + this rider commit together after ratification" with a
single combined message. **4a is already committed and pushed** as
`d823a93` on `main` (pushed in the prior turn, before this rider prompt
arrived). Combining it with this rider into one commit would require
amending or squashing `d823a93` and force-pushing over it — which is
exactly what CLAUDE.md's Working Style #13 ("NEVER REWRITE PUSHED HISTORY
ON MAIN," Session 64) says to stop and surface rather than execute.

This rider task only asked me to edit + report + not commit, which I've
done — no destructive action was taken. But when ratification lands and
someone asks for "4a + this rider as one commit," that instruction should
be treated as stale/to-be-confirmed rather than auto-executed: the two
straightforward non-destructive options are (a) commit this rider as its
own new commit on top of `d823a93` (keeping both in history), or (b) if a
single combined commit is genuinely wanted, that's an explicit
squash-and-force-push request that needs your direct confirmation first.
Flagging now so this doesn't get executed silently later.
