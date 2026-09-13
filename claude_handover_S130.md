# HANDOVER -> S131 (written at end of S130, 2026-09-13)

**RECOMMENDED MODEL: Sonnet 4.6** for the interpreter-prompt / answer_view work below.
Switch to Opus only for: the advisory-reader promote/hold decision, the silence-gate
negation-guard fix, or debugging stuck after 2 attempts.

---

## 0. READ THESE FIRST — DO NOT ASSERT ANYTHING BEFORE YOU HAVE

1. `CLAUDE.md` — the **S130 lock** and the **S129b lock** (read together; S130 is later).
2. `diagnostics/KNOWN_PATTERNS.md` rows **P-022, P-023, P-024, P-025**. P-024 and P-025 exist
   because of mistakes made in S130 itself. Read them before calling anything missing.
3. `SESSION_LOG.md` -> `## S130` (the last entry).
4. `docs/ANSWER_PATHS.md` — the two-path map.

Rules 32/33/34 bind you: **never assert from memory or from a summary — including this
handover — when a primary source is available.** This document is a map, not authority.

---

## 1. WHERE THE PROJECT STANDS

**Path B is the product.** `frontend/app.py` answers through the five-stage pipeline
(Planner -> Calculator -> Retriever -> Interpreter -> Verifier). Path A
(`agent/infra/orchestrator`) is retained, tested, intact, and wired to nothing.

**S130 IS COMMITTED** on `wip/interpretive-pilot`, on top of `c0d6c70`. Suite
217 -> **228 passed** in `tests/astro/`. Read the SHA from `git log` — this document
names none, because none existed when it was written (CODE-READ PROVENANCE).
Sulabh commits; never commit without the literal line `RATIFIED: commit authorized`.

**VERIFY BEFORE THE SUITE, ALWAYS:** `python -m pytest -q -m "not integration"`.
A bare `pytest` spends API credit — `pytest.ini` declares an `integration` marker for
real GPT calls and sets no `addopts`.

**THE S130 COMMIT CARRIES FOUR FILES THAT ARE NOT S130 WORK.** Sulabh folded in his own
in-flight changes at commit time: `scripts/astrosage_kundli_fetcher.py` (NEW — fetches the
AstroSage PDF directly from the web, removing the manual-upload step), plus `.gitignore`,
`requirements.txt` (adds `playwright`, which that fetcher needs) and
`diagnostics/gate_rule_citations_report.md`. The S130 commit message does not mention them.
If you are reading that commit to understand S130, those four are noise; if you are
wondering where the fetcher came from, it is Sulabh's, not S130's.

**Consequence worth knowing:** the AstroSage panel is still the covering surface that
retires only when the fact block covers its sections (S125 V1 ORDER) — the fetcher changes
how the PDF ARRIVES, not that plan. But it puts a live network fetch and a Playwright
dependency into the app's path, which is new, and it is not covered by any test in
`tests/astro/`.

**The fact block now carries:** `ascendant_sign`, `lord_house_map`, `planet_positions`,
`house_lords`, `aspects`, `dignity` (head only), `navamsa`. All seven are declared in
`capability_gate.FACT_BLOCK_PROVIDES` and pinned by `tests/astro/test_capability_gate.py`.

---

## 2. THE RULES THAT WILL BITE YOU IF YOU MISS THEM

1. **FACT-BLOCK GROWTH CONTRACT** — widening `pipeline._fact_block` REQUIRES adding the
   matching key to `capability_gate.FACT_BLOCK_PROVIDES` **in the same change**. A test pins
   them together and it WILL fire; that is it working, not a nuisance.
2. **A legacy `chart_facts` dict must keep rendering byte-identically.** Pinned by
   `test_fact_block_stays_byte_identical_for_a_legacy_facts_dict`. Break it and every replay
   of an old capture reports false diffs.
3. **`chart_facts.py` RESTATES, NEVER COMPUTES.** It imports no ephemeris, no sign table, no
   lord table. If your change needs one, the change belongs in the caller or the calculator.
4. **`chart_calculator.py` IS LOCKED (S20): "Don't touch chart_calculator. Don't retrofit D1."**
   S130 wired D9 without breaking this, because `meta.jd_ut` / `meta.asc_lon_sidereal` were
   already returned. Keep it that way.
5. **PRATYANTAR** — still unhooked. The block carries no dasha, so today's safety is
   ABSENCE, not a guard. Whoever adds dasha MUST add the suppression in that same change
   (±37d drift, wrong lord).
6. **LIVE RUNS COST REAL MONEY.** Required ONLY when: the interpreter prompt changed, the
   fact block gained a new fact class, model/config changed, or something is being ratified.
   Everything else -> `scripts/replay_capture.py`, zero API cost. **The Claude sandbox is
   FIREWALLED from api.openai.com** — verified S130, `CONNECT tunnel failed, 403`. Live runs
   happen only on Sulabh's machine.

---

## 3. IMMEDIATE NEXT STEPS (in order)

### 1. VERIFY THE GHOST FIX (live, Sulabh's machine, 2 questions)
The CITABLE IDS manifest landed but has **never run live**. Ask:

```
1. Do I have any raja yogas or special combinations in my chart?
2. What does Saturn's placement mean for my life?
```

Verify with `python -m pytest -q -m "not integration"` first, never a bare `pytest`.

Read off the capture: `ghost_citations` should be **[]** on both (was `['ch34_s013',
'ch48_s001']` and a 10-id list), `claims_returned` on the Saturn turn should rise well above
2, and `reasoning_effort_path` should still read `extra_body`.

### 2. THE ANSWER SHAPE — the biggest remaining gap, and now the highest-value work
The FACTS are no longer the constraint. Measured in `20260913T065603Z.md`: Sarala VRY (8th
lord in the 12th) and the Moon's Neecha Bhanga were both sitting in the fact block and went
unused, and D9 was never mentioned despite `Mercury: Virgo, D9 house 12, Exalted` being
present. The benchmark answer (`Output.txt` in the project) opens with a verdict, ranks
findings by reliability, names what it is ruling OUT and why, and flags its own unverified
step. Ours emits a flat list of whichever verses matched, and still leaks jargon the VOICE
block already bans ("angle-trine lords' union", "trinal interlinks").

Owners: `agent/astro/interpreter.py` (`_SYSTEM_HEAD`) and `agent/astro/answer_view.py`.
**CONSTRAINT:** `answer_view.render_user_answer` deliberately does NOT rewrite claim text —
rewriting is where a gate-verified claim silently becomes an unverified one. So ranking and
the verdict line must come from STRUCTURE the interpreter emits, not from post-hoc editing.
That probably means extending the claim schema (e.g. a confidence//ruled-out field), which
is an interpreter-prompt change and therefore a live-run trigger.

### 3. THEN, in rough priority order
- **The silence gate's negation guard is clause-blind.** `read_condition` returned `None`
  ("condition is negated or exclusionary") on a Saturn claim because "unless" appeared in a
  DIFFERENT clause. It failed safe, so a claim reciting "the 10th lord in the 8th" — false
  for this chart — shipped to the user. `ungated_pct` hit 100% on two turns.
- **The planner selects almost everything.** 14 of 16 domains, 81 units, 185k-229k prompt
  tokens against the ~80k the $0.19/question estimate assumed; `cached_tokens` 0 on six of
  seven turns, so the corpus-first cache is not hitting. Cost and latency both live here now.
- **`planetary_nature` is a glossary domain** (all five chapters are reference material) and
  the planner picks it ALONE for "what does X say about me" questions, producing "Venus is a
  female planet". A one-line planner gloss is drafted in
  `diagnostics/planet_reader_evidence_S130.md` §2 — NOT applied, because a planner prompt
  change affects every question and cannot be verified without live gpt-4o calls.
- **Advisory planet reader: HOLD.** 21 claims judged, 0 disagreements — a real zero, but
  gpt-5 writes every claim as "With <planet> in the <TRUE house>, …", so the reader validated
  a true prefix 21 times and never got the chance to refuse. Promotion grants DROP authority
  and no drop event has been observed. Use `scripts/classify_advisory_drops.py`.

---

## 4. DEFERRED / OWED (nothing lost, nothing started)

- **JHora asks: BOTH CLOSED S130.** `reference/oracle_fixtures/sulabh.md` **§3f** is a new
  matched-mode (Traditional Lahiri) clipboard capture carrying the Navamsa column, the
  upagrahas and the sphutas. D9 is **10/10 against production**, and byte-identical to §3b's
  True-Chitrapaksha Navamsa column — so D9 signs are stable across both ayanamsa modes for
  this chart. That CLOSES the accepted D9 precision gap: measured harmless, not just theorised.
  Dignity needed no oracle column — it derives from the oracle-confirmed Rasi column via the
  fixed S21 tables, 7/7 agreeing, recorded at §4 and clearly marked a DERIVATION.
- **AWAITING SULABH'S ADJUDICATION — `sulabh.md` §3e's Lagna.** §3e and §3f are the same
  capture in the same mode (all 9 grahas byte-identical) but their Lagna differs:
  §3e `Sg 22°40'59.06"` (residual **+38.62″**, the ONLY positive value in a table where every
  other row is −0.14″ to −47.91″) vs §3f `Sg 22°41'58.24"` (residual **−20.56″**, beside Sun's
  −20.63″). Almost certainly a hand-transcription slip in §3e — same class as the Saturn "(R)"
  slip already resolved in that file. **NOT auto-corrected**: §3e is the RATIFIED D1 oracle and
  `meta.asc_lon_sidereal` feeds `compute_navamsa`. Recorded as a CONFLICT block at §3f.
  Adjudicating it does NOT change the D9 result — production already matches JHora 10/10.
- **`vimshottari` / dasha** + the pratyantar hook. Blocked on the gate being able to
  range-verify a date.
- **Architect's refactor** — `pipeline._fact_block` still calls
  `payload_builder.parse_lord_house_map`; the adapter should own that.
- **MASTER BUILD PLAN** stale (~13 lines).
- **Cost-constraint re-ratification** — $0.01 ratified vs 185k-229k prompt tokens measured.
- **`main` is stale at S84** -> project RAG is ~45 sessions behind. Everything since lives on
  `wip/interpretive-pilot`.

---

## 5. TRAPS — THINGS SESSIONS KEEP GETTING WRONG

- **"I can't reach it from here" is NOT "it doesn't exist" (P-024).** Three times now:
  `chart_d1` (twice), `navamsa` (built S20, oracle-clean, unwired ~110 sessions), and
  `dignity` (always in `calculate_chart()`'s output, just never restated). BEFORE calling
  anything missing: `ls` the package, grep the CALLER not the module, and check what
  `calculate_chart()` already RETURNS. An unwired module is a WIRING task for the caller.
- **A citation inside a comment is a LEAD, not authority (P-025).** The dignity exclusion
  cited `docs/KNOWN_DIVERGENCES.md` for a claim that file does not contain. Open the cited
  file. If it does not say what it is cited for, label the decision UNRECORDED and take it
  to Sulabh.
- **`agent/calculations/core/chart_d1.py` is a PERMANENT, DELIBERATE stub. Never implement
  it (P-022).** The D1 chart is in production at `chart_calculator.py::calculate_chart()`.
- **A TypeError on a named kwarg means the SDK SIGNATURE is old, not that the API rejects the
  parameter (P-023).** Conflating them silently disabled `reasoning_effort` for every call.
- **Prove reachability before calling anything a defect.** S130 called
  `silence_gate.py:525-527` a genuine defect; a 2,800-case exhaustive differential harness
  showed the failure is unreachable by construction. Rule 28.
- **`ch34_s011` is NOT a mis-citation — it is 5/5 faithful.** Called wrong TWICE by reading a
  truncated slice of a 5,396-char segment. Read the whole segment.
- **Saturn "(R)" is RESOLVED — do not reopen.** Transcription slip in `sulabh.md`'s hand-typed
  3e table; census is 8/8.
- **Surbhi's birth data is 11 Sep 1992, 10:30, Patna.** It has been fabricated before.
- **Accepted D9 precision gap:** `meta.jd_ut` (6dp) and `meta.asc_lon_sidereal` (4dp) are
  rounded — ~0.2 arc-seconds against a 3°20' pada. Resolving it means exposing unrounded
  values from `chart_calculator`, i.e. the S20 lock. Recorded, not resolved; do not "fix" it
  by touching the calculator.
- **NEVER run the bare full suite to verify a change.** `pytest.ini` declares an
  `integration` marker for "real GPT calls" and sets NO `addopts`, so a plain
  `pytest` SPENDS API CREDIT. Use `python -m pytest -q -m "not integration"`.
  Every `tests/astro/` test is stub-driven and makes no network call.
- **VERIFY AFTER WRITING A FILE — the write receipt is not proof.** S130 pushed
  `interpreter.py` twice; the second push reported success and the OLD bytes were
  still on disk, so the CITABLE IDS manifest was missing while its four tests were
  present. Cost a full failed commit attempt. After writing, re-read the file and
  grep for a string only the new version contains. Corollary: when a comparison
  looks alarming, check you are comparing CURRENT bytes and not a stale snapshot —
  S130 also raised a false "systematic revert" alarm that way.
- **A file-delivery path is NOT reusable — this is what actually caused the two
  "lost" S130 writes.** Delivering a file to the repo twice through the SAME staging
  path serves the FIRST version the second time: the receipt says "written" and the
  old bytes land. Confirmed S130 — staged copy 12,856 bytes, device received 10,785.
  It hit `interpreter.py` (manifest missing while its tests were present, failing a
  whole commit attempt) and then hit the handover itself. **Use a fresh, uniquely
  named staging path for every delivery, and re-read the file afterwards.**
- **CRLF**: the Windows tree is CRLF. Convert anything written back, or the diff is
  whole-file.

---

## 6. WORKING PROTOCOL (Sulabh's, non-negotiable)

- Expert-to-expert. **No explanation unless asked** — usage limit is tight.
- **You do the coding.** You have full repo access. Write files into the repo and tell him the
  path; do NOT deliver source as chat file-cards. Hand over a Claude Code prompt only for what
  you genuinely cannot do yourself.
- **REVIEW before PROCEED** — flag at least one issue before approving any edit.
- **SAMPLE before SCALE. HARDEST CASE first. SURGICAL EDITS** — no full-file rewrites.
- **One prompt, one task.** Never proceed to the next step without confirmation.
- **Commits are Sulabh's**, from his tree. State the recommended model as the first line of
  every Claude Code prompt.
- Every claim about the codebase carries **branch + commit SHA**. If you can't name the SHA,
  you didn't read the code — say so.
- **"X does not exist" is never sayable alone** — only "X not found in \<paths\> on
  \<branch\>@\<sha\>". A contradiction from Sulabh is a **STOP** signal: re-verify the SOURCE,
  never re-run the same search harder.
