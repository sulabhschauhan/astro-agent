# Session: compute_bav_contributors() — Prastaara kakshya-scoring support

**Changed file:** `agent/calculations/ashtakavarga/ashtakavarga.py` (only
file changed besides the benign `calc_router_stage2.log` growth from
running the suite; `git status` confirms it). `compute_bav`, `compute_sav`,
and `AV_TABLES` untouched except the new CITATION item (e).

**New function:** `compute_bav_contributors(placements) ->
dict[owner][sign] = frozenset[str]` — per-cell contributor-name sets
(which of Sun..Saturn/Lagna donate a bindu), for future Prastaara
Ashtakavarga transit kakshya scoring (PVR ch. 25.5.2, Table 60: a kakshya
has a rekha iff the transiting planet is benefic in the rasi w.r.t. that
kakshya's lord — needs contributor identity, not just the bindu count).

**Design — no duplicated validation or table data:**
- Calls `compute_bav(placements)` first, which performs all input
  validation (missing/unknown contributor keys, unrecognized signs) and
  raises the identical `ValueError`s — no validation code duplicated.
- Reuses the same `AV_TABLES` and Aries-absolute indexing convention;
  iterates the same `(reference, house)` structure as `compute_bav` but
  accumulates contributor names into a `set` per cell instead of a bindu
  count, since tracking identity (not just count) is the whole point of
  this function. This loop is structurally similar to `compute_bav`'s but
  isn't literal duplication of table data or validation — it's the
  necessary set-accumulation variant of the same table walk.

**SELF-INVARIANT (oracle-lock by construction):** for every (owner, sign),
asserts `len(contributor_set) == compute_bav(placements)[owner][sign]`,
naming owner+sign on failure. Since `compute_bav` is already 96/96
per-cell JHora-validated on David (Session 54), this makes
`compute_bav_contributors` correct-by-construction against the same
oracle without a second, separate fixture.

**Out of scope (left to a future transit-scorer module, per the docstring
and CITATION (e)):** kakshya lord order (Saturn, Jupiter, Mars, Sun, Venus,
Mercury, Moon, Lagna; 3d45' divisions) and the transit scoring itself.

**Smoke-check (not committed as a test):** ran the invariant across all
384 cells (4 reference charts x 8 owners x 12 signs — David hardcoded,
Sulabh/Surbhi/Sheridan derived live via `calculate_chart()`, same pattern
as `test_ashtakavarga_cross_charts.py`). All 384 cells passed;
throwaway script deleted after the run.

## Test tallies
- Full suite: `2348 passed, 3 skipped, 1 warning` — unchanged (no new test
  file this prompt, per instructions; existing suite still green after the
  addition).

No existing test file, `compute_bav`, `compute_sav`, or `AV_TABLES` logic
changed.
