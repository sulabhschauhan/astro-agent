# Near-miss margin analysis — dogfood_capture.md since S84 archive/clear

Analysis only. No production code or threshold changes.

## 1. Runs captured since S84 clear

`diagnostics/dogfood_capture.md` currently holds **3 RUN blocks**, all same
day (2026-07-31), all `capture_reason: instability, silence`:

| # | timestamp | capture_reason |
|---|---|---|
| 1 | 2026-07-31T15:06:06.947177 | instability, silence |
| 2 | 2026-07-31T15:13:30.702501 | instability, silence |
| 3 | 2026-07-31T15:16:23.707563 | instability, silence |

No `wrong_source` or `all_rejected` runs in this window. Runs 1 and 2 have
near-identical LEFT/RIGHT field text (same confirmed descriptions,
word-for-word) — almost certainly the same user session recaptured across
retries, not two independent data points. Run 3 adds a HAND_DETAIL capture
and has a materially different head-line retrieval result (see below).

**Sample size verdict up front: 3 failing runs, of which 2 are near-
duplicates of each other. This is well under the <5-run floor this task set
for drawing a distribution. Reporting plainly per the task's own instruction
rather than stretching a conclusion — see Section 4.**

## 2. Per-run failing-feature near-miss data

"Failing" = `stage1_feature_diagnostics` outcome `empty_first` (Stage-1
returned RAW=0 claims) or a rejected-then-retried attempt. `unknown` rows
(sun line, mount of jupiter in runs 1-2) were never queried (absence-phrased
or no quality resolved) — not a retrieval/extraction failure, excluded below.

| Feature | Run | capture_reason | Rank-1 chunk | Rank-1 score | Rank-3 score (cutoff) | Gap (r1-r3) | Stage-1 outcome |
|---|---|---|---|---|---|---|---|
| fate line | 1 | instability, silence | p165_c1 | 0.6002 | 0.5671 | 0.033 | empty_first (raw=0) |
| fate line | 2 | instability, silence | p165_c1 | 0.6001 | 0.5671 | 0.033 | empty_first (raw=0) |
| fate line | 3 | instability, silence | p165_c0/p165_c1 (tied) | 0.4942 | 0.4729 | 0.021 | empty_first (raw=0) |
| fingers | 1 | instability, silence | p96_c0 | 0.5164 | 0.51 | 0.006 | empty_first (raw=0) |
| fingers | 2 | instability, silence | p96_c0 | 0.5164 | 0.51 | 0.006 | empty_first (raw=0) |
| fingers | 3 | instability, silence | p96_c0 | 0.5251 | 0.5125 | 0.013 | **success_first** (not a failure this run) |
| heart line | 1 | instability, silence | p160_c2 | 0.6427 | 0.6061 | 0.037 | empty_first (raw=0) |
| heart line | 2 | instability, silence | p160_c2 | 0.6427 | 0.6061 | 0.037 | empty_first (raw=0) |
| heart line | 3 | instability, silence | p159_c3 | 0.6088 | 0.5971 | 0.012 | empty_first (raw=0) |
| head line | 3 | instability, silence | p151_c2 | 0.5898 | 0.5485 | 0.041 | empty_first (raw=0) — head line SUCCEEDED in runs 1-2, only failed in run 3 |
| thumb | 1 | instability, silence | p88_c0 | 0.5104 | 0.5041 | 0.006 | success_retry (attempt_1 overlap 0.31 < 0.4 floor for p88_c0, retried, passed) |
| thumb | 2 | instability, silence | p88_c0 | 0.5104 | 0.5041 | 0.006 | success_retry (attempt_1 overlap 0.38 < 0.4 floor for p88_c0, retried, passed) |

Notes:
- In every single row above, the rank-3 score (current cutoff) is already
  within ~0.006-0.041 of the rank-1 score — the same "no cliff" shape S81/S82
  measured corpus-wide. There is no row where the gap between rank-3 and a
  buried rank-4+ candidate looks like a real cutoff loss.
- No feature in any of the 3 runs has its best (or any plausible) candidate
  outside the top-3 window. `empty_first` is Stage-1 emitting **zero raw
  claims** (raw=0) given chunks it already had in-window — this is not a
  rank/window symptom by construction; widening the window would hand the
  same LLM call the same top-3-plus-more chunks it already saw.
- thumb's two rejections are the one mechanism actually visible here, and
  it's the OVERLAP FLOOR (0.4), not rank: a claim WAS extracted (raw=1) from
  the in-window rank-1/rank-2 chunk (`p88_c0`), scored 0.31 and 0.38 overlap,
  below the 0.4 floor, rejected on attempt 1, then recovered on retry both
  times.

## 3. Distribution requested (Section 4 of the task)

Given every failing feature's supporting evidence is already inside the
current `_N_RESULTS_PER_FEATURE=3` window in all 3 runs:
- Window=5 would catch: **0 additional failures** (nothing failing here is
  rank-4/5).
- Window=8: **0**.
- Window=10: **0**.

Miss-rank is not "scattered" or "consistent" in the sense the task's
decision gate asks about, because there IS no buried-rank miss in this data
— the question the gate poses (uniform stable rank N vs. per-feature
scatter) doesn't have a live instance to measure from these 3 runs. Zero
widening cases means this sample cannot support opening the widening case
at all, let alone characterize its shape.

## 4. Flag: any RUN where the correct chunk never appears in the 30-pool

None identified. All 3 runs are `instability, silence` (not `wrong_source`),
and every failing feature's near_miss_margin shows a plausible in-doctrine
top candidate (fate ~p165, fingers ~p96, heart ~p159/160, head ~p145-151) —
consistent with prior sessions' validated doctrine locations. No feature in
this window shows a candidate pool that looks corpus-empty or off-topic.
Nothing here to flag as a corpus/query gap distinct from the S84-confirmed
pattern below.

## 5. Cross-check against S84's specific claim

S84 (3cc3abe, 3 runs reviewed Jul 31): "near_miss_margin shows NO case of a
correct/strong candidate buried past rank 3 for any failing feature (fate
line, fingers, heart line, mount of jupiter all failed with top-3 scores
0.51-0.68 already in window)."

**These 3 new runs CONFIRM that finding, do not contradict it.** Same
features (fate line, fingers, heart line) fail again with top-3 scores in
the same 0.49-0.65 band, still with no buried candidate. New data point:
run 3 shows **head line** also failing via `empty_first` for the first time
in this data — but its near_miss_margin top-3 (p151_c2 0.59, p146_c2 0.57,
p147_c0 0.55) is even stronger than runs 1-2's head-line success case, so
this is not a new counter-example either; if anything it strengthens the
case that the bottleneck is downstream of retrieval, not the window.

## 6. Bottom line for the decision this task serves

Per the task's own gate: "if accumulated captures show a consistent
near-miss margin (correct chunk buried at stable rank N) then widen; else
per-feature fix." Neither branch is actually supported by this data —
**there is no buried-rank case to widen for**, consistent or scattered.
The recurring failure signature across all 3 runs is downstream of
retrieval (Stage-1 raw=0 extraction, or the 0.4 overlap floor rejecting an
in-window claim on first attempt) — same as S84's own next-lead note. No
number is proposed here (Working Style #16/#19) — with 3 total runs (2 of
them near-duplicate) there isn't enough independent evidence to set
anything regardless of which branch this pointed to.

**Recommendation for design chat, not a decision made here:** the open
lead is still the Stage-1 overlap floor / raw=0 extraction behavior (S84's
own next-session pointer), not the retrieval window. Continue accumulating
dogfood captures (ASTRO_DOGFOOD_CAPTURE must stay on in the deployed
frontend per S83's between-session action item) before either widening the
window or touching the 0.4 floor — 3 runs is too thin to set either number.
