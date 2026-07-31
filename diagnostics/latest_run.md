# Removed stale xfail marker: test_yogini_orchestrator_returns_current_md

## Change applied

`tests/test_yogini_routing.py`:
- Removed the `@pytest.mark.xfail(reason=...)` decorator from
  `test_yogini_orchestrator_returns_current_md` -- its cited blocker
  (`result_formatter.py`'s `format_answer()` not admitting `yogini_dasha`)
  is resolved, confirmed against `result_formatter.py`'s own S73/Prompt 5
  docstring and the live `_format_yogini_dasha()` dispatch branch (see prior
  `diagnostics/latest_run.md` investigation, this session).
- Appended one `UPDATE (Session 84)` note to the module docstring's existing
  Session 72/73 history, closing out the "Still xfail; will pass once
  Prompt 5 lands" line left stale from Session 73 -- test is a live
  assertion again.
- No other test in this file touched.

## Flag: unused `import pytest`

`tests/test_yogini_routing.py` line 45 (`import pytest`) is now unused --
the removed decorator was its only reference in this file. Left as-is: out
of this prompt's stated scope ("no other test changes"). Worth a follow-up
cleanup pass if/when this file is touched again.

## Full suite result

**3360 passed, 7 skipped, 0 failed** (82.22s) -- 0 xpassed (was 1 before this
change; the former XPASS is now counted as a normal PASS, net +1 passed vs.
the prior run, same total collected).

```
........................................................................ [ 34%]
........................................................................ [ 36%]
........................................................................ [ 38%]
........................................................................ [ 40%]
........................................................................ [ 42%]
........................................................................ [ 44%]
........................................................................ [ 47%]
........................................................................ [ 49%]
........................................................................ [ 51%]
........................................................................ [ 53%]
........................................................................ [ 55%]
........................................................................ [ 57%]
........................................................................ [ 59%]
........................................................................ [ 62%]
........................................................................ [ 64%]
.........................................................s.....ss....... [ 66%]
........................................................................ [ 68%]
........................................................................ [ 70%]
........................................................................ [ 72%]
........................................................................ [ 74%]
........................................................................ [ 76%]
........................................................................ [ 79%]
........................................................................ [ 81%]
........................................................................ [ 83%]
........................................................................ [ 85%]
........................................................................ [ 87%]
........................................................................ [ 89%]
........................................................................ [ 91%]
........................................................................ [ 94%]
...........................s.............................s....ss........ [ 96%]
........................................................................ [ 98%]
.......................................................                  [100%]
============================== warnings summary ===============================
..\..\..\AppData\Local\Programs\Python\Python311\Lib\site-packages\opentelemetry\util\_importlib_metadata.py:32
  C:\Users\sulab\AppData\Local\Programs\Python\Python311\Lib\site-packages\opentelemetry\util\_importlib_metadata.py:32: DeprecationWarning: SelectableGroups dict interface is deprecated. Use select.
    return EntryPoints(ep for group_eps in eps.values() for ep in group_eps)

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
[_patch_stage2_openai] stub invocation count: 7
3360 passed, 7 skipped, 1 warning in 82.22s (0:01:22)
```

Nothing committed. This session's uncommitted working-tree changes:
`agent/interpretive/palm_reading.py`, `tests/interpretive/test_palm_reading.py`,
`tests/test_yogini_routing.py`, `CLAUDE.md`, `frontend/app.py` (pre-existing
S82 palm UI gate, untouched this session), `diagnostics/latest_run.md`.
