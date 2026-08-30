# S118 — banned-mention censor: jurisdiction principle applied GENERALLY

DECISION SERVED: apply the ratified "a rule-fired feature is outside the
retrieval support-gate's authority" principle (3a3d625 applied it to the gate
TUPLES) to the banned-mention censor. Claim-driven, not needle-driven. No Mars
special-casing, no needle-table edit, no retrieval change.

STATUS: implemented, verified, **COMMITTED AND PUSHED** as `27a9edd` on
`wip/interpretive-pilot` (ratification token received in a follow-up prompt --
see section 7). Sections 1-6 below were written before that token arrived and
are preserved as the pre-commit record.

---

## 1. Confirmed mechanism (verified at HEAD 3a3d625, `wip/interpretive-pilot`)

**1a. Censor shape — confirmed exactly as described.**
`_check_banned_feature_mentions` (`agent/interpretive/palm_reading.py`, was
line 1266) looped over `unsupported_features`, compiled a word-boundary
alternation of that feature's `_SUPPORT_NEEDLES`, and flagged the feature on
the first `pattern.search(low)` hit. The check knew only "SOME needle of this
unsupported feature matched"; it could not ask *which* word matched or whether
anything else legitimately owned that word.

**1b. Root cause of the C6 failure — confirmed, and it is NOT a gate-tuple
regression.** 3a3d625 works exactly as designed: from
`diagnostics/s117_live_confirmation_raw.json`, `"mount of mars positive"` (the
M_023 claim, C6) is in **neither** gate tuple. The failure is entirely
downstream of that: `"mount of mars negative"` never fired a rule and never
retrieved a supporting chunk, so it is honestly in `unsupported_features` — and
`_SUPPORT_NEEDLES` gives **both** Mars mounts the single shared needle `"mars"`
(a documented, accepted imprecision: Cheiro p113 has no single-word
discriminator). C6's sentence, *"The Upper Mount of Mars gives you active
courage and a martial spirit."*, therefore word-boundary-matched `"mars"` on
behalf of the unclaimed sibling. Live result: the whole otherwise-clean reading
failed with `unsupported feature mentioned: mount of mars negative` **twice** —
once at the Stage-2 extra-validator seam, once at the fail-closed backstop.

**1c. Scope of the threading — established, and the set already existed.**
`features_with_surviving_rule_claims` is computed once in
`_prepare_deterministic_prep` (the same expression that narrows both gate
tuples). It was **not** in scope at either censor call site. Both real call
sites live inside `complete_palm_reading`, which holds the `prep`:

| call site | line (HEAD) | reached via |
|---|---|---|
| `_build_display_extra_validators` → `_banned` closure | 2654 | Stage-2 retry seam |
| `_run_display_checks` | 1610 | fail-closed backstop |
| `_run_ring1_checks` | 1583 | retired single-call path (dead code, left alone) |

Minimal clean threading (what was implemented): carry the already-computed set
on `PalmReadingPrep` as a new defaulted field, and derive the allowed-needle
set **once** in `complete_palm_reading`, feeding it to both live call sites. No
recomputation anywhere; the retired third call site keeps the empty default and
is byte-identical.

---

## 2. The general predicate

Let `allowed_needles` = union of `_SUPPORT_NEEDLES[f]` over every feature `f`
with a surviving rule claim. For each unsupported feature, collect the set of
needles that **actually matched** the text (`pattern.finditer`, not
`pattern.search`):

> flag `feature` iff `matched` is non-empty **and** `matched ⊄ allowed_needles`
> — i.e. at least one word it was named by is accounted for by **no** claimed
> feature.

Nothing in the predicate names a feature, a mount, or Mars. It reads
`_SUPPORT_NEEDLES` only to *derive* the allowed set, so a future needle edit or
a new shared-needle pair is covered by construction.

### 2a. Proof it ALLOWS a claimed feature

| case | claimed | unsupported | text | matched | allowed | result |
|---|---|---|---|---|---|---|
| C6 / Upper Mars | `mount of mars positive` (+5) | `mount of mars negative` | *"The Upper Mount of Mars gives you active courage…"* | `{mars}` | `{mars, head, life, venus, jupiter, saturn}` | **allowed** |
| apollo→sun overlap | `mount of apollo` | `sun line` | *"The Mount of the Sun is generously formed…"* | `{sun}` | `{apollo, sun}` | **allowed** |
| sun-line→apollo (non-mount claim) | `sun line` | `mount of apollo` | *"Your sun line runs clear and unbroken."* | `{sun}` | `{sun}` | **allowed** |

### 2b. Proof it still GUARDS the genuinely unsupported

| case | claimed | unsupported | text | matched | allowed | result |
|---|---|---|---|---|---|---|
| unshared needle | `head line` | `sun line` | *"Your sun line runs clear…"* | `{sun}` | `{head}` | **FLAGGED** |
| own-word naming | `sun line` | `mount of apollo` | *"The Mount of Apollo is generously formed."* | `{apollo}` | `{sun}` | **FLAGGED** |
| no claims at all | — | `mount of mars negative` | *"The Upper Mount of Mars gives you active courage."* | `{mars}` | `∅` | **FLAGGED** (identical to pre-S118) |
| word boundary intact | — | `sun line`, `markings` | *"A sunny disposition and a remarkable steadiness."* | `∅` | `∅` | not flagged (unchanged) |

Registry-wide sanity sweep: the same probe sentence naming every registry
feature yields **15 flags with no claims** and **0 flags with every feature
claimed** — the guard is fully live at one extreme and fully deferential at the
other, with nothing hardcoded in between.

### 2c. REJECTED alternative (evaluated, and it is NOT equivalent)

The prompt offered a "cleaner equivalent" framing: skip a feature entirely when
`needles(feature) ⊆ allowed_needles`. **It is strictly coarser and over-flags.**
Row 3 of table 2a is the counterexample: with `sun line` claimed
(`allowed = {sun}`) and `mount of apollo` unsupported,
`needles(apollo) = {apollo, sun} ⊄ {sun}`, so the subset form would still fail a
sentence about the claimed sun line — even though its only matched word,
`"sun"`, is fully attributable to the claim. Per-matched-needle attribution is
what actually states the ratified principle; the subset form only approximates
it. This is recorded in the shipped docstring and pinned by a dedicated test
(`…_when_a_non_mount_line_holds_the_claim`).

---

## 3. Exact before / after

`agent/interpretive/palm_reading.py` — **+107 / −7 lines** (docstrings included;
the behavioural change is 2 lines).

**BEFORE**
```python
def _check_banned_feature_mentions(
    text: str, unsupported_features: tuple[str, ...]
) -> list[str]:
    ...
        if pattern.search(low):
            failures.append(f"unsupported feature mentioned: {feature}")
```

**AFTER**
```python
def _allowed_needles_for_claimed_features(rule_claim_features) -> frozenset[str]:
    return frozenset(
        needle
        for feature in rule_claim_features
        for needle in _SUPPORT_NEEDLES.get(feature, ())
    )


def _check_banned_feature_mentions(
    text: str,
    unsupported_features: tuple[str, ...],
    allowed_needles: frozenset[str] = frozenset(),
) -> list[str]:
    ...
        matched = {m.group(1).lower() for m in pattern.finditer(low)}
        if matched and not matched <= allowed_needles:
            failures.append(f"unsupported feature mentioned: {feature}")
```

Threading (compute once, pass down):

| site | change |
|---|---|
| `PalmReadingPrep` | new field `rule_claim_features: frozenset[str] = frozenset()` |
| `_prepare_deterministic_prep` | `rule_claim_features=frozenset(features_with_surviving_rule_claims)` — the SAME set the two tuple narrowings use, not recomputed |
| `complete_palm_reading` | `allowed_needles = _allowed_needles_for_claimed_features(prep.rule_claim_features)`, computed once, fed to both call sites |
| `_build_display_extra_validators` | new 3rd param, defaulted; passed into the `_banned` closure |
| `_run_display_checks` | new 4th param, defaulted; passed into the censor call |
| `_run_ring1_checks` (retired path) | **untouched** — takes the empty default |

NOT touched, per scope: `_apply_support_gate`, `_SUPPORT_NEEDLES`, the decline
block / gate tuples (3a3d625 owns those), `claim_voicing`'s transplanted copy
(separate logged debt), retrieval.

**Behavioural blast radius, stated precisely:** because 3a3d625 already removes
a claimed feature from `unsupported_features`, the censor could never flag a
claimed feature for naming *itself*. The only outcomes this change can flip are
therefore ones where a genuinely unsupported feature **shares or overlaps** the
matched needle with a claimed one. Today `_SUPPORT_NEEDLES` contains exactly two
such collisions — `{mars positive, mars negative}` on `"mars"` and
`{mount of apollo, sun line}` on `"sun"` — and both are tested in both
directions. Every other reading, and the entire LLM Stage-1 path, is
byte-identical.

---

## 4. Test results — 13 new tests, all passing

Added to `tests/interpretive/test_palm_reading_rules_engine.py` (+263 lines),
alongside 3a3d625's own jurisdiction tests.

| # | requirement | test(s) | result |
|---|---|---|---|
| 1 | **GENERALITY / NON-MARS** | `test_censor_allows_overlapping_needle_when_apollo_holds_the_claim` · `test_censor_allows_overlapping_needle_when_a_non_mount_line_holds_the_claim` | **PASS** |
| 2 | **THE MARS LIVE FAILURE** (deterministic) | `test_upper_mars_claim_survives_the_censor_end_to_end` | **PASS** |
| 3 | **GUARD INTACT** | `test_censor_still_fails_the_unsupported_feature_named_by_its_own_word` · `test_censor_still_fails_a_genuinely_unsupported_unclaimed_feature` · `test_censor_still_fails_end_to_end_when_the_text_names_an_unclaimed_feature` | **PASS** |
| 4 | **DECLINE UNCHANGED** | `test_unclaimed_mars_sibling_is_still_declined_not_promoted` | **PASS** |
| 5 | **NO CLAIMS AT ALL** | `test_censor_with_no_claims_at_all_is_unchanged` (3 params) · `test_llm_stage_one_prep_grants_no_censor_exemption` | **PASS** |

**On (1), the non-Mars generality proof.** The primary proof is the
`sun line` ↔ `mount of apollo` overlap, run in **both** directions. The stronger
direction is the one where the claim is held by the **sun line — a line, not a
mount** — with the unsupported `mount of apollo` carrying a strict *superset* of
its needles. That case is the anti-mount-patch proof and simultaneously the case
that fails under the rejected subset framing, so it pins the predicate's shape,
not just its outcome. (A rule-fired sun line cannot be built end-to-end today —
no sun-line rules exist in any of the 4 live rule files — so this pair is
exercised at the censor's own boundary, where the allowed set is still *derived*
from the claimed-feature set by the real production helper.)

**On (2), why it is deterministic.** The end-to-end test drives the real
pipeline with a fake client: `MOUNTS: DEVELOPMENT (Upper Mount of Mars):
present` → M_023 fires → one claim on `mount of mars positive`, retrieval
stubbed to unrelated life-line text so `mount of mars negative` is honestly
unsupported. It asserts the verbatim live C6 sentence reaches `reading_text`,
`validation.failures == ()`, and **exactly 2 LLM calls** — 2 means the
extra-validator seam saw no failure and Stage 2 never needed its retry.
Its pre-fix counterpart is not hypothetical: the first parametrised row of test
(5) asserts that this *same sentence* + *same unsupported feature* + empty
allowed set still yields the old failure string.

**On (4).** The same run shape asserts `mount of mars negative` remains in
`unsupported_features`, is absent from `supported_features`, is selected into
`_compute_decline_features`, and is named in the delivered `reading_text`'s
decline block. Nothing was silently promoted.

**On (5).** Asserted twice per case — through the derived-empty set and through
the **default argument**, i.e. every pre-existing caller including the retired
`_run_ring1_checks` path. Plus a dataclass-level pin that the LLM Stage-1 prep
grants no exemption (its claims are retrieval-sourced, hence squarely inside the
gate's jurisdiction).

**One test-fixture correction made en route, flagged not silent:** the guard
test originally used *"the markings on the palm are many"* and expected
`markings/other features` to flag. It does not — `"markings"` does not
word-boundary-match the `"mark"` needle. That is **pre-existing, deliberate**
behaviour (the S67 R2 rider: word-boundary matching so `"remarkable"` never
fires `"mark"`), unrelated to S118 and unchanged by it. The test was corrected
to use `"a star"`, a needle that genuinely matches. It is the same singular-noun
needle limitation already registered in CLAUDE.md's Carry-Forward
("needle-inventory audit", S70 F-E); no needle was edited here.

---

## 5. Verification

| check | result |
|---|---|
| **Deterministic C6 recheck** (replayed the LIVE capture — real `reading_text_tagged`, real `unsupported_features`, real claim set from `diagnostics/s117_live_confirmation_raw.json`; **no live call needed or made**) | BEFORE (empty allowed): `['unsupported feature mentioned: mount of mars negative']` → **AFTER (S118): `[]`** |
| `python scripts/gate_rule_citations.py` | 4 rule files, 99 live + 16 parked rules, **NOT_FOUND_ANYWHERE: 0** |
| **`pytest -q` FULL SUITE** | **3687 passed, 0 failed, 7 skipped** (79s) |
| All four lines' rule/reading tests, re-run explicitly (`test_palm_reading` · `_rules_engine` · `test_palm_rules_table` · `test_rule_to_claim` · `test_claim_voicing` · `test_claim_extraction` · `test_vocab_reachability_scan` · `test_gate_rule_citations`) | **270 passed, 0 failed, 4 skipped** |
| Zero behaviour change where no rule fires | proven three ways: the default-argument assertions in test (5), the LLM-path dataclass default, and the registry-wide sweep (15 flags with no claims — unchanged) |

Live claim/allowed sets recovered from the capture for the C6 recheck:
`claimed = {head line, life line, mount of jupiter, mount of mars positive,
mount of saturn, mount of venus}` → `allowed = {head, life, jupiter, mars,
saturn, venus}`; `unsupported = (sun line, mount of mercury, mount of mars
negative, mount of luna)`. The live capture shows the failure string twice
because the seam and the backstop each produced it; a single censor call
reproduces one, and S118 clears both since they now share one allowed set by
construction.

---

## 6. Files changed (working tree only — NOT committed)

- `agent/interpretive/palm_reading.py` — +107 / −7
- `tests/interpretive/test_palm_reading_rules_engine.py` — +263 / −0

## 7. COMMITTED AND PUSHED (RATIFIED)

Ratification token received; committed as ONE unit on `wip/interpretive-pilot`.

| item | value |
|---|---|
| **Commit SHA** | `27a9edd` |
| Subject | `fix(palm): banned-mention censor honors surviving rule claims — jurisdiction applied generally (S118)` |
| Parent | `3a3d625` (the gate-tuple jurisdiction fix this generalizes) |
| Files | `agent/interpretive/palm_reading.py` (+107/-7) · `tests/interpretive/test_palm_reading_rules_engine.py` (+263/-0) — **2 files, 363 insertions, 7 deletions** |
| **Push** | `3a3d625..27a9edd  wip/interpretive-pilot -> wip/interpretive-pilot` — **succeeded**, fast-forward |
| Post-push check | `git log origin/wip/interpretive-pilot..HEAD` returns empty (nothing unpushed); `origin/wip/interpretive-pilot` is at `27a9edd` |

Pre-commit gates, both re-run immediately before staging:
- `pytest -q` -> **3687 passed, 7 skipped, 0 failed** (79s)
- `python scripts/gate_rule_citations.py` -> **NOT_FOUND_ANYWHERE: 0** (4 rule files, 99 live + 16 parked)

Staging hygiene: `diagnostics/latest_run.md` was left **unstaged** and is NOT
in this commit, per instruction. No other tracked file was modified; the many
untracked `diagnostics/*`, `scripts/*`, `probes/` and `tests/interpretive/
test_capture_net_digest.py` entries are pre-existing session artifacts and were
not staged.

Known debt carried in the commit message, unchanged and still open:
`claim_voicing._FEATURE_TRAIT_NEEDLES` is a drifted verbatim copy of
`_SUPPORT_NEEDLES` (10 vs 16 features), and the dual use of `_SUPPORT_NEEDLES`
for both corpus retrieval and output censoring is the deeper structural cause —
Direction B, deferred to its own session.


---

## 8. Branch close-out — digest tool committed, branch clean

Second ratified artifact landed; `wip/interpretive-pilot` is now fully pushed.

### 8a. Both commits

| # | SHA | subject | files |
|---|---|---|---|
| 1 | `27a9edd` | `fix(palm): banned-mention censor honors surviving rule claims — jurisdiction applied generally (S118)` | `palm_reading.py` (+107/-7) · `test_palm_reading_rules_engine.py` (+263/-0) |
| 2 | `dee8007` | `feat(diagnostics): capture-net monthly digest summarizer (read-only)` | `agent/interpretive/capture_net_digest.py` (new, 170) · `tests/interpretive/test_capture_net_digest.py` (new, 168) — 338 insertions |

Push: `27a9edd..dee8007  wip/interpretive-pilot -> wip/interpretive-pilot`.
`git log origin/wip/interpretive-pilot..HEAD` -> **empty**; remote branch head
is `dee8007`. Parent chain: `3a3d625` (S117) -> `27a9edd` (S118) -> `dee8007`.

### 8b. Gates before the digest commit

- `pytest -q` -> **3687 passed, 7 skipped, 0 failed** (78s). Count is unchanged
  from the S118 run because the digest tests were **already on disk and already
  being collected** — pytest collects from the filesystem, not from the git
  index, so committing them adds no new tests to the suite. Verified directly:
  `pytest tests/interpretive/test_capture_net_digest.py` -> **7 passed**.
- `python scripts/gate_rule_citations.py` -> **NOT_FOUND_ANYWHERE: 0**.

### 8c. Commit-message claims verified against source (not taken on trust)

| claim | evidence |
|---|---|
| "read-only … Never writes the log" | only `path.read_text()`; no `open()` for write, no `.write` anywhere in the module |
| "groups by trigger x feature x disposition" | `build_digest` returns `counts_by_trigger`, `counts_by_trigger_x_feature`, `counts_by_disposition` |
| "surfaces the ai_decision lane" | `ai_decision_rows` collected where `trigger == "ai_decision"` |
| "CLI + build_digest/render_markdown API" | both public functions present; `argparse` CLI under `__main__` |
| "Companion to the capture-net wiring (committed earlier)" | `agent/interpretive/capture_net.py` is tracked, committed in `3866997` (S116) |
| trigger vocabulary not duplicated | `_KNOWN_TRIGGERS` derived from `capture_net._DISPOSITION_TO_TRIGGER` |

### 8d. Final cleanliness — every remaining file accounted for

**Tracked, modified: 1**

| file | disposition |
|---|---|
| `diagnostics/latest_run.md` | **keep — this report**; committed as the docs commit carrying this section (docs/diagnostics commits are exempt from the ratification-token rule, Working Style #14) |

**Untracked: 47 — all keep-untracked session artifacts, none needs-attention**

| group | count | disposition |
|---|---|---|
| `diagnostics/*` (9 `.json` raw captures, 10 `.py` one-off validators, 6 `.txt` before/after dumps, 2 `.md`, 1 `.csv` template) | 28 | keep-untracked (session artifact) |
| `scripts/*_probe.py` / sweep / gate one-offs | 18 | keep-untracked (session artifact) |
| `probes/` | 1 (dir) | keep-untracked (session artifact) |

Zero untracked files fall outside `diagnostics/`, `probes/`, `scripts/`
(verified by inverse filter — the "would need attention" list came back empty).

**Working Style #16 audit check, run rather than assumed:** the rule requires
any probe script whose numbers are cited in a decision to be committed
alongside its report. Every untracked `scripts/*` basename was grepped against
the committed `CLAUDE.md`, `SESSION_LOG.md`, and `diagnostics/` — **zero
citations found**. None of these probes backs a recorded decision, so leaving
them untracked creates no audit gap. (`diagnostics/gate_rule_citations_report.md`
is regenerated on every gate run and is intentionally not tracked.)

### 8e. Note on scope

The instructing prompt said "Two small commits" but specified only one
(step 4, the digest). I read the second as this report — CLAUDE.md's own
diagnostics convention has `latest_run.md` committed to git, and docs commits
need no ratification token. Only the digest commit touched source. If the
intended second commit was something else, say so and I will land it.
