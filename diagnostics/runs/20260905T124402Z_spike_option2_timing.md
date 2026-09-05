# Option 2 spike -- Track A (computed dates) + Track C (meaning only)

Generated: 2026-09-05T12:44:02Z
Question: When will I get married?

## Prediction (stated before running)

gpt-4o will produce >=1 dated claim, every date traceable to the fact block, and will stay silent on which specific outcome the marriage has. A date NOT in the fact block would be the single most important finding of the run, to be led with.

## 1. Step 0 -- constant verification

| constant | expected | actual | match |
|---|---|---|---|
| HARD_CONTEXT_CEILING | 72000 | 72000 | OK |
| APPROX_TO_REAL_RATIO | 1.7 | 1.7 | OK |
| INTERPRETER_TPM_LIMIT | 30000 | 30000 | OK |

## 2. Step 1 -- the plan (live, temp=0, NOT substituted)

| domains | houses | whose_chart | time_scope | in_scope | houses widened beyond [7]? |
|---|---|---|---|---|---|
| marriage, timing_dasha | [7] | self | future | True | False |

Reasoning (verbatim): The question is about the timing of marriage, which involves the 7th house for marriage and timing_dasha to determine when it might occur.

Plan call: 2.55s, source=llm, planner_fallback=False

## 3. Step 2 -- Track A deterministic fact block

Module: `agent\calculations\dashas\vimshottari.py` (1 line(s))

```python
"""Vimshottari dasha sequence, antardasha, and pratyantar periods."""
```

Public functions defined in this module: (none)
Public classes defined in this module: (none)

**STOP -- `agent/calculations/dashas/vimshottari.py` is a STUB: docstring only, zero functions, zero classes. Track A cannot compute the 7th-lord placement, the mahadasha sequence, the current mahadasha/antardasha, or the future 7th-lord periods. Per this task's own rule, no date is approximated and no interpreter call is made. Steps 3 and 4 are SKIPPED. $0 spent on Steps 3-4.**

Total cost this run: ~$0.002 (Step 1 planner call only).
