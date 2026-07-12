# frontend/app.py — question path rewired to orchestrator + renderer (Session 65, 4d)

Docs/code task: ONE file edited (`frontend/app.py`), chat/question path
only. Self-gate: `ast.parse()` clean, zero remaining functional `ask(`
call sites, palm/AstroSage blocks confirmed zero-diff. Committed per the
ratification token, as the LAST action after all checks passed.

## Where chart_data was found (task step 1's "find it; if app.py does NOT
already hold one, STOP" instruction)

`st.session_state.chart` — set at the sidebar's birth-details form submit
handler: `chart = calculate_chart(name.strip(), dob, tob, place); st.session_state.chart = chart`
(pre-existing code, untouched by this edit). This is exactly
`orchestrator.answer_question()`'s expected `chart_data: dict` parameter
("pre-computed calculate_chart() output for the primary native. Never
recomputed here.", per that function's own docstring, read before wiring
this call). No chart computation was wired by me — it already existed.

## Self-gate results

```
$ python -c "import ast; ast.parse(open('frontend/app.py', encoding='utf-8').read())"
syntax OK

$ grep -n "\bask(" frontend/app.py
218:# ask()) is NOT modified, and astrosage_parser.py is NOT modified; the RAG/
```

The single match is a pre-existing code **comment** (from the earlier
AstroSage-display task, mentioning `ask()` descriptively to explain that
`pdf_context` still flows there) — not a call site, and not touched by
this edit. **Zero functional `ask(` references remain.**

```
$ python -c "from agent.infra.orchestrator import answer_question; from agent.interpretive.answer_renderer import render_answer"
imports OK
```

**Palm/AstroSage zero-diff check** — confirmed via the diff's own hunk
line ranges, not just a keyword grep:

```
$ git diff frontend/app.py | grep "^@@"
@@ -19,12 +19,13 @@ os.chdir(_ROOT)
@@ -94,8 +95,6 @@ if "palm_left_regen_warning" not in st.session_state:
@@ -716,44 +715,6 @@ for msg in st.session_state.messages:
@@ -764,59 +725,35 @@ if prompt:
```

Four hunks total: (1) the import block, (2) removing the dead
`pending_question` session-default line (the `palm_left_regen_warning`
line shown in that hunk's context is unchanged, just adjacent context
Git includes for readability), (3) the "Generate My Reading" button
block, (4) the chat-input handler. **None fall within the palm/AstroSage
upload-and-display block** (original lines ~215–707: PDF upload/parse,
the new AstroSage display expander, both palm upload/confirm/swap
blocks, spouse PDF, hand-detail photo, palm-reading-generation block —
all untouched). A follow-up keyword grep on the diff (`palm_left|
palm_right|pdf_context|spouse_pdf|hand_detail|...`) only matches lines
being REMOVED from inside the deleted `ask()` call's own keyword
arguments and the deleted "Generate My Reading" block's context-check —
i.e., code that READ those session-state values to hand them to `ask()`,
not edits to the blocks that WRITE/DISPLAY them.

## Rule 4: dead-code removal, what was removed and why each is provably dead

- **`pending_question` session-state key** (default + both read/write
  sites) — after removing `ask()`'s "gated" result handling (below),
  there is no remaining site anywhere in the file that ever sets
  `pending_question` to a non-`None` value again. Verified by grep
  across the whole file before removal (3 total references, all inside
  the one unit removed together): the session-state default, the
  "Generate My Reading" button's guard condition, and its own reset-to-
  `None` line.
- **The "Generate My Reading" button block** (`_has_new_context` +
  the `if st.session_state.pending_question is not None...` block) —
  this entire block existed to resume a question that
  `agent.astrologer.ask()`'s Phase 1 context-classifier gate had
  deferred (`result["gated"] == True`). `orchestrator.answer_question()`
  has no "gated" concept at all in its return contract (always returns
  a `DomainAnswer`, `REFUSAL` included, never a "need more context, try
  again later" state) — so this entire mechanism is provably dead once
  `ask()` itself is no longer called anywhere in this file.
- **The `if result["gated"]: ... else: ...` branch** inside the old
  chat-input handler — same reasoning; `answer_question()`'s return
  value has no `"gated"`/`"nudges"` keys at all (it's a `DomainAnswer`
  dataclass, not the old dict shape), so this branching and the
  `nudges`-info-box rendering inside it are both dead by construction
  once the call target changed.
- **`introduce`/`_introduce` flags** — an `agent.astrologer.ask()`-
  specific "Parashara introduces himself" persona feature;
  `answer_question()`/`render_answer()` have no persona/greeting
  concept at all (fully deterministic template-fill, no LLM). Removed
  as part of the same call-site rewrite, not a separately-decided
  removal.

**Left untouched (NOT dead, explicitly checked)**: the "Render
conversation history" loop's `for _nudge in msg.get("nudges", []):`
(line ~716) — this is a safe `.get()`-with-default read, not a write
site, and still correctly handles any pre-existing session file saved
to disk from before this change that legitimately carries a `"nudges"`
key on old assistant messages. Newly-appended messages simply omit that
key going forward (the `.get()` default handles its absence
gracefully) — this is a natural, backward-compatible evolution of the
message shape, not residue needing removal or a quarantine note.

## Rule 5: quarantine marker

Per the task's own instruction, no comment was added atop
`agent/astrologer.py`'s `ask()` — that file is not in this task's file
list (`frontend/app.py` only). Noting here instead, as instructed:
`agent.astrologer.ask()` is now genuinely unreferenced by the frontend
(confirmed by this task's own `ask(` grep) — this is the quarantine the
CLAUDE.md Session 65 "T4 V1 boundaries" lock already called for
("astrologer.ask() QUARANTINED: frontend must not call it... module
retained for V1.1 Path (a) research only"). `agent/context_classifier.py`
and `agent/context_bundle.py` (only ever reachable via `ask()`) are
transitively quarantined the same way — none of the three files were
touched, deleted, or marked in this task; they remain on disk exactly
as-is, simply unreachable from the frontend now.

## No exception-type narrowing (rule 2)

The task asked for "try/except around the chain: exception -> st.error
with message" (singular chain, singular catch) — replaced the old
three-way `ValueError`/`RuntimeError`/generic-with-API-key-sniffing
`except` cascade (which existed to interpret `astrologer.ask()`'s own
specific failure modes, e.g. OpenAI auth errors) with one
`except Exception as e: st.error(f"{type(e).__name__}: {e}")`, matching
`orchestrator.answer_question()`'s own documented `Raises:` contract
(`ValueError`, `RuntimeError`, both now generically caught) without
inventing narrower handling for failure modes that no longer apply to
this call target (there is no OpenAI call in this deterministic path at
all, so the old API-key-sniffing branch would never fire and was
correctly dropped, not preserved as vestigial dead logic).

## Full diff

```diff
diff --git a/frontend/app.py b/frontend/app.py
index 7d3b15d..df83ee3 100644
--- a/frontend/app.py
+++ b/frontend/app.py
@@ -19,12 +19,13 @@ os.chdir(_ROOT)
 import streamlit as st
 
 from agent.chart_calculator import calculate_chart, format_kundali_context, geocode_place_candidates
-from agent.astrologer import ask
 from agent.session_manager import SessionManager
 from agent.astrosage_parser import parse_astrosage_pdf
 from PIL import Image
 from agent.palm_processor import validate_palm_image, describe_palm_image, describe_hand_detail_image
 from agent.interpretive.palm_reading import generate_palm_reading
+from agent.infra.orchestrator import answer_question
+from agent.interpretive.answer_renderer import render_answer
 
 logger = logging.getLogger(__name__)
 
@@ -94,8 +95,6 @@ if "palm_left_regen_warning" not in st.session_state:
     st.session_state.palm_left_regen_warning = None
 if "palm_right_regen_warning" not in st.session_state:
     st.session_state.palm_right_regen_warning = None
-if "pending_question" not in st.session_state:
-    st.session_state.pending_question = None
 if "spouse_pdf_context" not in st.session_state:
     st.session_state.spouse_pdf_context = None
 if "_spouse_pdf_name" not in st.session_state:
@@ -716,44 +715,6 @@ for msg in st.session_state.messages:
             for _nudge in msg.get("nudges", []):
                 st.info(_nudge)
 
-# ─── "Generate My Reading" button ────────────────────────────────────────────
-# Shown when a question was gated and context has since been uploaded.
-_has_new_context = (
-    st.session_state.get("palm_left_str") is not None
-    or st.session_state.get("palm_right_str") is not None
-    or st.session_state.pdf_context is not None
-)
-if st.session_state.pending_question is not None and _has_new_context:
-    if st.button("✋ Generate My Reading"):
-        _pq = st.session_state.pending_question
-        st.session_state.pending_question = None
-        _introduce = len(st.session_state.messages) == 0
-        with st.spinner("Consulting the stars…"):
-            _btn_result = ask(
-                question=_pq,
-                kundali_context=st.session_state.kundali_str or None,
-                pdf_context=st.session_state.pdf_context or None,
-                palm_left=st.session_state.get("palm_left_str"),
-                palm_right=st.session_state.get("palm_right_str"),
-                spouse_pdf=st.session_state.get("spouse_pdf_context"),
-                hand_detail=st.session_state.get("hand_detail_str"),
-                session=st.session_state.session_mgr,
-                introduce=_introduce,
-            )
-        _btn_answer = _btn_result["answer"]
-        _btn_nudges = _btn_result.get("nudges", [])
-        st.session_state.messages.append({"role": "user", "content": _pq})
-        st.session_state.messages.append({
-            "role":    "assistant",
-            "content": _btn_answer,
-            "nudges":  _btn_nudges,
-        })
-        try:
-            st.session_state.session_mgr.save()
-        except RuntimeError:
-            pass
-        st.rerun()
-
 # Chat input — disabled until chart is ready
 prompt = st.chat_input(
     "Enter your birth details in the sidebar first" if not st.session_state.chart_ready else "Ask about your birth chart…",
@@ -764,59 +725,35 @@ if prompt:
     if not st.session_state.chart_ready:
         st.warning("Please calculate your birth chart in the sidebar first.")
     else:
-        # introduce=True only on the very first real answer (no messages yet)
-        introduce = len(st.session_state.messages) == 0
-
         with st.chat_message("user"):
             st.markdown(prompt)
 
+        # Deterministic calc-engine pipeline ONLY (CLAUDE.md "V1 scope" lock):
+        # answer_question() routes -> builds a DomainChartProfile -> formats
+        # a DomainAnswer (REFUSAL included); render_answer() turns that into
+        # display text. No partner chart wiring in V1 -- marriage questions
+        # will REFUSAL via has_partner_data, same as any other domain's
+        # REFUSAL (rendered like any other answer, not specially handled).
+        # Both user+assistant messages are appended together, only after a
+        # full success, so a failure anywhere in this chain leaves
+        # st.session_state.messages completely unchanged (no partial turn).
         try:
             with st.spinner("Consulting the stars…"):
-                result = ask(
-                    question=prompt,
-                    kundali_context=st.session_state.kundali_str or None,
-                    pdf_context=st.session_state.pdf_context or None,
-                    palm_left=st.session_state.get("palm_left_str"),
-                    palm_right=st.session_state.get("palm_right_str"),
-                    spouse_pdf=st.session_state.get("spouse_pdf_context"),
-                    hand_detail=st.session_state.get("hand_detail_str"),
-                    session=st.session_state.session_mgr,
-                    introduce=introduce,
-                )
-
-            if result["gated"]:
-                st.session_state.pending_question = prompt
-                st.warning(result["answer"])
-            else:
-                st.session_state.messages.append({"role": "user", "content": prompt})
+                domain_answer = answer_question(prompt, st.session_state.chart)
+                answer_text = render_answer(domain_answer)
 
-                with st.chat_message("assistant"):
-                    answer = result["answer"]
+            st.session_state.messages.append({"role": "user", "content": prompt})
 
-                    st.markdown(answer)
+            with st.chat_message("assistant"):
+                st.markdown(answer_text)
 
-                    for _nudge in result.get("nudges", []):
-                        st.info(_nudge)
+            st.session_state.messages.append({"role": "assistant", "content": answer_text})
 
-                    st.session_state.messages.append({
-                        "role":    "assistant",
-                        "content": answer,
-                        "nudges":  result.get("nudges", []),
-                    })
+            # Persist session to disk; non-fatal on failure
+            try:
+                st.session_state.session_mgr.save()
+            except RuntimeError:
+                st.warning("Session could not be saved. Chat history may not persist.")
 
-                    # Persist session to disk; non-fatal on failure
-                    try:
-                        st.session_state.session_mgr.save()
-                    except RuntimeError:
-                        st.warning("Session could not be saved. Chat history may not persist.")
-
-        except ValueError as e:
-            st.error(f"Invalid input: {e}")
-        except RuntimeError as e:
-            st.error(f"Database error: {e}")
         except Exception as e:
-            err = str(e).lower()
-            if "api_key" in err or "authentication" in err:
-                st.error("OpenAI API key missing or invalid — check your .env file.")
-            else:
-                st.error(f"{type(e).__name__}: {e}")
+            st.error(f"{type(e).__name__}: {e}")
```
