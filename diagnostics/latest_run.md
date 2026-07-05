# P9 thin-slice — combustion.py

**Date:** 2026-07-05 (Session 50)
**File created:** `agent/calculations/core/combustion.py` (implementation only).

## What was built
`compute_combustion(chart_data)` — Asta detection for Moon/Mars/Mercury/
Jupiter/Venus/Saturn. Orb table: Surya Siddhanta convention (12/17/14/11/10/15
deg), retro overrides Mercury 12, Venus 8. PVR silent on combustion orbs;
PyJHora Jupiter/Venus-swap and non-classical retro divergence documented in
module CITATION block, not followed.

## Smoke result
Import OK. Ad hoc functional check against calculate_chart() for Sulabh and
Surbhi matched documented anchors exactly: Sulabh zero combust (Mercury-Sun
14.6501 > 14 orb); Surbhi Mercury 3.6018 and Jupiter 4.9738 both combust.
