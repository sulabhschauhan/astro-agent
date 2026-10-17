# Dated-Compose Socket — Design (S152)

Status: DESIGN CLOSED, ratification pending. Supersedes the S151 "generic
dated-compose socket deferred" lock (the trigger has fired). Reverses two prior
decisions (flagged below) — both require Sulabh's explicit ratification before
any source commit.

## 1. Decision

One uniform socket. All four dated capabilities — muhurta, combustion, graha
ingress, masa — plug in the SAME way:

    build the capability's events into the per-chart timeline file over a fixed
    forward window  ->  a question FILTERS its stored slice by a typed param
    ->  render into the fact block  ->  interpreter explains, never computes
    ->  a request beyond the window rebuilds that one slice live.

There is no "live vs stored" split and no `kind` field. My earlier two-kinds
framing was wrong once cost was removed: a full-year muhurta scan is swisseph
CPU-seconds, not LLM tokens (Sulabh's correction). With cost off the table,
muhurta stops being special — its question horizon ("next month" / "next 2
years" / "next 5 dates") becomes a FILTER over a stored window, exactly like
ingress's {planet, house}.

### Lock reversals (conscious supersede — Sulabh to ratify)

- **R1. Muhurta is now STORED, not live-composed.** Reverses S151
  ("MUHURTA IS LIVE-COMPOSED, NOT STORED"). Basis: the cost premise behind that
  lock is invalid (CPU, not tokens). Sulabh drove this reversal in S152 chat.
- **R2. `timeline_store.WINDOW_DAYS` 365 -> 730.** One window subsumes muhurta's
  natural 2-year horizon so all four share one store and one re-anchor.
  THRESHOLD DISCIPLINE: 730 = muhurta's locked MAX_SCAN_DAYS (S147). Scope: the
  shared Tier-A sky scan + per-chart projection window only. Tuning note: Tier-A
  cost is ~2x a 1-year scan (cheap, shared across all charts); Saturn's next
  ingress (~2.5 yr/sign) can still fall beyond 730 -> live path handles the
  remainder, by design (do not chase 100% in-store). `REANCHOR_TAIL_DAYS` stays
  90.

## 2. Registry schema additions (`capability_registry.Capability`)

Three new typed fields; additive, so existing rows stay valid:

- `builder: str | None` — dotted ref to the fact builder
  (`"agent.astro.combustion_facts:build"`). The dispatcher resolves it lazily
  (keeps the registry a leaf module — no agent.* import at module load).
- `param_schema: dict` — the closed, typed filter shape the planner fills for
  this capability (see 4). The ONE typed-param mechanism the S151 lock asked for,
  defined once.
- `horizon_days: int = 730` — this capability's forward window.

`dated=True` now means "has a builder + horizon_days + lives in the timeline
file" for all four. `plan.muhurta_horizon` is RETIRED as a one-off on `Plan`;
its content moves into muhurta's `param_schema` fill, so no capability hangs a
bespoke param on `Plan` again (the P-030 anti-pattern).

## 3. Dispatch (in `pipeline.answer_question`)

Replaces the bespoke `if "muhurta" in capabilities` block (pipeline.py:689-709):

1. Collect the dated capability ids present in `plan.capabilities`.
2. Ensure the per-chart timeline file covers them: ONE
   `load_timeline_for_chart` call builds/loads the trio's slices from a SINGLE
   Tier-A sky load; muhurta's slice is built by its own per-chart scan into the
   same file. (The trio share Tier A; muhurta cannot — that is the only residue
   of "two kinds", and it is internal to the builders, invisible to the socket.)
3. For each present capability: filter its stored slice by the planner's
   `param_schema` values -> attach under its `fact_key` in `chart_facts`.
4. A requested target outside `horizon_days` -> rebuild THAT slice live with an
   extended horizon (same builder, bounded scan). Ingress uses the S148 measured
   crossing-rate bound — NOT a sampling rate (locked).

`_fact_block` rendering becomes generic: iterate the fired dated capabilities,
render each slice under its `interpreter_directive` from the registry. No
per-capability hardcoded render block.

## 4. Per-capability param shapes (`param_schema`)

| capability | filter param | from the question |
|---|---|---|
| muhurta | `{mode: "days"\|"count", value: int>0}` | "next month" / "next 5 dates" |
| ingress | `{planet: str, house: int 1-12, ref: "lagna"\|"moon"}` | "when does Saturn enter my 7th" |
| combustion | `{planet?: str}` | "when is Mercury combust" (omit = all) |
| masa | `{date?: iso, month?: int}` | "which month is it" (omit = current) |

All are FILTERS over already-computed stored events. The planner fills whichever
schema matches the routed capability; `validate_plan_object` checks it against
the closed schema (same posture as domains/capabilities today).

## 5. Build sequence — six one-task prompts (Sonnet, LLM: none, -> latest_run.md)

Each is independently testable; suite must be green before the next.

1. **Schema + muhurta migrate (behaviour-neutral).** Add the three Capability
   fields; move muhurta onto `builder`/`param_schema`/`horizon_days`; retire
   `plan.muhurta_horizon` into muhurta's param fill. Muhurta STILL live-composed
   here (no store yet) — pure plumbing, S64 goldens byte-pinned.
2. **Window 365 -> 730 (R2).** `WINDOW_DAYS`, Tier-A scan, projection, re-anchor
   test. Threshold-discipline note in code.
3. **Generic dispatch + fact_block + FIRST capability: combustion.** Combustion
   is fully in-window, clean intervals, no beyond-horizon branch — the cheapest
   socket proof. SAMPLE-before-SCALE: one fixed captured chart + pinned `as_of`,
   oracle-validate the combustion dates (reuse the S147 Surya-Siddhanta orbs /
   external solar-conjunction dates), suite green. Growth contract: add
   `combustion` fact_key to `FACT_BLOCK_PROVIDES` in the SAME change.
4. **ingress** — adds the `{planet, house, ref}` filter + the beyond-horizon live
   branch (S148 rate bound). Validate ingress dates against JHora (P-027: oracle
   grades the answer, never an input).
5. **masa** — placement facts only; `name_sa=None` unless sankranti_count==1
   (locked, do not name the intercalary month). Trivial once 3-4 land.
6. **Muhurta fully onto the stored/filtered path (R1).** Build muhurta's 730-day
   window into the file; question filters the stored windows; keep live-rebuild
   for >730d or an unsatisfiable want_count. HIGHEST regression surface (S64
   goldens + the live Streamlit electional/prediction routing) — last, pinned.

## 6. Agent roster — surfaced conflicts only

- **Conflict (Debate): sequencing.** Business wanted ingress first (highest user
  value: "when does Saturn enter my 7th"). QA + Critic wanted the cheapest
  mechanism proof first (no beyond-horizon branch). RESOLVED: combustion first as
  the socket proof (step 3), ingress second (step 4) once the mechanism is green.
  Business value is deferred by exactly one prompt, not lost.
- **Ephemeris Auditor (HIGH, unopposed):** beyond-horizon ingress MUST use the
  S148 measured rate bound; re-stated in step 4. Muhurta stored windows re-anchor
  like any dated slice.
- **Validation Source (HIGH, unopposed):** every ingress/combustion/masa date is
  oracle-validated before its capability ships; registration stays self-sourcing
  (no row without a backing, validated builder).
- No other conflicts. UI/UX (no upsell), Architect (uniform socket) concur.

## 7. Not re-litigated (ruled)

Masa intercalary naming stays withheld (no corpus source). No-upsell /
self-sourcing / one-registry-route stand. do's-don'ts + remedies wait for Lal
Kitab ingestion.
