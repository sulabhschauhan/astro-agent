# S130 — evidence behind the stress-test question set

Companion to `diagnostics/stress_test_questions_S130.md` (the run sheet).
Nothing here is needed to run the test. It is the reasoning and the measured
numbers, kept so the promote/hold call is auditable.

Branch `wip/interpretive-pilot @ c0d6c70`. No source file was changed to produce
any number below. Sandbox egress to `api.openai.com` was tested and is blocked
(`CONNECT tunnel failed, response 403`), so nothing here was measured against
the live model.

---

## 1. What the run is for

`advisory_would_drop_a_kept_claim` decides whether the advisory planet reader in
`silence_gate.py` gets promoted to enforcing. It only means something if the
planet reader actually fires, and it only fires on claims shaped
*"<graha> is in the <Nth>"*.

**The trap.** The frozen real gpt-5 run
(`tests/fixtures/qa_captures/s129_live_gpt5_20260912T160015Z.md`) answered
*"What does my chart say about my career and profession?"* with four claims —
all four **lord-shaped** ("With the 10th lord in the 4th…"). Re-judged in S130
with Sulabh's real planet positions injected, the reader fired on **0 of 4**.
Re-asking that question alone returns `0` **vacuously**, which looks identical
to "the reader agrees with the enforcing gate".

## 2. The corpus is not the constraint — the model's phrasing is

Measured per planner domain by building the **real payload** through
`payload_builder.build_payload()` and counting with `silence_gate`'s own
readers. Deterministic, no API.

| domain | segs | planet-shaped | lord-shaped | planet % |
|---|---|---|---|---|
| technique_method | 586 | **164** | 116 | 58.6% |
| career | 618 | **96** | 131 | 42.3% |
| health | 585 | 92 | 134 | 40.7% |
| wealth | 698 | 92 | 138 | 40.0% |
| spirituality | 367 | 91 | 126 | 41.9% |
| longevity | 502 | 87 | 127 | 40.7% |
| parents | 371 | 72 | 127 | 36.2% |
| children | 373 | 59 | 125 | 32.1% |
| marriage | 350 | 51 | 136 | 27.3% |
| education | 259 | 40 | 117 | 25.5% |
| siblings | 183 | 32 | 126 | 20.3% |
| timing_dasha | 116 | 27 | 0 | 100% |
| property | 221 | 24 | 117 | 17.0% |
| enemies_conflict | 428 | 24 | 120 | 16.7% |
| travel | 147 | 20 | 115 | 14.8% |
| planetary_nature | 58 | 5 | 0 | 100% |

Every domain carries planet-shaped doctrine. The career payload had **96
planet-shaped sentences in front of gpt-5** and the model still wrote four
lord-shaped claims and nothing else.

So targeting planet-dense *chapters* does nothing. The only lever from the
question side is **naming a graha explicitly** — which is why Q1, Q2 and Q3 on
the run sheet name Saturn, planetary strength, and Mars/Venus rather than a life
area. A wealth question was dropped from an earlier draft: at 40.0% it is the
same instrument as career, which already returned zero.

Corollary: no question can be excused as "no planet material available", so a
vacuous zero is evidence about **gpt-5**, not about coverage.

## 3. Why Q6 and Q7 are both there

Tested directly against `capability_gate.assess`:

```
domains=['marriage','timing_dasha'], future -> refuse_outright=False
                                               kept=['marriage'] dropped=['timing_dasha']
domains=['timing_dasha'],            future -> refuse_outright=True   kept=[]
```

Q6 (*"When will I get married?"*) plans both domains. The gate drops the timing
half, **keeps marriage, and calls the interpreter** — the honest-partial path.
It is a full paid turn, not free. Only Q7, with no answerable domain left,
refuses outright before any model call.

Also verified, because it looked like a hole and is not: a forward `time_scope`
alone fires the requirement even with no timing domain —
`domains=['career'], scope=future` → `declined=['dasha_timing']`, message
emitted, no domain dropped, answer still produced. Pinned by
`test_future_time_scope_alone_triggers_even_without_the_timing_domain`.
**BY DESIGN** — do not re-raise it as a bug.

## 4. The two wrong-drop classes

Both measured in the S130 corpus sweep. Both are invisible while the reader is
advisory and become live wrong drops the moment it is promoted.

**(a) UNCAUGHT_LORDSHIP.** The ambiguity rule fires only when `_CONDITION_RE`
also matches, and that requires the literal `<Nth> lord`. Lordship worded any
other way is invisible to it, so the reader judges the sentence as a *plain*
planet claim on **half** its condition. 9 in the corpus, 8 would be dropped:

```
[not_applicable] bphs1_ch24  ...if Saturn or Mercury ruling the 5th is in the 12th.
[applicable    ] bphs1_ch24  where Mars ruling the 10th house is in the 2nd house.
[not_applicable] bphs1_ch18  Sun is in the 7th while his dispositor is conjunct...
```

The `applicable` row is right **by coincidence** (Mars is in Sulabh's 2nd) while
discarding the "ruling the 10th" half. Two causes mixed in: genuine alternate
phrasing (`ruling the 5th`, `dispositor`) and OCR-mangled ordinals (`Sth`,
`{2th`); only the first survives into interpreter prose.

This is the **mirror** of the blind spot CLAUDE.md records. The recorded one
fails safe. This one does not.

**(b) DEFINITIONAL.** Doctrine, not a precondition about this chart:

```
Jupiter and Mercury have Digbala in the ascendant.
Sun and Mars acquire this strength in the 10th house.
```

The reader parses `Jupiter … in the ascendant` and rules it false for Sulabh.
The sentence never claimed the placement holds for the native, so dropping it
silences a true statement. **Q2 on the run sheet is aimed at this class.**

## 5. How the capture gets read

```
python scripts/classify_advisory_drops.py diagnostics/qa_capture/<UTC>.md
```

Reads `advisory_detail` (statement + both verdicts, captured per claim),
isolates the true would-drops, sorts them into CORRECT_CATCH /
UNCAUGHT_LORDSHIP / DEFINITIONAL.

Decision rule, fixed before the data so it cannot be fitted to it:

- **`planet_claims_judged == 0`** → INCONCLUSIVE. The reader never fired. Per §2
  that is a finding about gpt-5's phrasing, and the reader cannot be promoted on
  this evidence at all, because there is none.
- **all would-drops CORRECT_CATCH** → promote is supported. Still a human call.
- **any UNCAUGHT_LORDSHIP or DEFINITIONAL** → **HOLD.** Promotion would silence a
  true claim — invisible in production, and the precise failure the silence gate
  exists to prevent, reintroduced by its own promotion.

Also read off the capture, independent of the metric:

- Q7's `gate_refused_outright` — the gate's own field, not a derived value.
- Q6's decline message present **alongside** a real marriage answer.
- Q5's rendered answer diffed against the frozen fixture's.
- `ungated_pct` per turn — how much of each shipped answer the enforcing gate
  could not judge at all.

## 6. Provenance and limits

Chart facts in every S130 measurement were derived from
`reference/oracle_fixtures/sulabh.md`: Sagittarius lagna (line 77), planet signs
from the JHora Traditional-Lahiri export (lines 151-159), sign→house via the
PDF p.3 Chalit Table (whole-sign, Bhav 1 = Sagittarius … Bhav 12 = Scorpio).
**Derived, not production** — `calculate_chart()` remains the authority and the
live run uses it.

**Not tested, and not claimed:** the pipeline end to end under a stubbed
interpreter. Three attempts failed on the ghost guard (the stub could not mint
resolvable `segment_ids`) and the line was abandoned rather than forced. S129
already verified 56/56 no-exception across 4 charts × 7 question shapes × 2
interpreter modes; this file adds nothing to that.
