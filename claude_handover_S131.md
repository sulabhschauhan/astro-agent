# HANDOVER -> S132 (written at end of S131, 2026-09-13)

**RECOMMENDED MODEL: Sonnet 4.6** for the Neecha Bhanga module and the fact-block
wiring. Opus only for: the fact-block growth-contract decision, or debugging stuck
after 2 attempts.

---

## 0. READ THESE FIRST

1. `CLAUDE.md` — the **S130 lock** and the **S129b lock**.
2. `diagnostics/KNOWN_PATTERNS.md` rows **P-022 .. P-025**.
3. `SESSION_LOG.md` -> `## S130`, then this file.
4. `agent/astro/composer.py` module docstring — the Stage 5b contract.
5. `agent/calculations/yogas/detector.py` module docstring — the yoga contract.

Rules 32/33/34 bind you: never assert from memory or a summary — including this
handover — when a primary source is available.

---

## 1. STATE OF THE TREE

**S130 IS COMMITTED** as `b6bcc54` on `wip/interpretive-pilot`, parent `c0d6c70`.
Read that SHA from `git log`; do not trust this line alone.

**CORRECTION CARRIED FROM S131:** `CLAUDE.md:8` and `SESSION_LOG.md` §S130 both
still say S130 is "Uncommitted on `wip/interpretive-pilot` atop `c0d6c70`". They
were written ~70 seconds before the commit and never updated. Two stale
documents; fix opportunistically, do not treat them as evidence of tree state.

**S131 IS UNCOMMITTED**, written on top of `b6bcc54`:

| file | state |
|---|---|
| `agent/astro/composer.py` | NEW — Stage 5b |
| `agent/astro/pipeline.py` | composer wired after the gate, **OFF by default** |
| `agent/astro/answer_view.py` | prefers composed output when present |
| `agent/calculations/yogas/detector.py` | Phase-0 stub FILLED |
| `agent/calculations/yogas/catalog/raja_yogas.py` | Phase-0 stub FILLED |
| `agent/calculations/yogas/catalog/special.py` | Phase-0 stub FILLED |
| `scripts/replay_capture.py` | `--compose` flag added |
| `scripts/probe_composer_guards_S131.py` | NEW |
| `scripts/probe_composer_e2e_S131.py` | NEW |
| `scripts/probe_yoga_detector_S131.py` | NEW |

Suite: **4123 passed, 7 skipped, 5 deselected**, unchanged before and after.
**VERIFY WITH `python -m pytest -q -m "not integration"`, never a bare `pytest`.**

---

## 2. WHAT S131 BUILT, AND WHY

### 2a. STAGE 5b — THE COMPOSER (`agent/astro/composer.py`)

**The decision that produced it.** S130 left answer SHAPE as the biggest gap. S131
first designed a deterministic scorer + verdict-templates-by-set-topology.
**Sulabh rejected it** and he was right: scoring logic and topology conditions
would need a new branch per question shape, and the thresholds would multiply
(Working Style #4). REPLACED BY: a second, tiny LLM call whose only input is the
gated claim set. Do not re-propose the scorer.

**Measured, not assumed** (`diagnostics/qa_capture/20260913T065603Z.md`): composer
input is 553 and 312 tokens of claims against **185,297** interpreter prompt
tokens on the same turn — ~0.8%. Live: `prompt_tokens` 1176 / 766.

**Interpreter prompt UNCHANGED.** That is deliberate and worth preserving: every
`_SYSTEM_HEAD` edit is a live-run trigger against a 185k payload, and the composer
takes shape work off it entirely.

**What replaces the S129b no-rewrite rule.** `answer_view` was locked against
rewriting AND re-ordering claim text. The composer does both, so the prohibition
is replaced by two mechanical checks in `composer._verify`:
  1. **ENFORCING — no new chart facts.** A rewrite may not contain a chart token
     (house ordinal / graha / sign / dignity) absent from the claim it rests on.
     Closed vocabulary, set containment, NO prose parsing — deliberately not the
     clause-reading whose negation guard proved clause-blind (S130 §6). A failing
     block DEGRADES to the original claim text; it is never dropped.
  2. **ADVISORY — conditions survive.** Recorded in `condition_advisory`, not
     enforced. A keyword test cannot distinguish an unhedged rewrite from one
     carrying the condition in other words, and enforcing it would push most
     answers back to the jargon original. **Promotion to enforcing is gated on
     the measured rate, exactly as the planet reader was (S129b (4)). Do not
     promote on intuition.**
  3. Coverage: every input claim is rendered or explicitly demoted; anything
     unaccounted for is restored automatically (`unaccounted_restored`).

`answer_view`'s docstring still carries the S129b "does not re-order" sentence
with an S131 note explaining that the re-ordering is the composer's and is
mechanically checked. **That lock was never formally amended by Sulabh** — he
approved the design, not a lock edit. Treat the amendment as UNRECORDED and take
it to him if it matters.

**LIVE RESULT (2 turns, real gpt-5, via `replay_capture --compose`):** 0 invented
facts across two independent calls. Both answers led with a verdict, both flagged
verified vs unverified per claim, both closed with what was not assessed. Full
before/after text in `diagnostics/latest_run.md` (copy archived under
`diagnostics/runs/`). gpt-5 is not deterministic call-to-call; two calls differed
in wording and in whether the advisory fired. That is expected, not a defect.

**OPEN — jargon.** "angle–trine" survived into 5 of 6 claim blocks, unglossed.
Sulabh REJECTED a prompt blocklist as hardcoding: "we cant harcode block for each
of these kinds of issues". Two general routes, neither chosen: (a) reframe the
prompt rule from a banned-word list to a principle plus a self-check, or (b)
DERIVE a jargon lexicon from the corpus (frequent in BPHS, rare in ordinary
English) rather than enumerating one. Same SSOT reasoning as
`feature_needles.py` and `ontology_registry.json`.

**OPEN — condition drop, OBSERVED ONCE.** Turn 1 claim 0: the source said
"especially WHEN that 1st lord also rules the 4th…", the rewrite stated it as
settled. Caught, logged, not blocked — by design. Sulabh: "lets keep this in
mind, no action as of now."

### 2b. THE YOGA DETECTOR (`agent/calculations/yogas/`)

**The decision that produced it.** S131 argued the ruled-out set could not come
from the model, because outside knowledge is barred (S124). **Sulabh challenged
this and was right.** VERIFIED against `data/chapter_index_bphs.json`: Gajakesari
is in `bphs1_ch36`, the Vipareeta trio (Harsha/Sarala/Vimala) in `bphs2_ch48`,
Neecha in `bphs1_ch24`. Further: **all four chapters were already selected and
shipped in the 065603Z turn** (46 units selected). The doctrine was in front of
gpt-5 and went unused; `ch48_s001` even appears in that turn's `ghost_citations`,
i.e. the model reached for the Vipareeta chapter and the addressing bug threw the
citation away. Ruling-out is a CALCULATION we can do, not outside knowledge.

**PRE-FLIGHT DONE (P-024).** Before building: `agent/calculations/yogas/` had
`detector.py`, `raja_yogas.py`, `neecha_bhanga.py`, `dhana_yogas.py`, `special.py`
as docstring-only Phase-0 stubs, and `pancha_mahapurusha.py` REAL and built (3,322
bytes, uses `agent.calculations.core.dignity.get_dignity_status`) — **and wired to
nothing.** `chart_calculator._calc_yogas` returns ONLY `mangal_dosha` and
`kalsarpa_yoga`; it has no raja-yoga logic to restate.

**CONTRACT.** `detect_yogas(chart_facts) -> YogaReport`. Pure arithmetic over the
already-computed fact block: no ephemeris, no `chart_calculator` import, no chart
fact computed (S124 + S20 both hold by construction). **NEVER RAISES** — a bad
rule costs a yoga, never the answer. Catalogue modules are plain
`detect(facts) -> list[dict]` functions so nothing in `catalog/` imports
`detector`; there is no cycle.

**EVERY RULE RETURNS A NOT-FIRED REASON.** That is the point, not a nicety.

**VALIDATED 6/6 against `Output.txt`** (the Claude-desktop benchmark for this same
chart — Sagittarius lagna, confirmed identical chart from the capture's own
`chart_facts`). `python -m scripts.probe_yoga_detector_S131` -> RESULT: PASS.

| rule | expected | got |
|---|---|---|
| Dharma-Karmadhipati | FIRED | FIRED |
| Sarala (VRY) | FIRED | FIRED |
| kendra_trikona_4_5 (Mars aspects Jupiter) | FIRED | FIRED |
| Harsha (VRY) | RULED OUT | RULED OUT |
| Vimala (VRY) | RULED OUT | RULED OUT |
| Gajakesari | RULED OUT | RULED OUT |

**CONTESTED DEFINITION, DELIBERATELY NOT RESOLVED.** The Vipareeta rules carry
`contested=True` + `contested_note`: Uttara Kalamrita requires the dusthana lord
in one of the OTHER two dusthanas; later compilations also count its own. The
module takes the UK reading — the same one the benchmark used to rule out Harsha.
**Do NOT widen the condition to "fix" it.** That is the Tiebreaker-principle call
and it is Sulabh's.

**DUPLICATE-LOOKING HITS ARE BY DESIGN, RULED S131.** 7 fired rows include
`kendra_trikona_7_9` and `kendra_trikona_10_9`, both resting on the same physical
Sun+Mercury conjunction. Sulabh ruled: **"Our composer will automatically merge
them we need not to do anything."** Do not add a dedupe pass, and do not re-raise
this as a defect.

---

## 3. IMMEDIATE NEXT STEPS (in order)

### 1. NEECHA BHANGA (`catalog/neecha_bhanga.py`, still a stub)
The last of the benchmark's four yogas. Needs three things the other modules did
not: **dignity** (present — nested in `planet_positions.<graha>.dignity`, head
only: Exalted / Debilitated / Own Sign), the **dispositor** (the lord of the sign
the debilitated planet sits in — derivable from `house_lords` + `planet_positions`,
no new calculation), and the **D9 route** (`navamsa.placements`, which carries its
own `dignity`).

Expected on Sulabh's chart: Moon debilitated in Scorpio (12th); dispositor Mars
EXALTED in Capricorn -> cancellation fires. The benchmark calls this "[Certain] on
the rule, [Likely] on real-world strength" — note it reports confidence on TWO
axes, which the verdict shape may want to carry.
**STILL OUT, deliberately (S130 lock):** exaltation DEGREES. The tables carry
signs only, so deep-exaltation and degree-keyed Neecha Bhanga variants are
unreachable. **Do not synthesise them.**

### 2. WIRE THE YOGAS INTO THE FACT BLOCK
`pipeline._fact_block` widens -> **`capability_gate.FACT_BLOCK_PROVIDES` MUST gain
the matching key IN THE SAME CHANGE.** `tests/astro/test_capability_gate.py` pins
them together and WILL fire; that is the contract working. Also pinned:
`test_fact_block_stays_byte_identical_for_a_legacy_facts_dict`.
The fired set becomes facts; the ruled-out set becomes the "what I am ruling out"
material. Decide whether ruled-out enters the fact block or is handed to the
composer separately — it is not doctrine the interpreter needs, it is an answer
ingredient.

### 3. TURN THE COMPOSER ON AND MEASURE
`ASTRO_COMPOSER_ENABLED=1`, or `compose=True` per call, or
`replay_capture --compose`. Watch `violations` (must stay empty) and the
`condition_advisory` rate (the promotion metric).

### 4. THEN, unchanged from S130's list
- The silence gate's negation guard is clause-blind; `ungated_pct` measured
  **66.7%** (raja yoga turn) and **100%** (Saturn turn). On the Saturn turn the
  composer has NO verification signal to rank by. This now blocks composer
  quality, so it has risen in priority.
- Planner selects 14/16 domains, 81 units, 185k–229k prompt tokens,
  `cached_tokens` 0 on six of seven turns.
- `planetary_nature` is a glossary domain the planner picks alone.
- Advisory planet reader: still HOLD.

---

## 4. TRAPS (S130's, all still live — plus S131's)

- **`gate.verdicts` never leaves the pipeline.** Computed in
  `apply_silence_gate`, consumed only by `render_audit` and `to_dict`;
  `answer_question`'s return dict does NOT carry it. The composer reaches it
  in-process at `pipeline.py`'s gate call. Verified by repo-wide grep.
- **Claims carry no id.** `composer._claim_rows` assigns positional ids by
  re-deriving the kept partition from `gate.verdicts`, which is in claim order.
  If you ever change how kept/dropped is partitioned, that alignment breaks.
- **The capture's per-claim verdict join key is `statement[:160]`**
  (`gate_stats.advisory_detail`). Two claims sharing a 160-char prefix collide.
  `scripts/probe_composer_guards_S131.py` joins POSITIONALLY instead.
- **`fact_block` is not in the capture** — `chart_facts` is, and `_fact_block()`
  is deterministic, so it is reconstructible. Do not look for a section.
- **Seven fact CLASSES, six top-level `chart_facts` keys.** `dignity` is NESTED
  in `planet_positions`, present only for Exalted / Debilitated / Own Sign.
  `chart_facts["dignity"]` raises KeyError.
- **`interpreter.py`'s module docstring is STALE** — still says "PATH B / LAB
  TRACK — NOT WIRED TO THE PRODUCT (S128 lock). This module has NO non-test
  caller." False since S129. First thing a session reads in that file.
- **A file-delivery path is NOT reusable.** Deliver every file through a fresh,
  uniquely named staging path and re-read it afterwards. S131 used `S131a/b/c`
  prefixes and verified each write by grepping for a string only the new version
  contains.
- **CRLF**: the Windows tree is CRLF. Convert or the diff is whole-file.
- Everything in `claude_handover_S130.md` §5 still applies.

---

## 5. WORKING PROTOCOL (Sulabh's, non-negotiable)

- Expert-to-expert. **Work silently; reply very briefly, in layman terms.** No
  long structured write-ups unless asked. Usage is tight.
- **You do the coding.** Write files into the repo and name the path. **Never
  deliver source as chat file-cards** — S131 did this once and was pulled up for
  it.
- **REVIEW before PROCEED** — flag at least one issue before approving any edit.
- **SAMPLE before SCALE. HARDEST CASE first. SURGICAL EDITS.**
- **One prompt, one task.** Never proceed without confirmation.
- **Commits are Sulabh's.** Never commit without the literal line
  `RATIFIED: commit authorized`.
- Every codebase claim carries **branch + commit SHA**, or say you did not read it.
- **"X does not exist" is never sayable alone** — only "X not found in \<paths\>
  on \<branch\>@\<sha\>". A contradiction from Sulabh is a **STOP** signal:
  re-verify the SOURCE. S131 hit this twice and Sulabh was right both times.
- State the recommended model as the first line of every Claude Code prompt.
