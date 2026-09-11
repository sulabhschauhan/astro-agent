# ASTRO AGENT — S127 HANDOVER (written at S126 close, 2026-09-11)

> **Tombstone this file the moment S127 closes.** A stale handover is confidently wrong.

MODEL: Opus for the design decision. Sonnet 4.6 for Claude Code implementation.
State the model on the first line of every Claude Code prompt.

## READ THIS ORDER, THEN TRUST IT — do not re-derive
1. `CLAUDE.md` — Current Session Focus + Locked Decisions. **AUTHORITATIVE.**
2. `SESSION_LOG.md` § S126 — the evidence behind every number below.
3. `ASTRO AGENT — MASTER BUILD PLAN.md` — the map.

## WHERE THINGS STAND — the answer pipeline is COMPLETE and COMMITTED
`question → plan → select → build → interpret (gpt-5) → silence gate → answer`
runs end to end. Suite **3938 passed / 7 skipped / 0 failed**.

| Stage | File | State |
|---|---|---|
| 1 Planner | `agent/astro/planner.py` | committed; window/ceiling config for gpt-5 |
| 2 Select | `planner.select_units` + `filter_segments_by_domain` | committed; 16-domain, Fix1 applied |
| 3 Build | `agent/astro/payload_builder.py` | unchanged |
| 4 Interpreter | `agent/astro/interpreter.py` | **NEW, committed** — gpt-5, structured claims, ghost guard |
| 5 Pipeline+Gate | `agent/astro/pipeline.py` + `silence_gate.py` | **committed** — `answer_question` wires it all |

## CLOSED — DO NOT RE-OPEN (S126 burned time re-opening these; don't)
- **Interpreter model is gpt-5. Validated on real calls** (`scripts/validate_model.py`, `diagnostics/latest_run.md`): 0 ghost citations, honest refusal, 105k-token recall, ~$0.16/big-Q, one 400k call. Luna/mini are REJECTED (41.3% long-context recall). Do not re-benchmark models.
- **Selection speaks ONLY the locked 16 domains** (S124). There is NO topic/rule_type/facet axis, and there will not be one without a lock change. `segment_tags_bphs_career3.json` (segtag-2.0) entity-tagging is on the S124 REJECTED list. `property` is a domain; there is no `property_home`. **Do not build a new tagging layer — S126 tried, it was wrong, it was reverted.**
- **Demoting the relation funnel was TESTED and REJECTED** — it only enlarges payloads. Leave it.
- **Never narrow, never fail-open to silence doctrine.** Window is solved by the 400k model; TPM by tier. Sub-tagging / per-query LLM filters are narrowing judges — rejected.

## MEASURED — cite, do not re-derive
- gpt-5: `INTERPRETER_CONTEXT_WINDOW=400_000`, `HARD_CONTEXT_CEILING=225_000` approx (planner.py). `reasoning_effort=minimal`. Corpus-first prompt → automatic 90% cache (~24h TTL) on the user-independent verse block.
- Fix1 cut `timing_dasha` 252→38 segs (ch46 computation + ch61/62/63 suppressed sub-dasha); marriage-timing 158k→113k real, zero doctrine lost.
- gpt-5 cleared 105k prompt tokens with no 429 → TPM headroom is fine at this tier.

## NEXT TASK — the calculation stubs `vimshottari` + `chart_d1`
gpt-5's honest refusal on "when will I marry" is the proof: the FACT BLOCK today is only the chart's lord→house map + ascendant, so timing and planet-placement questions cannot be answered. Build `vimshottari` (running dasha) + `chart_d1` (planet positions) FIRST — they widen the fact block, unlock every "when" question, and retire the AstroSage PDF. Each carries the 4-reference-chart validation protocol (`calculations/` package; PVR book + JHora oracle; empirical validation across the 4 charts, zero free parameters). The silence gate's coverage widens automatically as the block grows — no new gate code.

Then: the **vision / palm track** (new work; palm rules engine is already COMPLETE for V1 per S125 — this is a separate vision effort, scope it in the next session with Sulabh).

## WORKING STYLE REMINDERS THAT MATTERED THIS SESSION
- The Cowork sandbox is FIREWALLED from api.openai.com — any GPT run goes on Sulabh's machine (hand him a Claude Code prompt that writes to `diagnostics/latest_run.md`).
- Source commits need the literal line `RATIFIED: commit authorized`. Docs/diagnostics are exempt.
- Before calling anything "unfinished" or proposing a new mechanism, SEARCH the locked decisions + REJECTED-APPROACHES list in SESSION_LOG (DESIGN-INTENT-FIRST, S123). S126's biggest time-sink was proposing a tag layer already rejected at S124.
