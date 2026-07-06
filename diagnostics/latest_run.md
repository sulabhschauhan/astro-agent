# Session 54: Ashtakavarga package reconciliation (stub removal)

**Ashtakavarga module file (unchanged from previous prompt):**
`agent/calculations/ashtakavarga/ashtakavarga.py` — `compute_bav` + `compute_sav`.

## Verification before deletion
- `agent/calculations/ashtakavarga/bav.py` — confirmed docstring-only stub
  (1 line: `"""Bhinna (individual) Ashtakavarga — per-planet bindhu tables."""`).
- `agent/calculations/ashtakavarga/sav.py` — confirmed docstring-only stub
  (1 line: `"""Sarva Ashtakavarga — aggregate bindhu scores across all planets."""`).
- Repo-wide grep for `ashtakavarga.bav` / `ashtakavarga.sav` / `ashtakavarga/bav`
  / `ashtakavarga/sav` imports: zero hits outside PyJHora-main (vendored,
  out of scope). Safe to delete — no revert needed.

## Three surgical actions — diff summary
1. **Deleted** `agent/calculations/ashtakavarga/bav.py` and
   `agent/calculations/ashtakavarga/sav.py` (superseded stubs).
2. **CLAUDE.md** — Calculation Architecture package-structure line: replaced
   `` `ashtakavarga/` (bav, sav) `` with
   `` `ashtakavarga/` (single module: compute_bav + compute_sav; bav.py/sav.py stubs superseded and removed, Session 54) ``.
   **Master Build Plan** ("ASTRO AGENT — MASTER BUILD PLAN.md") file manifest:
   replaced the two lines
   `ashtakavarga/bav.py — Bhinnashtakavarga (per-planet point table)` /
   `ashtakavarga/sav.py — Sarvashtakavarga (aggregate point table)` with one
   line: `ashtakavarga/ashtakavarga.py — single module: compute_bav + compute_sav; bav.py/sav.py stubs superseded and removed (Session 54)`.
   (Phase 5 session-narrative detail further down in the Master Build Plan,
   lines ~595-627, left untouched — out of scope for a stub-listing
   reconciliation, and superseded by the locked P2 sequencing anyway.)
3. **CLAUDE.md** — appended to Known Source Divergences (this repo's
   carry-forward/known-items list): "**Ashtakavarga router wiring
   carry-forward** (Session 54) — `tests/infra/test_orchestrator_e2e.py::test_refusal_ashtakavarga_still_unbuilt`
   asserts router-level refusal via `_UNBUILT_MODULE_KEYWORDS`. Router
   wiring for ashtakavarga MUST update this test in the same change —
   expected designed failure, not a regression." Verified before writing:
   the test and `_UNBUILT_MODULE_KEYWORDS` both exist as cited
   (`tests/infra/test_orchestrator_e2e.py:401`, `agent/infra/calc_router.py:90`).

## Post-deletion full test suite
Run as `python -m pytest tests/ -q` (bare `pytest -q` from repo root also
collects PyJHora-main's own vendored test dir, which fails on
missing `geocoder`/`PyQt6` — pre-existing, unrelated to this change, scoped
out by pointing at `tests/`):

```
1895 passed, 3 skipped, 1 warning in 94.45s (0:01:34)
```

Matches the required baseline exactly. No import failures from the stub
deletion — deletion stands, no revert needed.

Files touched this turn: CLAUDE.md, "ASTRO AGENT — MASTER BUILD PLAN.md",
deleted bav.py/sav.py, this file. `diagnostics/calc_router_stage2.log` also
shows a 16-line append (STAGE2_VARIABLE test-run log growth, benign,
per CLAUDE.md's own note on that file).
