# Uncommitted diff: frontend/app.py

**One-line note**: wires the S83 near-miss margin log into
`_capture_dogfood_run()` -- appends a `### near_miss_margin` block per
dogfood capture, one line per feature showing the full ranked candidate
list (`window={N} candidates=[(rank, chunk_id, score), ...]`) pulled from
`reading.stage1_feature_diagnostics[feature]["candidates"]`, or
`NOT CAPTURED`/`EMIT_ERROR` when empty/failed -- logging only, no
production-path behavior change. (Correction to my last message: I'd
mis-described this as "the S82 palm UI gate work" without having reread the
diff -- it is not; it's the S83 near-miss margin wiring, confirmed against
the actual diff below.)

**Confirmed**: `git status --short` shows only `M frontend/app.py` -- this
is the only uncommitted change outstanding in the working tree.

Not committed -- source-code edit, no `RATIFIED: commit authorized` token
in this prompt.

## Full diff

```diff
diff --git a/frontend/app.py b/frontend/app.py
index 53ee65c..f840241 100644
--- a/frontend/app.py
+++ b/frontend/app.py
@@ -25,6 +25,7 @@ from PIL import Image
 from agent.palm_processor import validate_palm_image, describe_palm_image, describe_hand_detail_image
 from agent.interpretive.palm_reading import (
     generate_palm_reading, prepare_palm_reading, complete_palm_reading, _FEATURE_PAGE_RANGES,
+    _N_RESULTS_PER_FEATURE,
 )
 from agent.infra.orchestrator import answer_question
 from agent.interpretive.answer_renderer import render_answer
@@ -313,6 +314,32 @@ def _capture_dogfood_run(palm_left, palm_right, hand_detail, reading) -> None:
     # close-out prompt's job, not done here.
     lines.append("")
 
+    # S83 near-miss margin log: full ranked candidate list (up to 30) before
+    # window slicing, one line per feature. No threshold, no behavior change --
+    # logging only. Format: {feature}: window={N} candidates=[(rank, chunk_id, score), ...]
+    lines.append("### near_miss_margin")
+    try:
+        has_data = False
+        for feature in sorted(reading.stage1_feature_diagnostics):
+            diag = reading.stage1_feature_diagnostics[feature]
+            candidates = diag.get("candidates", [])
+            if candidates:
+                has_data = True
+                formatted = ", ".join(
+                    f"({rank}, {chunk_id}, {score})"
+                    for rank, chunk_id, score in candidates
+                )
+                lines.append(
+                    f"  {feature}: window={_N_RESULTS_PER_FEATURE} "
+                    f"candidates=[{formatted}]"
+                )
+        if not has_data:
+            lines.append("near_miss_margin: NOT CAPTURED")
+    except Exception as exc:
+        logger.warning("app._capture_dogfood_run: near_miss_margin capture failed: %s", exc)
+        lines.append("near_miss_margin: EMIT_ERROR")
+    lines.append("")
+
     _DOGFOOD_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
     with open(_DOGFOOD_LOG_PATH, "a", encoding="utf-8") as f:
         f.write("\n".join(lines) + "\n")
```
