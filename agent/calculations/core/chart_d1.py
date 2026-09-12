"""
agent/calculations/core/chart_d1.py

=====================================================================
THIS STUB IS DELIBERATE AND PERMANENT. DO NOT IMPLEMENT IT.
=====================================================================

The D1 (Rasi) chart is ALREADY BUILT AND IN PRODUCTION. It lives in
`agent/chart_calculator.py::calculate_chart()`, which returns, per planet,
`planetary_positions[<planet>] = {house, sign, dignity, retrograde,
longitude}` plus `house_lord_mapping`, `conjunctions`, `aspects_by_planet`,
`aspected_by` and `yogas_doshas`. Nothing about the D1 chart is missing.

WHY THIS FILE IS EMPTY
----------------------
It is one of the "45 empty placeholders" created by the Phase-0 package
skeleton commit `f5cf073`. The refactor that would have filled it -- P1.1 /
P1.4, moving `chart_calculator.py` into `calculations/` behind a shared
`Chart` dataclass -- was ABORTED AT S22/S24 BEFORE ANY CODE WAS WRITTEN.

  SESSION_LOG_ARCHIVE_S19-S66.md:73 --
  "Chart/VargaType prep task aborted before any code was written: grep
   confirmed no Chart dataclass exists anywhere in the codebase, and
   calculations/core/panchanga.py's functions take raw (datetime, latitude,
   longitude) primitives directly, not a chart object -- wiring the
   requested guard-rail pattern would have required adding a new parameter
   to ~9 function signatures, which the task explicitly forbade. Paused and
   re-scoped with Sulabh rather than inventing infrastructure nothing
   consumes."

The whole package settled on PRIMITIVES instead of a shared chart object --
that is why `vargas/navamsa.py` is `compute_navamsa(jd_ut, asc_lon_sidereal)`
and not `compute_navamsa(chart)`. Filling this stub would reintroduce the
architecture that decision rejected.

WHAT TO DO INSTEAD
------------------
Whatever you were about to compute here, `calculate_chart()` already returns.
RESTATE it; never recompute it.

  - Need planet positions in the interpreter's fact block?
        -> extend `agent/astro/chart_facts.py` (the restate-don't-compute
           adapter) and `agent/astro/pipeline.py::_fact_block`.
  - Need a new field the calculator does not yet surface?
        -> add a regression test to the production path FIRST, then expose
           it there (the S127 pattern: `53b90f3` characterization test for
           16 D1 fields, then `a65cb4c` surfaced per-planet longitude --
           a value already computed internally and discarded, no new
           ephemeris call).

STANDING INSTRUCTIONS THAT SAY THE SAME THING
---------------------------------------------
  SESSION_LOG.md:508     "chart_d1 stub is DELIBERATE ... do NOT rewrite
                          the stub."
  claude_handover_S126.md  same, verbatim.
  CLAUDE.md                DESIGN-INTENT-FIRST known-intentional list.
  diagnostics/KNOWN_PATTERNS.md  P-022.

Sessions have now mistaken this file for pending work more than once. If you
are reading it because a plan said "implement chart_d1", the plan is wrong:
read `docs/ANSWER_PATHS.md` and the three sources above before writing
anything.
"""
