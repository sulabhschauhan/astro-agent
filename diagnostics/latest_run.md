# Session 56: enrichment render tests -- timing_enrichment coverage

One file changed: `tests/infra/test_result_formatter_av_transit.py`. No
production file touched (`git status --short` confirms only the test
file + the benign `diagnostics/calc_router_stage2.log` growth from
running the suite).

## Career minimal-payload finding (read `_format_career()` before writing)

Read `result_formatter.py`'s `_format_career()` directly rather than
guessing. Minimal required `career_strength` payload shape:

- `"shadbala"`: dict keyed by planet name. Each row needs
  `"shadbala_rupa"`/`"ratio"`/`"rank"` (read by `_significator_block()`).
  `"sun"` and `"saturn"` keys are read UNCONDITIONALLY
  (`shadbala["sun"]`, `shadbala["saturn"]`), independent of `tenth_lord`.
  At least one row needs `rank == 1` (`strongest_planet`'s `next()`) and
  one needs `rank == 7` (`weakest_planet`'s `next()`) -- an unmatched
  `next()` over an empty generator raises `StopIteration`, not a soft
  default, so these can't be omitted.
- `"bhava_bala"`: dict keyed by house number; only house 10 is read
  (`bhava_bala[10]["total_rupa"]`).
- `"tenth_lord"`: must be a valid key into `"shadbala"`.

Built the minimal fixture as 2 planets, not 3: `"sun"` (`rank=1`,
doubling as both `tenth_lord` and `strongest_planet`) and `"saturn"`
(`rank=7`, `weakest_planet`) -- satisfies every direct-index/`next()`
requirement above with the smallest possible dict. Added as
`_CAREER_SHADBALA`/`_CAREER_BHAVA_BALA`/`_career_payload(**extra)` in the
test file.

## Changes made

1. **Module docstring**: appended a Session 56 section (tests 9-13,
   hardest first) after the existing 8-test list -- the existing 8
   descriptions themselves untouched (surgical addition, not a rewrite).
2. **`_domain_profile(domain, payload)`** (new helper): `_profile()` is
   left untouched (hardcodes `domain="av_transit"`, used by all 8
   original tests) rather than widened -- a new domain-generic builder
   for the career_strength/current_dasha tests instead.
3. **`_CAREER_SHADBALA`/`_CAREER_BHAVA_BALA`/`_career_payload()`** (new):
   the minimal career fixture derived above.
4. **5 new tests**, hardest case first, exactly as specified:
   - `test_enrichment_resolution_note_never_leaks_into_av_transit_domain`
     -- adversarial: av_transit's own `answer_payload` has exactly 3
     keys; `"resolution_note"` absent at the top level, inside
     `dasha_envelope`, AND inside every `sub_windows` entry (nested
     check, not just a top-level one).
   - `test_career_enrichment_absent_key_byte_identical` -- no
     `timing_enrichment` in payload -> `answer_payload` key set is
     exactly the pre-Session-56 4 keys, `sources ==
     ("shadbala", "bhava_bala")`.
   - `test_dasha_enrichment_present_renders_block_and_extends_sources` --
     valid block renders (`"D Mon YYYY"` dates via the J2000 anchor,
     `resolution_note` naming both axes), `sources` extends to the
     4-tuple. `near_boundary` forced `True` so `demotion_reason` is a
     real, non-`None` string here -- strengthens the "no enrichment
     language" check into something non-trivial (a `None` check would
     have passed vacuously with the default `near_boundary=False`).
   - `test_enrichment_empty_sub_windows_block_dropped_silently` --
     `sub_windows=[]` inside the enrichment block -> no exception, key
     omitted, `sources` stays at the base tuple. Docstring explicitly
     contrasts this with test 1's (`test_empty_sub_windows_raises_
     never_collapse_value_error`) domain-level fail-closed `ValueError`
     -- same S54 guard's spirit (no ranked sub-windows isn't
     renderable), inverted letter (degrade, not raise), per the Session
     56 locked decision.
   - `test_career_enrichment_present_renders_block` -- mirrors the
     dasha present-block test for career_strength independently,
     confirming both domains' append paths work on their own (each
     starts from its own base `sources` tuple).
5. **+1 assertion** on the existing
   `test_tier_always_tier_2_range_and_demotion_reason_fixed`:
   `assert answer.uncertainty_days == 37.0` -- closes the passthrough
   gap flagged in design chat at this file's original creation. No other
   line in that test touched.

## Suite

**2948 passed, 3 skipped, 0 failed** -- matches the expected 2943 + 5
exactly (the +1 assertion adds no count, as predicted). Isolated run of
the extended file alone: 13/13 passed (8 original + 5 new), confirming
none of the original 8 were altered in behavior.
