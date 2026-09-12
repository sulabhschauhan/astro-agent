# ASTRO AGENT — S127 HANDOVER (written at S126 close, 2026-09-11)

> **Tombstone this file the moment S127 closes.** A stale handover is confidently wrong.

MODEL: Opus for the design decision. Sonnet 4.6 for Claude Code implementation.
State the model on the first line of every Claude Code prompt.

## READ THIS ORDER, THEN TRUST IT — do not re-derive
0. **CONFIRM you are on `wip/interpretive-pilot`** (`git branch --show-current`). `main` is stale at S84 — building on it silently drops the whole pipeline. `wip` @ `a0569b0` is self-contained (clones clean, 3938 pass). If the project RAG surfaces S84-era content, the GitHub sync still points at `main` (repoint it to `wip/interpretive-pilot` in project settings) — until then, trust these docs over RAG. Detail: SESSION_LOG § "S126 close addendum".
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
- **The `parked_cost_reduction` item is SUPERSEDED — do not resume it.** S126 overtook it: its top lever (gpt-4o-mini interpreter) is REJECTED (mini = 41.3% long-context recall, cites wrong verses); its prompt-caching sub-idea is ADOPTED (gpt-5 automatic 90% cache + corpus-first prompt); per-question cost is already ~$0.16 (~$0.03 cached) and nothing refuses over ceiling. Only remnant (cache the interpreter ANSWER for chart-independent questions) is LOW priority. The doc was removed from the project.

## MEASURED — cite, do not re-derive
- gpt-5: `INTERPRETER_CONTEXT_WINDOW=400_000`, `HARD_CONTEXT_CEILING=225_000` approx (planner.py). `reasoning_effort=minimal`. Corpus-first prompt → automatic 90% cache (~24h TTL) on the user-independent verse block.
- Fix1 cut `timing_dasha` 252→38 segs (ch46 computation + ch61/62/63 suppressed sub-dasha); marriage-timing 158k→113k real, zero doctrine lost.
- gpt-5 cleared 105k prompt tokens with no 429 → TPM headroom is fine at this tier.

## NEXT TASK — widen the FACT BLOCK via `vimshottari` + `chart_d1` (read the corrections FIRST)
gpt-5's honest refusal on "when will I marry" is the proof: the FACT BLOCK today is only the chart's lord→house map + ascendant, so timing and planet-placement questions can't be answered. Widening it is the next work — but three corrections to earlier phrasing (verified vs archives S22–S76; full detail in SESSION_LOG "S127 build-guidance correction"):
- **`vimshottari` unlocks RANGE-level "when" (which mahadasha/antardasha), NOT day-precise dates.** Gap D1 (S75/S76, ratified) already excludes day-precision from V1 (row-0 residual −0.33 to −2.66d, apparent-Moon convention). MD/AD logic already lives in `agent/chart_calculator.py` (S44: "import the real logic, don't touch the stub") — extract-and-wire WITH regression coverage first, not greenfield.
- **`chart_d1` is a deliberate stub** (P1.1 Chart-dataclass refactor aborted S22/S24 — consumers take primitives). `calculate_chart()` is the production D1 path with ZERO regression coverage and exposes sign/house/dignity, not raw longitudes. To surface planet positions: **regression-test the production path FIRST (HARDEST-CASE-FIRST), then expose longitudes — do NOT rewrite the stub.**
- **AstroSage STAYS in V1** (ratified S68). "Retire AstroSage" was an aspiration, not a decision — don't build toward removing it; removal is contingent on the engine demonstrably covering its outputs.
Each module carries the 4-reference-chart validation protocol (`calculations/`; PVR book + JHora oracle; 4 charts, zero free parameters). The silence gate's coverage widens automatically as the block grows — no new gate code.

Then: the **vision / palm track** (new work; palm rules engine is already COMPLETE for V1 per S125 — this is a separate vision effort, scope it in the next session with Sulabh).

## HOUSEKEEPING BACKLOG (not blocking; Sulabh flagged S126)
- **Split `diagnostics/` — it conflates ephemeral output with durable cited evidence.** The folder name says "throwaway" but it also holds the `_S<n>.md` reports, `KNOWN_PATTERNS.md`, golden scorecards and `dogfood_capture.md` that locked decisions cite (a cleanup had to hand-guard them). Refactor: `diagnostics/` = ephemeral only (`latest_run.md`, `runs/`, `*.log`, scratch — gitignore the whole dir); new `audit/` (git-tracked, "do-not-touch") = the cited evidence. Migrate with `git mv` (keeps history), update `.gitignore` + the CLAUDE.md diagnostics convention, and add ONE SESSION_LOG note that pre-S127 `diagnostics/*_S<n>.md` citations now resolve under `audit/` (cheaper than re-pointing ~50 citations). It touches a documented convention (WS#21/#26) so treat it as a deliberate refactor, not a quick move.
- **Content-role tagging (`ingestion/chunker.py` + `embedder.py`) was DRAFTED then REVERTED at S126** (undocumented, incomplete — no upstream producer emits the values, so they were always `"unknown"`; V1 doesn't use the ChromaDB path). First half of the S115 HORIZON "ingest-time content-role tagging". To finish: (1) build producers in `pdf_processor.py`/`image_extractor.py` emitting real `text_source`/`content_class`, (2) re-add the lines, (3) re-embed. Reverted lines, so nothing is lost: `chunker.py` `_make_sub_chunks` add `"text_source": parent.get("text_source"), "content_class": parent.get("content_class"),`; `embedder.py` `_to_metadata` add `"text_source": chunk.get("text_source") or "unknown", "content_class": chunk.get("content_class") or "unknown",`.

## WORKING STYLE REMINDERS THAT MATTERED THIS SESSION
- The Cowork sandbox is FIREWALLED from api.openai.com — any GPT run goes on Sulabh's machine (hand him a Claude Code prompt that writes to `diagnostics/latest_run.md`).
- Source commits need the literal line `RATIFIED: commit authorized`. Docs/diagnostics are exempt.
- Before calling anything "unfinished" or proposing a new mechanism, SEARCH the locked decisions + REJECTED-APPROACHES list in SESSION_LOG (DESIGN-INTENT-FIRST, S123). S126's biggest time-sink was proposing a tag layer already rejected at S124.
