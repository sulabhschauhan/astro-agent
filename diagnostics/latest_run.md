# agent/interpretive/answer_renderer.py — deterministic DomainAnswer -> layman renderer (Session 65, 4c)

New Ring 1/2 files: `agent/interpretive/answer_renderer.py` (module) and
`tests/interpretive/test_answer_renderer.py` (13 tests). Zero LLM (S23
lock) — pure Python template-fill over `DomainAnswer`. Self-gate: new
tests green (13/13), full suite green with an exact +13 delta and zero
regressions. Committed per the ratification token provided at the top of
the task, as the LAST action after tests passed.

## Self-gate results

**New file in isolation:**
```
$ python -m pytest tests/interpretive/test_answer_renderer.py -v
...
13 passed, 1 warning in 1.73s
```

**Full suite:**
```
$ python -m pytest -q
...
3166 passed, 3 skipped, 1 warning in 137.14s (0:02:17)
```

**Delta**: prior baseline 3153 passed / 3 skipped + 13 new = **3166
passed / 3 skipped**. Exact match, zero regressions, skip count
unchanged. Self-gate GREEN — proceeded to commit.

## Every payload key verified against source before use (rule 1)

All 7 domains' `answer_payload` shapes were read directly from
`agent/infra/result_formatter.py`'s actual `_format_*()` branch code
(quoted/cited in each `_render_*()` helper's own docstring), not guessed:

| Domain (`answer.domain` value) | Source function | Key fields used |
|---|---|---|
| `current_dasha` | `_format_dasha()` | `mahadasha`/`antardasha` (`lord`/`start`/`end`), `near_boundary`, optional `timing_enrichment` |
| `sade_sati` | `_format_sade_sati()` | `active`, `phase`, `next_cycle_start`, conditionally `current_cycle_start`/`end` or `previous_cycle_end` |
| `career_strength` | `_format_career()` | `career_significators` (`tenth_lord`/`sun`/`saturn`, each `planet`/`ratio`/`rank`/`label`), `strongest_planet`, `weakest_planet`, `bhava_10_rupa` |
| `marriage_compatibility` | `_format_marriage()` | `total_score`, `max_score`, `koota_scores` (8 keys), `mangal_dosha` (`boy`/`girl`/`both_have`), `verdict` |
| `arudha_lagna` | `_format_arudha_lagna()` | `arudha_sign`, `lagna_sign`, `lord`, `co_lord_deciding_step` |
| `upapada_lagna` | `_format_upapada()` | `upapada_sign`, `lagna_sign`, `lord`, `co_lord_deciding_step` |
| `muhurta_window` | `_format_muhurta_window()` | `windows` (`start`/`end`/`tier`/`favorable_count`/`warnings`), `summary` (`tier1_window_count`/`earliest_tier1_start`) |

Two field semantics not already documented in `result_formatter.py`/
`chart_profile.py` were verified by reading the underlying calculation
module directly rather than guessed:
- `sade_sati`'s `phase` field: confirmed `Literal["RISING", "PEAK",
  "SETTING", "NONE"]` by reading `agent/calculations/transits/sade_sati.py`.
- `career_strength`'s rank ceiling ("rank N of **7**", not guessed at
  9 or some other number): confirmed by `_format_career()`'s own
  `weakest_planet = next(p for p, row in shadbala.items() if row["rank"]
  == 7)` — 7 classical grahas, no Rahu/Ketu in shadbala.
- `muhurta_window`'s `warnings` tuple contents ("Janma Tara", "Janma
  Rashi", "Panchaka") confirmed by reading `muhurta_scorer.py` directly —
  relevant because "Rashi" (with an "h") does NOT match
  `palm_reading._JARGON_BLACKLIST`'s `"rasi"` (without an "h"), a
  spelling distinction that matters for the jargon-compliance test.

## Design decisions surfaced (rules 2, 3, 4, 5)

- **REFUSAL (rule 2)** short-circuits `render_answer()` entirely —
  `answer_payload["user_message"]` returned verbatim, domain dispatch
  skipped (a REFUSAL's `domain` can be `None`, per
  `result_formatter.format_refusal()`), and **`demotion_reason` is
  deliberately NOT appended** for REFUSAL: `format_refusal()` already
  used `demotion_reason` to select which `user_message` to show, so
  appending it again would just restate the same refusal reason a
  second time, not add a genuine additional accuracy caveat. Verified
  by `test_refusal_returns_user_message_verbatim_no_demotion_append`.
- **`demotion_reason` (rule 3)** is appended as `"\n\nAccuracy note: " +
  demotion_reason`, verbatim, whenever truthy, for every non-REFUSAL
  domain. Verified by `test_demotion_reason_appended_as_accuracy_note_verbatim`.
- **`current_dasha`'s `boundary_note` field is deliberately NOT
  rendered** inside `_render_current_dasha()`, even though it's always
  present in the payload dict (possibly `None`) — reading
  `_format_dasha()`'s source shows `boundary_note` and `demotion_reason`
  are set together from the same `if near_boundary:` branch and carry
  the same ±37-day-drift message; rendering both would duplicate the
  identical caveat once via the domain body and once via the top-level
  "Accuracy note" append. This is safe (not an assumption) because the
  two fields are never decoupled by `_format_dasha()`'s own code —
  verified against the source before relying on it.
- **Muhurta tier relabeling (rule 4)**: `TIER_1`->"excellent",
  `TIER_2`->"good", `TIER_3`->"favorable for you specifically", fully
  replacing the raw jargon strings (not appending labels alongside them
  — verified by `test_muhurta_tier_relabeling_replaces_raw_jargon`
  asserting `"TIER_1"`/`"TIER_2"`/`"TIER_3"` are absent from the
  rendered text). **This appears to close the CLAUDE.md Session 64
  carry-forward** ("Per-window `MuhurtaTier` value strings are internal
  jargon") — flagged here per the task's explicit instruction, **NOT**
  acted on: CLAUDE.md is not in this task's file list (`agent/interpretive/
  answer_renderer.py` + `tests/interpretive/test_answer_renderer.py`
  only), so the carry-forward entry itself is untouched.
- **Jargon rule (rule 5)** interpreted as: a blacklisted term may appear
  as a domain topic name (rule 5's own examples: "Sade Sati", "Arudha
  Lagna") provided it is glossed — either at that exact occurrence or
  earlier in the same rendered text (natural language legitimately
  refers back to an already-explained term without re-explaining every
  single time; see `_render_current_dasha()`'s second, backward-
  referencing use of "Mahadasha" inside its Antardasha sentence). No
  runtime jargon-check exists inside `answer_renderer.py` itself (see
  the module's own docstring for why: this output is fully self-
  authored/deterministic, unlike `palm_reading.py`'s LLM-output
  validation, so there's nothing untrusted to check at runtime — the
  compliance burden lives in the test suite instead).

## Full test list (13 tests)

1. `test_refusal_returns_user_message_verbatim_no_demotion_append`
2. `test_unknown_domain_raises_value_error`
3. `test_missing_payload_key_raises_keyerror_fail_loud` (extra rigor
   beyond the task's explicit list, directly proving rule 6's "fail-
   loud" contract)
4. `test_demotion_reason_appended_as_accuracy_note_verbatim`
5–11. Seven per-domain happy-path tests (one per
   `current_dasha`/`sade_sati`/`career_strength`/
   `marriage_compatibility`/`arudha_lagna`/`upapada_lagna`/
   `muhurta_window`)
12. `test_muhurta_tier_relabeling_replaces_raw_jargon`
13. `test_no_unglossed_jargon_across_all_domain_outputs` (loops over all
    7 happy-path outputs, reuses `palm_reading._JARGON_BLACKLIST`
    directly rather than duplicating it — single source of truth)

## Commit

Committed after this report was written and the self-gate confirmed
GREEN, per the task's explicit "commit is the LAST action" instruction
and the ratification token provided at the top of the prompt.
