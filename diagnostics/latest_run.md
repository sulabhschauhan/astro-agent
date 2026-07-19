# S68 F-B: _ABSENCE_PHRASES regex broadening -- implementation report

## Source-path correction (verify-before-transcribe)

The instructing prompt named `.claude/read_prompt.md` as the location of
the 2026-07-18 F5-captured RUN blocks. That file's content has since been
overwritten by an unrelated later commit (`2bb2e44 Update
.claude/read_prompt.md content` -- it now holds a Sade Sati/marriage
question, nothing palm-related). The real capture log is
`diagnostics/dogfood_capture.md` (`frontend/app.py`'s `_capture_dogfood_
run()` writes there, confirmed by reading the source, not assumed). It
contains **3** 2026-07-18 RUN blocks, not 4 (`11:34:32`, `11:35:40`,
`11:38:22` -- matching SESSION_LOG's own Session 68 Run A/B/C labels).
Used those 3 for this measure-first pass; noted here rather than blocking
on the discrepancy, since the 3 blocks are the complete, real,
already-ratified (Ring 3 pass 3) capture set.

## What changed

Two-tier fix in `agent/interpretive/palm_reading.py`'s `_is_absence()`:
- **TIER 1** (`_ABSENCE_PHRASES`): the OLD 6-phrase fixed-substring list,
  unchanged in content, recompiled as case-insensitive regex (`re.escape`
  per phrase -- byte-identical matching behavior to the old `in` check).
- **TIER 2** (`_ABSENCE_PATTERNS_BY_FEATURE`, new): per-feature,
  noun-anchored `no <0-3 filler words> <feature noun> <0-6 filler words>
  visible` patterns, reusing `_SUPPORT_NEEDLES` as the noun source (one
  extra inflection, "marking", added only for the markings feature).
  `_is_absence()` gained an optional `feature` parameter; both call sites
  (`_resolve_feature_quality`, `_is_genuine_negative_absence`) now pass
  it. `scripts/probe_fc_retrieval.py`'s existing single-argument call
  (`_is_absence(t)`) keeps working unmodified -- `feature=None` is the
  pre-F-B behavior (TIER 1 only).

## Sanity check against the design's own false-positive warning

Before running classification over the captured runs, verified the
literal danger case the design called out -- direct interpreter probe,
not a guess:

```
_is_absence('no breaks, chains, forks, or islands visible.', 'life line') -> False
_is_absence('no breaks, chains, forks, or islands visible.', 'head line') -> False
_is_absence('no breaks, chains, forks, or islands visible.', 'heart line') -> False
```

This is the REAL LEFT-hand LIFE/HEAD/HEART LINE text from all 3 captured
runs, containing "islands" -- a literal `markings/other features` needle
-- yet it correctly stays unmatched for all three line features, because
each feature's noun pattern requires ITS OWN noun ("life"/"head"/"heart"),
none of which appear in that clause. Confirms per-feature noun anchoring
(not a generic "no...visible" match) is doing real protective work here,
not just in theory.

## MEASURE-FIRST: OLD vs NEW classification, all 3 RUN blocks

LEFT and RIGHT hand text is byte-identical across all 3 runs (regenerate/
add-HAND_DETAIL only); HAND_DETAIL exists only in the 3rd run
(`11:38:22`). One consolidated table therefore covers all 3 runs, with
HAND_DETAIL fields marked as run-3-only.

| Source | Field text | Feature | OLD | NEW | Delta |
|---|---|---|---|---|---|
| LEFT | "no breaks, chains, forks, or islands visible" | life line | not-absence | not-absence | none |
| LEFT | "no breaks, chains, forks, or islands visible" | head line | not-absence | not-absence | none |
| LEFT | "no breaks, chains, forks, or islands visible" | heart line | not-absence | not-absence | none |
| LEFT | "Barely visible." | fate line | not-absence | not-absence | none |
| LEFT | "Mount of Venus appears developed" (clause) | mount of venus | not-absence | not-absence | none |
| LEFT | **"No marks clearly visible."** | markings/other features | not-absence | **absence** | **FLIP** |
| RIGHT | "no clear breaks or forks" (no "visible") | life line | not-absence | not-absence | none |
| RIGHT | "Sun line is not clearly visible" (clause) | sun line | absence (TIER1) | absence (TIER1) | none |
| RIGHT | "Mount of Venus appears developed" (clause) | mount of venus | not-absence | not-absence | none |
| RIGHT | "No clear marks such as crosses, stars, grilles, squares, or moles visible." | markings/other features | absence (TIER1) | absence (TIER1) | none |
| HAND_DETAIL (run 3 only) | "A prominent line curves around the base of the thumb." | life line | not-absence | not-absence | none |
| HAND_DETAIL (run 3 only) | "This line runs horizontally..." | head line | not-absence | not-absence | none |
| HAND_DETAIL (run 3 only) | "The heart line is visible, curving..." | heart line | not-absence | not-absence | none |
| HAND_DETAIL (run 3 only) | "There is no clearly visible fate line in the image." | fate line | not-absence | not-absence | **none (see below)** |
| HAND_DETAIL (run 3 only) | "...appear slightly raised" (venus/jupiter clause) | mount of venus / mount of jupiter | not-absence | not-absence | none |
| HAND_DETAIL (run 3 only) | **"There are no unusual markings or features visible on the hand."** | markings/other features | not-absence | **absence** | **FLIP** |

**Every delta is exactly the expected one**: the 2 MARKS/markings-class
fields (LEFT's field-label text, HAND_DETAIL's bullet text) flip from
"not-absence" to "absence" -- both previously-missed word-order variants
of the pass-3 finding. Every LINE-quality field (all 3 lines' "no
breaks/chains/forks/islands" text, both hands' fate line, life line's
"no clear breaks or forks") is unchanged. **No unexpected delta occurred
-- nothing to STOP on.**

### One observed-but-out-of-scope non-catch (documented, not a bug)

HAND_DETAIL's fate line text, "There is no clearly visible fate line in
the image.", stays `not-absence` under BOTH old and new code -- not a
regression (it was already a miss), and not fixed by this pass. Reason:
its word order is `no <qualifier> visible <noun>` (noun AFTER "visible"),
the reverse of the design's specified `no <qualifier> <noun> <anything>
visible` target shape. This is a real but DIFFERENT word-order gap than
the one F-B was scoped to fix (the pass-3 finding was specifically about
`no <qualifier> <noun>` vs `no <noun> <qualifier>` ordering, both noun-
before-visible). Not escalated here: this exact field is harmless in
practice (fate line's OTHER 2 sources -- LEFT "Barely visible.", RIGHT's
real quality text -- already carry it to a genuine, correctly-supported
retrieval in the actual captured Run 3 output, `unsupported_features:
()`), so nothing downstream is currently affected by leaving this
narrower gap open.

## The knock-on (pass-3-vs-pass-4 comparability evidence)

For all 3 captured runs, `markings/other features`'s raw-text set is now
ALL absence-phrased (LEFT + RIGHT always; + HAND_DETAIL in run 3), so
`_is_genuine_negative_absence` now returns `True` where it previously
returned `False`. Concretely, per run:
- The feature is REMOVED from both `supported_features` and
  `unsupported_features` entirely (the genuine-negative-absence
  pathway -- nothing to support, nothing to decline).
- Zero `search()` calls fire for it (previously 1, since a query was
  built from the un-recognized "absence" text).
- Its previously-borderline sources disappear from `sources` -- these
  were real production near-floor hits (0.3654/0.3639/0.3484 in run 1/2,
  0.4115/0.4078 in run 3, all barely above the 0.30 `_SUPPORT_SCORE_
  FLOOR`) that were junk retrieval symptomatic of exactly this bug, not
  genuine markings doctrine.
- The decline block no longer names it (it was never named there before
  either, since it was `supported`, not `unsupported` -- this is a
  change in WHY it's absent from the decline block, not a visible text
  change).
- `_check_feature_coverage`'s denominator shrinks by 1 for these 3 runs
  (one fewer `supported` feature that coverage has to check) -- any
  future pass-4 scoring against these same captures will see a smaller
  supported-feature set than pass-3's `ring3_palm_rubric_S67_pass3.md`
  scored against. This is the fix working as intended, not a
  regression: pass-3's own Findings #1 flagged this exact field as
  "routing a genuinely-absent field through the fail-open real-query
  path instead of genuine-negative-absence... a latent risk" -- that
  risk is now closed for this field, and any pass-4 comparison to
  pass-3's markings-related findings should account for the feature no
  longer appearing in `supported_features` at all.

## Tests

Zero test-file edits needed. Full suite run FIRST, unprompted (not
assumed clean): **3220 passed, 3 skipped** -- exact match to the F-A
baseline, 0 regressions, 0 new failures. Grepped
`tests/interpretive/test_palm_reading.py` for existing MARKS fixtures:
all 3 hits already read `"MARKS: No clear marks visible."` -- already a
TIER-1 match under the OLD code (that exact word order was never the bug
pass-3 found), so no existing test exercised the word-order gap this
prompt fixes. This explains the clean run: the fix closes a gap real
production dogfood data hit but the existing synthetic test suite never
happened to construct.

Per the instructing prompt's two-commit-one-push discipline: since
nothing broke, this is a SINGLE commit, no commit B needed.

## Full pytest result

`python -m pytest -q`: **3220 passed, 3 skipped** -- baseline was 3220/3
(post F-A), 0 regressions, 0 new tests this pass (a pure classification-
logic broadening with no user-visible surface change to test against
beyond what the suite already covers).
