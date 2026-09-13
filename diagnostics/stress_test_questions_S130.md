# S131 RUN SHEET

```
$env:ASTRO_PALM_ENABLED=1; $env:ASTRO_DOGFOOD_CAPTURE=1; $env:PALM_RULES_ENGINE=1; streamlit run frontend/app.py
```

Calculate Kundli, then ask:

1. Do I have any raja yogas or special combinations in my chart?
2. What does Saturn's placement mean for my life?

Then send me `diagnostics/qa_capture/<UTC>.md`.

Three questions only if you also applied the planner gloss (§2 below) — in that
case add:

3. What do Mars and Venus in my chart say about me?

---

## Why only these

**Q1** is the one new measurement. The S130 run produced 21 planet judgements and
**zero** disagreements, because gpt-5 wrote every claim as
`"With <planet> in the <true house>, <doctrine>"` — the reader checked a true
prefix and passed. Drop behaviour was never exercised. Yoga doctrine is written
as *conditions* ("if X is in the Nth"), most of them false for any given chart,
so it is the realistic source of a NOT_APPLICABLE. Without one, promote/hold
stays undecidable.

**Q2** repeats S130 turn 1 verbatim as the before/after for the
`reasoning_effort` fix. Compare against: **55.51s total, interpreter 50.51s,
reasoning_tokens 8384, `reasoning_effort_applied: false`.** Check
`reasoning_effort_path` in the new capture — it should read `named_kwarg` or
`extra_body`, never `dropped (...)`.

**Q3** is the definitional control and only means anything after the gloss.

Dropped from the S130 set: *"When will I get married?"* burned 50,277 prompt
tokens for `interpreter_refused: true` and zero claims, and *"What will happen in
my next dasha period?"* already establishes the refusal for free. Also dropped
the lord-of-10th and career questions — both are now-answered controls.

## S130 results, for reference

| question | claims | adv APPLICABLE | adv NOT_APPLICABLE | ungated% | interp |
|---|---|---|---|---|---|
| Saturn's placement | 3 | 1 | 0 | 66.7 | 50.5s |
| strong or weak planets | 9 | 7 | 0 | 100.0 | 58.4s |
| Mars and Venus | 12 | 12 | 0 | 100.0 | — |
| lord of 10th | 2 | 0 | 0 | 0.0 | — |
| career | 5 | 1 | 0 | 20.0 | — |
| when married | 0 | — | — | — | refused, paid |
| next dasha | — | — | — | — | refused at gate, free |

**Promote/hold verdict: HOLD.** Not because a wrong drop appeared — none did —
but because no drop event was observed at all, and drop authority is the only
thing promotion grants.

## 1. FIXED — `reasoning_effort` never reached the API

`interpreter.py::_default_llm` caught `TypeError` from the named
`reasoning_effort=` kwarg and retried **without the parameter**. On an SDK whose
`chat.completions.create` signature predates that kwarg, that path ran on every
call — 7 of 7 turns showed `reasoning_effort_applied: false` with 3,328-8,384
reasoning tokens and 50-58s interpreter stages.

Now the TypeError path retries via `extra_body={"reasoning_effort": ...}`, which
reaches the API on any SDK version. Only a refusal **by the API** drops the
setting, and `usage.reasoning_effort_path` records which of the three paths ran.
Suite 217 passed. Counts as a config change, so the next run is a required live
run — which it is anyway.

Related, unfixed, watch it: prompt_tokens hit **170,469** and **184,501** on
turns 1-2 against the ~80k the $0.19/question estimate was built on, and
`cached_tokens` was 0 on six of seven turns. The corpus-first cache is not
hitting. Worth its own look once the reasoning fix lands.

## 2. YOUR CALL — `planetary_nature` is a glossary domain

All five of its chapters are reference material:

```
bphs1_ch2   Great Incarnations (Of The Lord)
bphs1_ch3   Planetary Characters And Description   <- male/female, guna, element, tissue
bphs1_ch4   Zodiacal signs Described
bphs2_ch76  Effects of the Five Elements
bphs2_ch77  Effects of the Satwa Guna etc.
```

There is no placement doctrine in it. When the planner picked it **alone** for
*"What do Mars and Venus say about me?"*, gpt-5 correctly recited definitions and
prefixed each with a true placement — producing "With Venus in the 6th house
(Taurus), Venus is a female planet." Faithful, cited, gate-clean, and worthless
to a reader.

LAYER: this is the **planner**, not the gate and not selection. The gate cannot
catch it — its law is "drop only when the claim's condition is POSITIVELY FALSE",
and these conditions are true. Selection is locked (S124/S126) and is not at
fault; the tags are correct.

Proposed one-line gloss in `planner.py`'s system prompt:

> `planetary_nature` is REFERENCE material — planetary and sign definitions
> (gender, guna, element, bodily tissue, direction). Never plan it alone. Pair it
> with an interpretive domain, or omit it.

**Not applied.** A planner prompt change alters planning for every question and
cannot be verified without live gpt-4o calls, which the sandbox cannot make
(`api.openai.com` → 403). Shipping it untested would be SAMPLE-before-SCALE in
reverse. Apply it yourself if you agree, then Q3 tests it.

Precedent if you want one: S61 fixed planner-side misclassification by expanding
the prompt's glosses rather than touching thresholds, and locked that as the
remedy path.
